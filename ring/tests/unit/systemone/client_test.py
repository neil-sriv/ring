"""Tests for the System One client.

These mock the generated ApiClient. They do not call TypeSafe or the LLM
service.
"""

from __future__ import annotations

import json

import pytest
from llm_service import ApiClient, Configuration
from llm_service.exceptions import ApiException
from pydantic import ValidationError

from ring.systemone.client import SystemOneClientError, evaluate
from ring.systemone.schemas import (
    ChoiceAnswer,
    ChoiceQuestion,
    NoulAnswer,
    NoulQuestion,
    ScoreAnswer,
    ScoreQuestion,
    SystemOneRequest,
)


class _FakeRESTResponse:
    def __init__(self, status: int, payload: dict) -> None:
        self.status = status
        self.data = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self.data


def _config() -> Configuration:
    return Configuration(
        host="http://ring-llm:8006",
        api_key={"APIKeyHeader": "test-key"},
    )


def _request() -> SystemOneRequest:
    return SystemOneRequest(
        state={"question": "How was your week?", "response": "Long."},
        questions={
            "addresses": NoulQuestion(
                type="noul",
                instructions="Does the response address the question?",
            ),
            "register": ChoiceQuestion(
                type="choice",
                instructions="Which register fits the response?",
                criteria={"brief": None, "detailed": None},
            ),
            "completeness": ScoreQuestion(
                type="score",
                instructions="How complete is the response?",
                criteria=["Thin", "Solid"],
            ),
        },
    )


def _answers() -> dict:
    return {
        "model": "ring-llm-wrapper:jev-latest",
        "answers": {
            "addresses": {"type": "noul", "noul": 0.2},
            "register": {
                "type": "choice",
                "choice": "brief",
                "probabilities": {"brief": 0.8, "detailed": 0.2},
                "confidence": 0.6,
            },
            "completeness": {
                "type": "score",
                "score": 0.2,
                "legend": {"0": "Thin", "1": "Solid"},
                "probabilities": {"0": 0.8, "1": 0.2},
                "confidence": 0.6,
            },
        },
        "usage": {"input_tokens": 1, "output_tokens": 0},
    }


class TestSystemOneClient:
    def test_posts_noul_choice_and_score(self, monkeypatch) -> None:
        captured: dict = {}

        def fake_call_api(
            self,
            method,
            url,
            header_params=None,
            body=None,
            post_params=None,
            _request_timeout=None,
        ):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = header_params
            captured["body"] = body
            captured["timeout"] = _request_timeout
            return _FakeRESTResponse(200, _answers())

        monkeypatch.setattr(ApiClient, "call_api", fake_call_api)
        monkeypatch.setattr(
            "ring.systemone.client.get_llm_config",
            lambda: type("Cfg", (), {"config": _config()})(),
        )

        result = evaluate(_request())

        assert captured["method"] == "POST"
        assert captured["url"] == "http://ring-llm:8006/systemone"
        assert captured["headers"]["X-API-Key"] == "test-key"
        assert captured["timeout"] == 30
        questions = captured["body"]["questions"]
        assert set(questions) == {"addresses", "register", "completeness"}
        assert questions["addresses"]["type"] == "noul"
        assert questions["register"]["type"] == "choice"
        assert questions["register"]["criteria"] == {
            "brief": None,
            "detailed": None,
        }
        assert questions["completeness"]["type"] == "score"
        assert questions["completeness"]["criteria"] == ["Thin", "Solid"]
        # Question map keys stay in the map, not inside each question.
        assert "addresses" not in questions["addresses"]

        assert isinstance(result.answers["addresses"], NoulAnswer)
        assert result.answers["addresses"].noul == 0.2
        assert isinstance(result.answers["register"], ChoiceAnswer)
        assert result.answers["register"].choice == "brief"
        assert isinstance(result.answers["completeness"], ScoreAnswer)
        assert result.answers["completeness"].score == 0.2

    def test_upstream_status_is_not_parsed(self, monkeypatch) -> None:
        def fake_call_api(self, *args, **kwargs):
            return _FakeRESTResponse(401, {"detail": "bad key"})

        monkeypatch.setattr(ApiClient, "call_api", fake_call_api)
        monkeypatch.setattr(
            "ring.systemone.client.get_llm_config",
            lambda: type("Cfg", (), {"config": _config()})(),
        )

        with pytest.raises(SystemOneClientError) as exc_info:
            evaluate(_request())
        assert exc_info.value.status_code == 401

    def test_transport_error(self, monkeypatch) -> None:
        def fake_call_api(self, *args, **kwargs):
            raise ApiException(status=0, reason="connection refused")

        monkeypatch.setattr(ApiClient, "call_api", fake_call_api)
        monkeypatch.setattr(
            "ring.systemone.client.get_llm_config",
            lambda: type("Cfg", (), {"config": _config()})(),
        )

        with pytest.raises(SystemOneClientError) as exc_info:
            evaluate(_request())
        assert exc_info.value.status_code == 502

    def test_rejects_empty_questions(self) -> None:
        with pytest.raises(ValidationError):
            SystemOneRequest(
                state="hello",
                questions={},
            )
