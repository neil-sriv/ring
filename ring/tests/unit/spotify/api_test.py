"""Spotify linking API."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.fastapp.config import get_config
from ring.parties.models.user_model import User
from ring.spotify.models.user_spotify_playlist import UserSpotifyPlaylist
from ring.spotify.oauth import create_oauth_state
from ring.spotify.settings import SpotifyAppConfig
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory

TRACK_A = "a" * 22
TRACK_B = "b" * 22
Handler = Callable[[httpx.Request], httpx.Response]


def _configure(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> None:
    app_config = SpotifyAppConfig(
        client_id="cid",
        client_secret="csecret",
        redirect_uri="http://localhost/api/v1/spotify/callback",
    )
    monkeypatch.setattr(
        "ring.spotify.settings.get_spotify_app_config",
        lambda: app_config,
    )
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def factory(*args: object, **kwargs: object) -> httpx.Client:
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("ring.spotify.client.httpx.Client", factory)


def _token_ok(request: httpx.Request) -> httpx.Response | None:
    if request.url.path != "/api/token":
        return None
    body = request.content.decode()
    if "grant_type=authorization_code" in body:
        return httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh-1",
                "token_type": "Bearer",
            },
        )
    if "refresh_token=refresh-1" in body:
        return httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh-2",
                "token_type": "Bearer",
            },
        )
    return httpx.Response(
        200,
        json={"access_token": "access", "token_type": "Bearer"},
    )


def _member_letter(
    db_session: Session, current_user: User, *, include_member: bool
):
    group = GroupFactory.create()
    if include_member:
        group.members.append(current_user)
    letter = LetterFactory.create(
        group=group, title=f"spotify:track:{TRACK_A}"
    )
    question = QuestionFactory.create(
        letter=letter,
        question_text=(
            f"https://open.spotify.com/track/{TRACK_A}?si=1 "
            f"https://open.spotify.com/album/{'d' * 22}"
        ),
    )
    ResponseFactory.create(
        question=question,
        participant=current_user,
        response_text=f"https://open.spotify.com/intl-fr/track/{TRACK_B}",
    )
    db_session.commit()
    return group, letter


class TestSpotifyStatus:
    def test_unconfigured(self, authenticated_client: TestClient) -> None:
        response = authenticated_client.get("/spotify/status")
        assert response.status_code == 200
        assert response.json() == {"configured": False, "linked": False}

    def test_configured_and_linked(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, lambda request: httpx.Response(500))
        current_user.spotify_refresh_token = "refresh-1"
        db_session.commit()
        response = authenticated_client.get("/spotify/status")
        assert response.status_code == 200
        assert response.json() == {"configured": True, "linked": True}


class TestSpotifyAuthorize:
    def test_unconfigured_is_unavailable(
        self, authenticated_client: TestClient
    ) -> None:
        response = authenticated_client.post(
            "/spotify/authorize", json={"return_to": "/loops/x"}
        )
        assert response.status_code == 503
        assert response.json()["detail"] == "Spotify linking is unavailable"

    def test_returns_authorization_url(
        self,
        authenticated_client: TestClient,
        current_user: User,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, lambda request: httpx.Response(500))
        response = authenticated_client.post(
            "/spotify/authorize",
            json={"return_to": "/loops/lttr_1?spotify_action=save"},
        )
        assert response.status_code == 200
        url = response.json()["authorization_url"]
        assert url.startswith("https://accounts.spotify.com/authorize?")
        assert "client_id=cid" in url
        assert "user-library-modify" in url
        assert "playlist-modify-private" in url
        assert "redirect_uri=" in url


class TestSpotifyCallback:
    def test_stores_refresh_token_and_redirects(
        self,
        unauthenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        state = create_oauth_state(
            current_user.api_identifier,
            "/loops/lttr_1?spotify_action=save",
        )
        response = unauthenticated_client.get(
            "/spotify/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )
        assert response.status_code == 302
        location = response.headers["location"]
        base = get_config().APP_BASE_URL.rstrip("/")
        assert location.startswith(f"{base}/loops/lttr_1?")
        assert "spotify=linked" in location
        assert "spotify_action=save" in location
        db_session.refresh(current_user)
        assert current_user.spotify_refresh_token == "refresh-1"

    def test_spotify_denial_does_not_store_a_token(
        self,
        unauthenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        state = create_oauth_state(current_user.api_identifier, "/loops/x")
        response = unauthenticated_client.get(
            "/spotify/callback",
            params={"error": "access_denied", "state": state},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "spotify=error" in response.headers["location"]
        assert "spotify_error=access_denied" in response.headers["location"]
        db_session.refresh(current_user)
        assert current_user.spotify_refresh_token is None

    def test_invalid_state(
        self,
        unauthenticated_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        response = unauthenticated_client.get(
            "/spotify/callback",
            params={"code": "auth-code", "state": "nope"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "spotify_error=invalid_state" in response.headers["location"]


class TestSaveLetterLibrary:
    def test_saves_unique_tracks(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        saved: list[list[str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            token = _token_ok(request)
            if token is not None:
                return token
            assert request.method == "PUT"
            assert request.url.path == "/v1/me/library"
            saved.append(str(request.url))
            return httpx.Response(200, json={})

        _configure(monkeypatch, handler)
        current_user.spotify_refresh_token = "refresh-1"
        _, letter = _member_letter(
            db_session, current_user, include_member=True
        )
        response = authenticated_client.post(
            f"/spotify/letters/{letter.api_identifier}/library"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["saved_count"] == 2
        assert body["track_ids"] == [TRACK_A, TRACK_B]
        assert TRACK_A in saved[0] and TRACK_B in saved[0]
        db_session.refresh(current_user)
        assert current_user.spotify_refresh_token == "refresh-2"
        me = authenticated_client.get("/parties/me")
        assert "refresh-2" not in me.text
        assert "spotify_refresh_token" not in me.json()

    def test_no_tracks_returns_empty(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError(f"unexpected {request.url}")

        _configure(monkeypatch, handler)
        current_user.spotify_refresh_token = "refresh-1"
        group = GroupFactory.create()
        group.members.append(current_user)
        letter = LetterFactory.create(group=group, title="no music")
        QuestionFactory.create(letter=letter, question_text="plain")
        db_session.commit()
        response = authenticated_client.post(
            f"/spotify/letters/{letter.api_identifier}/library"
        )
        assert response.status_code == 200
        assert response.json()["saved_count"] == 0

    def test_not_linked(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        _, letter = _member_letter(
            db_session, current_user, include_member=True
        )
        response = authenticated_client.post(
            f"/spotify/letters/{letter.api_identifier}/library"
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "spotify_not_linked"

    def test_rejected_refresh_token_unlinks(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "invalid_grant"})

        _configure(monkeypatch, handler)
        current_user.spotify_refresh_token = "refresh-1"
        _, letter = _member_letter(
            db_session, current_user, include_member=True
        )
        response = authenticated_client.post(
            f"/spotify/letters/{letter.api_identifier}/library"
        )
        assert response.status_code == 409
        db_session.refresh(current_user)
        assert current_user.spotify_refresh_token is None

    def test_not_a_member(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        current_user.spotify_refresh_token = "refresh-1"
        _, letter = _member_letter(
            db_session, current_user, include_member=False
        )
        response = authenticated_client.post(
            f"/spotify/letters/{letter.api_identifier}/library"
        )
        assert response.status_code == 403

    def test_missing_letter(
        self,
        authenticated_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        response = authenticated_client.post(
            "/spotify/letters/lttr_00000000-0000-0000-0000-000000000000/library"
        )
        assert response.status_code == 403

    def test_unconfigured(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        group.members.append(current_user)
        letter = LetterFactory.create(group=group)
        db_session.commit()
        response = authenticated_client.post(
            f"/spotify/letters/{letter.api_identifier}/library"
        )
        assert response.status_code == 503


class TestGroupPlaylist:
    def test_create_then_update_same_playlist(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            token = _token_ok(request)
            if token is not None:
                return token
            calls.append((request.method, request.url.path))
            if (
                request.method == "POST"
                and request.url.path == "/v1/me/playlists"
            ):
                return httpx.Response(201, json={"id": "pl_1"})
            if request.url.path.endswith("/items"):
                return httpx.Response(200, json={"snapshot_id": "s"})
            if request.method == "PUT":
                return httpx.Response(200, json={"id": "pl_1"})
            return httpx.Response(500, json={"unexpected": request.url.path})

        _configure(monkeypatch, handler)
        current_user.spotify_refresh_token = "refresh-1"
        group, _letter = _member_letter(
            db_session, current_user, include_member=True
        )
        created = authenticated_client.post(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert created.status_code == 200
        body = created.json()
        assert body["playlist_id"] == "pl_1"
        assert body["playlist_url"] == (
            "https://open.spotify.com/playlist/pl_1"
        )
        assert body["name"] == group.name
        assert body["track_count"] == 2
        calls.clear()
        updated = authenticated_client.post(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert updated.status_code == 200
        assert updated.json()["playlist_id"] == "pl_1"
        methods = [path for _method, path in calls]
        assert "/v1/me/playlists" not in methods
        assert any(path.endswith("/items") for path in methods)
        listed = authenticated_client.get(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert listed.status_code == 200
        assert listed.json()["playlist_url"].endswith("/pl_1")
        row = db_session.query(UserSpotifyPlaylist).one()
        assert row.spotify_playlist_id == "pl_1"
        assert row.user_id == current_user.id
        assert row.group_id == group.id

    def test_missing_playlist_is_404(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        current_user.spotify_refresh_token = "refresh-1"
        group = GroupFactory.create()
        group.members.append(current_user)
        db_session.commit()
        response = authenticated_client.get(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "no_spotify_playlist"

    def test_recreates_when_spotify_playlist_is_gone(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mode = {"miss": False}

        def handler(request: httpx.Request) -> httpx.Response:
            token = _token_ok(request)
            if token is not None:
                return token
            if (
                request.method == "POST"
                and request.url.path == "/v1/me/playlists"
            ):
                playlist_id = "pl_2" if mode["miss"] else "pl_1"
                return httpx.Response(201, json={"id": playlist_id})
            if (
                request.method == "PUT"
                and not request.url.path.endswith("/items")
                and mode["miss"]
            ):
                return httpx.Response(404, json={"error": {"status": 404}})
            return httpx.Response(200, json={"snapshot_id": "s"})

        _configure(monkeypatch, handler)
        current_user.spotify_refresh_token = "refresh-1"
        group, _letter = _member_letter(
            db_session, current_user, include_member=True
        )
        first = authenticated_client.post(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert first.json()["playlist_id"] == "pl_1"
        mode["miss"] = True
        second = authenticated_client.post(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert second.status_code == 200
        assert second.json()["playlist_id"] == "pl_2"

    def test_not_a_member(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        current_user.spotify_refresh_token = "refresh-1"
        group, _letter = _member_letter(
            db_session, current_user, include_member=False
        )
        response = authenticated_client.post(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert response.status_code == 403

    def test_not_linked(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _configure(monkeypatch, _token_ok)
        group = GroupFactory.create()
        group.members.append(current_user)
        db_session.commit()
        response = authenticated_client.post(
            f"/spotify/groups/{group.api_identifier}/playlist"
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "spotify_not_linked"
