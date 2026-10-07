from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from llm.config import LLMConfig
from llm.security.security import get_api_key
from llm.systemone.api import router as systemone_router
from llm.systemone.evaluate import (
    SystemOneError,
    build_prompt,
    evaluate,
    extract_json,
)
from llm.systemone.schemas import (
    SystemOneRequest,
    SystemOneResponse,
    Usage,
)

PAYOUT = "Help! My payouts have been failing for 3 days."

SAMPLE = {
    "state": PAYOUT,
    "model": "jev-latest",
    "questions": {
        "secret_question_key": {
            "type": "noul",
            "instructions": "Does this convey urgency?",
            "criteria": {
                "true": "Explicitly time-sensitive",
                "false": "No urgency expressed",
            },
        },
        "department": {
            "type": "choice",
            "instructions": "Which team should handle this?",
            "criteria": {
                "billing": "Payments, invoicing, refunds",
                "technical": "Bugs, outages, integrations",
                "sales": None,
            },
        },
        "frustration": {
            "type": "score",
            "instructions": "How frustrated is the customer?",
            "criteria": ["Calm", "Frustrated", "Very angry"],
        },
    },
}

WRAPPER_JSON = json.dumps(
    {
        "answers": [
            {"index": 0, "noul": 0.95},
            {
                "index": 1,
                "probabilities": {
                    "billing": 0.88,
                    "technical": 0.12,
                    "sales": 0.0,
                },
            },
            {
                "index": 2,
                "probabilities": {"0": 0.0, "1": 0.95, "2": 0.05},
            },
        ]
    }
)


def _request() -> SystemOneRequest:
    return SystemOneRequest.model_validate(SAMPLE)


def test_public_examples_validate() -> None:
    request = _request()
    assert request.model == "jev-latest"
    assert request.questions["department"].type == "choice"
    assert request.questions["frustration"].criteria == [
        "Calm",
        "Frustrated",
        "Very angry",
    ]


def test_rejects_bad_questions() -> None:
    with pytest.raises(ValidationError):
        SystemOneRequest.model_validate({"state": "x", "questions": {}})
    with pytest.raises(ValidationError):
        SystemOneRequest.model_validate(
            {
                "state": "x",
                "questions": {
                    "quality": {
                        "type": "score",
                        "instructions": "Rate it",
                        "criteria": ["only one"],
                    }
                },
            }
        )
    options = {f"opt{i}": None for i in range(256)}
    with pytest.raises(ValidationError):
        SystemOneRequest.model_validate(
            {
                "state": "x",
                "questions": {
                    "route": {
                        "type": "choice",
                        "instructions": "Pick",
                        "criteria": options,
                    }
                },
            }
        )


def test_prompt_omits_question_keys() -> None:
    prompt = build_prompt(_request())
    assert "secret_question_key" not in prompt
    assert "Does this convey urgency?" in prompt
    assert "billing" in prompt


def test_extract_json_from_fence() -> None:
    parsed = extract_json("```json\n" + WRAPPER_JSON + "\n```")
    assert parsed["answers"][0]["noul"] == 0.95


def test_local_wrapper_matches_public_shape() -> None:
    seen: list[str] = []

    async def completer(prompt: str) -> tuple[str, Usage]:
        seen.append(prompt)
        return WRAPPER_JSON, Usage(input_tokens=12, output_tokens=4)

    response = asyncio.run(
        evaluate(
            _request(),
            config=LLMConfig(jev_api_key=""),
            completer=completer,
        )
    )
    dumped = response.model_dump()
    assert response.model == "ring-llm-wrapper:jev-latest"
    assert dumped["answers"]["secret_question_key"] == {
        "type": "noul",
        "noul": 0.95,
    }
    department = dumped["answers"]["department"]
    assert department["choice"] == "billing"
    assert department["probabilities"]["billing"] == pytest.approx(0.88)
    assert department["probabilities"]["sales"] == pytest.approx(0.0)
    peak = 0.88
    uniform = 1 / 3
    assert department["confidence"] == pytest.approx(
        (peak - uniform) / (1 - uniform)
    )
    frustration = dumped["answers"]["frustration"]
    assert frustration["score"] == pytest.approx(1.05)
    assert frustration["legend"] == {
        "0": "Calm",
        "1": "Frustrated",
        "2": "Very angry",
    }
    assert "secret_question_key" not in seen[0]


