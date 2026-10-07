"""Score how completely a response answers its question.

One System One ``score`` question. The result is not stored.
"""

from __future__ import annotations

from ring.letters.models.response_model import Response
from ring.letters.schemas.response import ResponseScore
from ring.systemone.client import SystemOneClientError, evaluate
from ring.systemone.schemas import ScoreAnswer, ScoreQuestion, SystemOneRequest

RESPONSE_SCORE_LEVELS = [
    "Does not address the question",
    "Mentions the question without answering it",
    "Answers the question",
    "Answers the question with specific detail",
]

_QUESTION_KEY = "completeness"


def score_response(response: Response) -> ResponseScore:
    """Ask System One to place this response on the completeness rubric."""
    if not response.response_text or not response.response_text.strip():
        raise ValueError("Response has no text to score")

    result = evaluate(
        SystemOneRequest(
            state={
                "question": response.question.question_text,
                "response": response.response_text,
            },
            questions={
                _QUESTION_KEY: ScoreQuestion(
                    type="score",
                    instructions=(
                        "How completely does this response answer the "
                        "question?"
                    ),
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
