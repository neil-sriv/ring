from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import ValidationError

from llm.config import LLMConfig, get_config
from llm.systemone.schemas import (
    ChoiceAnswer,
    ChoiceQuestion,
    NoulAnswer,
    NoulQuestion,
    ScoreAnswer,
    ScoreQuestion,
    SystemOneRequest,
    SystemOneResponse,
    Usage,
)

Completer = Callable[[str], Awaitable[tuple[str, Usage]]]
Poster = Callable[[str, str, dict[str, Any]], Awaitable[httpx.Response]]

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class SystemOneError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def question_payload(
    question: NoulQuestion | ChoiceQuestion | ScoreQuestion,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": question.type,
        "instructions": question.instructions,
    }
    if isinstance(question, NoulQuestion) and question.criteria is not None:
        payload["criteria"] = question.criteria.model_dump(exclude_none=True)
    elif isinstance(question, ChoiceQuestion):
        payload["criteria"] = dict(question.criteria)
    elif isinstance(question, ScoreQuestion):
        payload["criteria"] = list(question.criteria)
    return payload


def request_body(request: SystemOneRequest) -> dict[str, Any]:
    # Question ids stay in this map. They are not part of question_payload,
    # matching TypeSafe: the key is not sent to the model.
    return {
        "state": request.state,
        "model": request.model,
        "questions": {
            key: question_payload(question)
            for key, question in request.questions.items()
        },
    }


def build_prompt(request: SystemOneRequest) -> str:
    questions = [
        {"index": index, **question_payload(question)}
        for index, question in enumerate(request.questions.values())
    ]
    state = request.state
    if not isinstance(state, str):
        state = json.dumps(state, ensure_ascii=False)
    spec = json.dumps(questions, ensure_ascii=False)
    return (
        "You are a decision function. Read the state and answer every "
        "question. Return only a JSON object with an answers array, one "
        "object per question, in the same order, each with its index.\n"
        "For type noul, include noul, a number from 0 (no) to 1 (yes).\n"
        "For type choice, include probabilities, a map from every criteria "
        "key to a probability. The values must sum to 1.\n"
        "For type score, include probabilities, a map from level index "
        'strings ("0", "1", ...) to a probability. The values must sum '
        "to 1.\n"
        "Do not add prose.\n\n"
        f"State:\n{state}\n\n"
        f"Questions:\n{spec}\n"
    )


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = _JSON_OBJECT.search(stripped)
        if match is None:
            raise SystemOneError(
                502, "Local wrapper returned a non-JSON completion"
            ) from None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise SystemOneError(
                502, "Local wrapper returned a non-JSON completion"
            ) from exc
    if not isinstance(parsed, dict):
        raise SystemOneError(502, "Local wrapper JSON was not an object")
    return parsed


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _normalize(weights: list[float]) -> list[float]:
    cleaned = [max(0.0, weight) for weight in weights]
    total = sum(cleaned)
    if total <= 0:
        share = 1.0 / len(cleaned)
        return [share for _ in cleaned]
    return [weight / total for weight in cleaned]


def _confidence(probabilities: list[float]) -> float:
    """Peakiness stand-in. Not TypeSafe's published confidence formula."""
    count = len(probabilities)
    if count <= 1:
        return 1.0
    peak = max(probabilities)
    uniform = 1.0 / count
    if peak <= uniform:
        return 0.0
    return (peak - uniform) / (1.0 - uniform)


def coerce_answers(
    request: SystemOneRequest, raw: dict[str, Any]
) -> dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer]:
    entries = raw.get("answers")
    if not isinstance(entries, list):
        raise SystemOneError(502, "Local wrapper JSON missing answers array")
    by_index: dict[int, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        index = entry.get("index")
        if isinstance(index, bool) or not isinstance(index, int):
            continue
        by_index[index] = entry

    answers: dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer] = {}
    for index, (key, question) in enumerate(request.questions.items()):
        entry = by_index.get(index)
        if entry is None:
            raise SystemOneError(
                502, f"Local wrapper omitted question index {index}"
            )
        if isinstance(question, NoulQuestion):
            answers[key] = _noul_answer(entry)
        elif isinstance(question, ChoiceQuestion):
            answers[key] = _choice_answer(question, entry)
        else:
            answers[key] = _score_answer(question, entry)
    return answers