def test_typesafe_proxy_forwards_body_and_skips_wrapper() -> None:
    called = {"completer": False}

    async def completer(prompt: str) -> tuple[str, Usage]:
        called["completer"] = True
        return "{}", Usage()

    async def poster(url: str, api_key: str, body: dict) -> httpx.Response:
        assert url == "https://api.typesafe.ai/v1/systemone"
        assert api_key == "ts-key"
        assert body["questions"]["department"]["criteria"]["sales"] is None
        assert "secret_question_key" in body["questions"]
        return httpx.Response(
            200,
            json={
                "model": "jev-1.13.0",
                "answers": {
                    "secret_question_key": {"type": "noul", "noul": 0.5},
                    "department": {
                        "type": "choice",
                        "choice": "billing",
                        "probabilities": {
                            "billing": 1.0,
                            "technical": 0.0,
                            "sales": 0.0,
                        },
                        "confidence": 1.0,
                    },
                    "frustration": {
                        "type": "score",
                        "score": 1.0,
                        "legend": {
                            "0": "Calm",
                            "1": "Frustrated",
                            "2": "Very angry",
                        },
                        "probabilities": {"0": 0.0, "1": 1.0, "2": 0.0},
                        "confidence": 1.0,
                    },
                },
                "usage": {"input_tokens": 30, "output_tokens": 8},
            },
        )

    response = asyncio.run(
        evaluate(
            _request(),
            config=LLMConfig(
                jev_api_key="ts-key",
                jev_base_url="https://api.typesafe.ai/v1",
            ),
            completer=completer,
            poster=poster,
        )
    )
    assert isinstance(response, SystemOneResponse)
    assert response.model == "jev-1.13.0"
    assert called["completer"] is False


def test_typesafe_error_is_forwarded() -> None:
    async def poster(url: str, api_key: str, body: dict) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    with pytest.raises(SystemOneError) as caught:
        asyncio.run(
            evaluate(
                _request(),
                config=LLMConfig(jev_api_key="ts-key"),
                poster=poster,
            )
        )
    assert caught.value.status_code == 429
    assert caught.value.detail == "slow down"


def test_route_auth_and_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    application = FastAPI(dependencies=[Depends(get_api_key)])
    application.include_router(systemone_router)
    client = TestClient(application)
    missing = client.post("/systemone", json=SAMPLE)
    assert missing.status_code == 401

    monkeypatch.setenv("LLM_API_KEY", "test-key")

    async def fake_evaluate(request: SystemOneRequest) -> SystemOneResponse:
        return SystemOneResponse(
            model="ring-llm-wrapper:jev-latest",
            answers={
                "secret_question_key": {"type": "noul", "noul": 0.95},
                "department": {
                    "type": "choice",
                    "choice": "billing",
                    "probabilities": {
                        "billing": 1.0,
                        "technical": 0.0,
                        "sales": 0.0,
                    },
                    "confidence": 1.0,
                },
                "frustration": {
                    "type": "score",
                    "score": 1.0,
                    "legend": {
                        "0": "Calm",
                        "1": "Frustrated",
                        "2": "Very angry",
                    },
                    "probabilities": {"0": 0.0, "1": 1.0, "2": 0.0},
                    "confidence": 1.0,
                },
            },
            usage=Usage(),
        )

    monkeypatch.setattr("llm.systemone.api.evaluate", fake_evaluate)
    ok = client.post(
        "/systemone",
        json=SAMPLE,
        headers={"X-API-Key": "test-key"},
    )
    assert ok.status_code == 200
    assert ok.json()["answers"]["secret_question_key"]["noul"] == 0.95

    bad = client.post(
        "/systemone",
        json={"state": "", "questions": {}},
        headers={"X-API-Key": "test-key"},
    )
    assert bad.status_code == 422
