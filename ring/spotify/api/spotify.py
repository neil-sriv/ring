"""Spotify linking, library saves, and per-user group playlists."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy.orm import Session

from ring.api_identifier.util import IDNotFoundException, get_model
from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.spotify import oauth, service, settings
from ring.spotify.crud import account as account_crud
from ring.spotify.errors import (
    SpotifyApiError,
    SpotifyNotConfiguredError,
    SpotifyNotLinkedError,
)
from ring.spotify.schemas.spotify import (
    SpotifyAuthorizeRequest,
    SpotifyAuthorizeResponse,
    SpotifyLibrarySaveResponse,
    SpotifyPlaylistResponse,
    SpotifyStatus,
)
from ring.sqlalchemy_base import get_db

router = APIRouter()


def _spotify_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SpotifyNotConfiguredError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Spotify linking is unavailable",
        )
    if isinstance(exc, SpotifyNotLinkedError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="spotify_not_linked",
        )
    if isinstance(exc, SpotifyApiError):
        logger.warning("Spotify request failed: {}", exc.message)
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Spotify request failed",
        )
    raise exc


def _playlist_response(sync: service.PlaylistSync) -> SpotifyPlaylistResponse:
    return SpotifyPlaylistResponse(
        playlist_id=sync.playlist_id,
        playlist_url=sync.playlist_url,
        name=sync.name,
        track_count=sync.track_count,
    )


@router.get("/status", response_model=SpotifyStatus)
async def read_spotify_status(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies
    ),
) -> SpotifyStatus:
    """Report whether linking is configured and whether this user linked."""
    app_config = settings.get_spotify_app_config()
    return SpotifyStatus(
        configured=app_config.configured,
        linked=account_crud.user_is_linked(req_dep.current_user),
    )


@router.post("/authorize", response_model=SpotifyAuthorizeResponse)
async def start_spotify_authorization(
    body: SpotifyAuthorizeRequest,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies
    ),
) -> SpotifyAuthorizeResponse:
    """Return the Spotify authorization URL for the current user."""
    try:
        app_config = settings.require_spotify_app_config()
    except SpotifyNotConfiguredError as exc:
        raise _spotify_http_error(exc) from exc
    state = oauth.create_oauth_state(
        req_dep.current_user.api_identifier, body.return_to
    )
    return SpotifyAuthorizeResponse(
        authorization_url=oauth.authorization_url(state, app_config)
    )


@router.get("/callback")
async def spotify_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Exchange the Spotify code and send the browser back to the app."""
    return_to = "/"
    user_api_id = ""
    if not state:
        return _callback_redirect(return_to, spotify_error="invalid_state")
    try:
        user_api_id, return_to = oauth.decode_oauth_state(state)
    except ValueError:
        return _callback_redirect("/", spotify_error="invalid_state")
    if error or not code:
        return _callback_redirect(
            return_to,
            spotify_error=oauth.safe_oauth_error(error or "missing_code"),
        )
    try:
        user = get_model(db, User, api_id=user_api_id)
    except IDNotFoundException:
        return _callback_redirect(return_to, spotify_error="user_not_found")
    try:
        service.link_with_authorization_code(db, user, code)
    except SpotifyNotConfiguredError:
        return _callback_redirect(return_to, spotify_error="unavailable")
    except SpotifyApiError as exc:
        logger.warning("Spotify token exchange failed: {}", exc.message)
        return _callback_redirect(
            return_to, spotify_error="token_exchange_failed"
        )
    return RedirectResponse(
        oauth.redirect_location(return_to, spotify="linked"),
        status_code=status.HTTP_302_FOUND,
    )


def _callback_redirect(return_to: str, spotify_error: str) -> RedirectResponse:
    return RedirectResponse(
        oauth.redirect_location(
            return_to,
            spotify="error",
            spotify_error=spotify_error,
        ),
        status_code=status.HTTP_302_FOUND,
    )


@router.post(
    "/letters/{letter_api_id}/library",
    response_model=SpotifyLibrarySaveResponse,
)
async def save_letter_tracks_to_spotify_library(
    letter_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies
    ),
) -> SpotifyLibrarySaveResponse:
    """Save this letter's Spotify tracks to the current user's library."""
    letter = load_and_check(
        req_dep.db, req_dep.current_user, Action.READ, letter_api_id
    )
    assert isinstance(letter, Letter)
    try:
        track_ids = service.save_letter_to_library(
            req_dep.db, req_dep.current_user, letter
        )
    except (
        SpotifyNotConfiguredError,
        SpotifyNotLinkedError,
        SpotifyApiError,
    ) as exc:
        raise _spotify_http_error(exc) from exc
    return SpotifyLibrarySaveResponse(
        saved_count=len(track_ids), track_ids=track_ids
    )


@router.get(
    "/groups/{group_api_id}/playlist",
    response_model=SpotifyPlaylistResponse,
)
async def read_group_spotify_playlist(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies
    ),
) -> SpotifyPlaylistResponse:
    """Return the current user's playlist link for this group, if created."""
    group = load_and_check(
        req_dep.db, req_dep.current_user, Action.READ, group_api_id
    )
    assert isinstance(group, Group)
    try:
        sync = service.read_group_playlist(
            req_dep.db, req_dep.current_user, group
        )
    except (
        SpotifyNotConfiguredError,
        SpotifyNotLinkedError,
        SpotifyApiError,
    ) as exc:
        raise _spotify_http_error(exc) from exc
    if sync is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_spotify_playlist",
        )
    return _playlist_response(sync)


@router.post(
    "/groups/{group_api_id}/playlist",
    response_model=SpotifyPlaylistResponse,
)
async def ensure_group_spotify_playlist(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies
    ),
) -> SpotifyPlaylistResponse:
    """Create or update the current user's playlist for this group."""
    group = load_and_check(
        req_dep.db, req_dep.current_user, Action.READ, group_api_id
    )
    assert isinstance(group, Group)
    try:
        sync = service.ensure_group_playlist(
            req_dep.db, req_dep.current_user, group
        )
    except (
        SpotifyNotConfiguredError,
        SpotifyNotLinkedError,
        SpotifyApiError,
    ) as exc:
        raise _spotify_http_error(exc) from exc
    return _playlist_response(sync)