def _noul_answer(entry: dict[str, Any]) -> NoulAnswer:
    noul = _as_float(entry.get("noul"))
    if noul is None:
        raise SystemOneError(502, "Local wrapper omitted a noul")
    return NoulAnswer(noul=min(1.0, max(0.0, noul)))


def _choice_answer(
    question: ChoiceQuestion, entry: dict[str, Any]
) -> ChoiceAnswer:
    raw_probs = entry.get("probabilities")
    if not isinstance(raw_probs, dict):
        raise SystemOneError(502, "Local wrapper omitted choice probabilities")
    weights = [
        0.0 if (parsed := _as_float(raw_probs.get(option))) is None else parsed
        for option in question.criteria
    ]
    probabilities = _normalize(weights)
    paired = list(zip(question.criteria, probabilities, strict=True))
    choice = max(paired, key=lambda item: item[1])[0]
    return ChoiceAnswer(
        choice=choice,
        probabilities={option: prob for option, prob in paired},
        confidence=_confidence(probabilities),
    )


def _score_answer(
    question: ScoreQuestion, entry: dict[str, Any]
) -> ScoreAnswer:
    raw_probs = entry.get("probabilities")
    if not isinstance(raw_probs, dict):
        raise SystemOneError(502, "Local wrapper omitted score probabilities")
    weights: list[float] = []
    for index, _label in enumerate(question.criteria):
        parsed = _as_float(raw_probs.get(str(index)))
        if parsed is None:
            parsed = _as_float(raw_probs.get(index))
        weights.append(0.0 if parsed is None else parsed)
    probabilities = _normalize(weights)
    score = sum(index * prob for index, prob in enumerate(probabilities))
    return ScoreAnswer(
        score=score,
        legend={
            str(index): label for index, label in enumerate(question.criteria)
        },
        probabilities={
            str(index): prob for index, prob in enumerate(probabilities)
        },
        confidence=_confidence(probabilities),
    )


async def default_completer(prompt: str) -> tuple[str, Usage]:
    from llm.ai_client.ai_client import LLMType, get_llm

    llm = get_llm(LLMType.GEMINI, "completions")
    completion = await llm.client.chat.completions.create(
        model=llm.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    text = completion.choices[0].message.content or ""
    usage_raw = completion.usage
    usage = Usage(
        input_tokens=getattr(usage_raw, "prompt_tokens", 0) or 0,
        output_tokens=getattr(usage_raw, "completion_tokens", 0) or 0,
    )
    return text, usage


async def evaluate_locally(
    request: SystemOneRequest,
    completer: Completer | None = None,
) -> SystemOneResponse:
    complete = completer or default_completer
    text, usage = await complete(build_prompt(request))
    return SystemOneResponse(
        model=f"ring-llm-wrapper:{request.model}",
        answers=coerce_answers(request, extract_json(text)),
        usage=usage,
    )


async def post_typesafe(
    url: str, api_key: str, body: dict[str, Any]
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=30.0) as client:
        return await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )


async def evaluate_typesafe(
    request: SystemOneRequest,
    config: LLMConfig,
    poster: Poster | None = None,
) -> SystemOneResponse:
    url = config.jev_base_url.rstrip("/") + "/systemone"
    send = poster or post_typesafe
    response = await send(url, config.jev_api_key, request_body(request))
    if response.status_code >= 400:
        detail = response.text[:500] or "TypeSafe request failed"
        raise SystemOneError(response.status_code, detail)
    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise SystemOneError(502, "TypeSafe returned non-JSON") from exc
    try:
        return SystemOneResponse.model_validate(payload)
    except ValidationError as exc:
        raise SystemOneError(
            502, "TypeSafe response did not match System One"
        ) from exc


async def evaluate(
    request: SystemOneRequest,
    config: LLMConfig | None = None,
    completer: Completer | None = None,
    poster: Poster | None = None,
) -> SystemOneResponse:
    cfg = config if config is not None else get_config()
    if cfg.jev_api_key:
        return await evaluate_typesafe(request, cfg, poster=poster)
    return await evaluate_locally(request, completer=completer)
