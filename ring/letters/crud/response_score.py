"""Check whether your own draft answers its prompt.

One System One ``score`` question. The result is not stored.
"""

from __future__ import annotations

from ring.letters.models.response_model import Response
from ring.letters.schemas.response import ResponseScore
from ring.systemone.client import SystemOneClientError, evaluate
from ring.systemone.schemas import ScoreAnswer, ScoreQuestion, SystemOneRequest

RESPONSE_SCORE_LEVELS = [
    "Your draft does not answer the prompt",
    "Your draft mentions the prompt without answering it",
    "Your draft answers the prompt",
    "Your draft answers the prompt with specific detail",
]

_QUESTION_KEY = "completeness"


def score_response(response: Response) -> ResponseScore:
    """Ask whether this draft answers its prompt."""
    if not response.response_text or not response.response_text.strip():
        raise ValueError("Your draft has no text to check")

    result = evaluate(
        SystemOneRequest(
            state={
                "prompt": response.question.question_text,
                "draft": response.response_text,
            },
            questions={
                _QUESTION_KEY: ScoreQuestion(
                    type="score",
                    instructions="Does this draft answer the prompt?",
                    criteria=list(RESPONSE_SCORE_LEVELS),
                )
            },
        )
    )
    answer = result.answers.get(_QUESTION_KEY)
    if not isinstance(answer, ScoreAnswer):
        raise SystemOneClientError(502, "System One omitted the score")
    return ResponseScore(
        model=result.model,
        score=answer.score,
        confidence=answer.confidence,
        legend=answer.legend,
    )
