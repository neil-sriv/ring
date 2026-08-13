"""Link unfurling service: safely fetch a URL and extract a rich preview.

This module fetches a user-supplied URL server-side and parses Open Graph,
Twitter card, and standard HTML meta tags into a ``LinkPreview``.

Because the URL is attacker-controlled, the fetch path is hardened against
SSRF: only ``http``/``https`` are allowed, the host must resolve to a public
IP address, and every redirect hop is re-validated before it is followed.
Responses are size-capped and time-bounded, and a small in-process TTL cache
avoids re-fetching the same URL for every reader of a letter.
"""

from __future__ import annotations

import ipaddress
import socket
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ring.fastapp.config import get_config
from ring.link_unfurl.schemas.link_preview import LinkPreview


class UnsafeURLError(ValueError):
    """Raised when a URL is malformed or points at a non-public address."""


class LinkUnfurlError(Exception):
    """Raised when a URL could not be fetched or parsed into a preview."""


# url -> (monotonic_expiry, preview)
_cache: dict[str, tuple[float, LinkPreview]] = {}


def clear_link_preview_cache() -> None:
    """Clear the in-process preview cache (used between tests)."""
    _cache.clear()


def _cache_get(url: str) -> LinkPreview | None:
    entry = _cache.get(url)
    if entry is None:
        return None
    expiry, preview = entry
    if expiry < time.monotonic():
        _cache.pop(url, None)
        return None
    return preview


def _cache_put(url: str, preview: LinkPreview, ttl_seconds: int) -> None:
    if ttl_seconds <= 0:
        return
    _cache[url] = (time.monotonic() + ttl_seconds, preview)


def _assert_public_host(host: str) -> None:
    """Reject hosts that resolve to a non-public IP address.

    Uses an allowlist: an address is only accepted when it is globally
    routable (``is_global``). This is safer than a hand-maintained denylist
    of ``is_private``/``is_loopback``/etc. flags, which misses ranges such
    as IANA shared/CGNAT space ``100.64.0.0/10``. IPv4-mapped IPv6 addresses
    (e.g. ``::ffff:100.64.0.1``) are unwrapped first, because the mapped
    IPv6 form reports ``is_global`` even when the embedded IPv4 does not.

    Args:
        host (str): The hostname (or IP literal) to validate.

    Raises:
        UnsafeURLError: If the host cannot be resolved or any resolved
            address is not globally routable.
    """
    try:
        addrinfos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Could not resolve host: {host}") from exc

    for info in addrinfos:
        ip = ipaddress.ip_address(info[4][0])
        effective = (
            ip.ipv4_mapped
            if isinstance(ip, ipaddress.IPv6Address)
            and ip.ipv4_mapped is not None
            else ip
        )
        if not effective.is_global:
            raise UnsafeURLError(f"URL resolves to a non-public address: {ip}")


def assert_url_is_safe(url: str) -> None:
    """Validate that ``url`` is a fetchable, public http(s) URL.

    Args:
        url (str): The URL to validate.

    Raises:
        UnsafeURLError: If the scheme is not http(s), the host is missing,
            or the host resolves to a non-public address.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError("Only http and https URLs can be unfurled")
    if not parsed.hostname:
        raise UnsafeURLError("URL is missing a host")
    _assert_public_host(parsed.hostname)


async def _read_capped(response: httpx.Response, max_bytes: int) -> bytes:
    """Read a streamed response body, stopping once ``max_bytes`` is read."""
    buffer = bytearray()
    async for chunk in response.aiter_bytes():
        buffer.extend(chunk)
        if len(buffer) >= max_bytes:
            return bytes(buffer[:max_bytes])
    return bytes(buffer)


async def _fetch_document(url: str) -> tuple[str, bytes]:
    """Fetch an HTML document, validating safety on every redirect hop.

    Args:
        url (str): The URL to fetch.

    Returns:
        tuple[str, bytes]: The final (resolved) URL and the response body,
            truncated to the configured maximum size.

    Raises:
        UnsafeURLError: If any hop resolves to a non-public address.
        LinkUnfurlError: On network errors, non-HTML content, too many
            redirects, or an HTTP error status.
    """
    config = get_config()
    headers = {
        "User-Agent": config.LINK_UNFURL_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }
    timeout = httpx.Timeout(config.LINK_UNFURL_TIMEOUT_SECONDS)
    current_url = url

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=timeout,
            headers=headers,
        ) as client:
            for _ in range(config.LINK_UNFURL_MAX_REDIRECTS + 1):
                # Re-validate before every request so a redirect cannot
                # point the fetcher at an internal address.
                assert_url_is_safe(current_url)
                async with client.stream("GET", current_url) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise LinkUnfurlError(
                                "Redirect missing a location header"
                            )
                        current_url = urljoin(current_url, location)
                        continue

                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    if "html" not in content_type.lower():
                        raise LinkUnfurlError(
                            "Unsupported content type: "
                            f"{content_type or 'unknown'}"
                        )
                    body = await _read_capped(
                        response, config.LINK_UNFURL_MAX_BYTES
                    )
                    return str(response.url), body
    except httpx.HTTPError as exc:
        raise LinkUnfurlError(f"Failed to fetch URL: {exc}") from exc

    raise LinkUnfurlError("Too many redirects")


def _meta(soup: BeautifulSoup, attr: str, value: str) -> str | None:
    """Return the stripped ``content`` of the first matching meta tag."""
    tag = soup.find("meta", attrs={attr: value})
    if tag is None:
        return None
    content = tag.get("content")
    if not isinstance(content, str):
        return None
    content = content.strip()
    return content or None


def _find_favicon(soup: BeautifulSoup) -> str | None:
    """Return the href of the first ``<link>`` whose rel mentions an icon."""
    for tag in soup.find_all("link"):
        rel = tag.get("rel")
        if not rel:
            continue
        tokens = rel if isinstance(rel, list) else [rel]
        if not any("icon" in token.lower() for token in tokens):
            continue
        href = tag.get("href")
        if isinstance(href, str) and href.strip():
            return href.strip()
    return None


def _page_title(soup: BeautifulSoup) -> str | None:
    if soup.title is None:
        return None
    text = soup.title.get_text().strip()
    return text or None


def _safe_media_url(base_url: str, value: str | None) -> str | None:
    """Absolutize a media URL, dropping non-http(s) schemes.

    Open Graph tags are attacker-controlled, so an ``og:image`` could be a
    ``javascript:`` or ``data:`` URI. Returning only http(s) URLs keeps
    those out of the frontend's ``<img src>``.
    """
    if not value:
        return None
    absolute = urljoin(base_url, value)
    if urlparse(absolute).scheme not in ("http", "https"):
        return None
    return absolute


def extract_link_preview(
    html: str, base_url: str, requested_url: str
) -> LinkPreview:
    """Parse HTML into a ``LinkPreview``.

    Args:
        html (str): The page HTML.
        base_url (str): The resolved URL, used to absolutize relative links.
        requested_url (str): The URL originally requested by the caller.

    Returns:
        LinkPreview: The preview populated with whatever metadata was found.
    """
    soup = BeautifulSoup(html, "html.parser")

    title = (
        _meta(soup, "property", "og:title")
        or _meta(soup, "name", "twitter:title")
        or _page_title(soup)
    )
    description = (
        _meta(soup, "property", "og:description")
        or _meta(soup, "name", "twitter:description")
        or _meta(soup, "name", "description")
    )
    image = (
        _meta(soup, "property", "og:image")
        or _meta(soup, "property", "og:image:url")
        or _meta(soup, "name", "twitter:image")
        or _meta(soup, "name", "twitter:image:src")
    )
    site_name = (
        _meta(soup, "property", "og:site_name") or urlparse(base_url).hostname
    )

    favicon = _find_favicon(soup)

    return LinkPreview(
        url=requested_url,
        resolved_url=base_url,
        title=title,
        description=description,
        image_url=_safe_media_url(base_url, image),
        site_name=site_name,
        favicon_url=(
            _safe_media_url(base_url, favicon)
            or _safe_media_url(base_url, "/favicon.ico")
        ),
    )


async def unfurl_url(url: str) -> LinkPreview:
    """Fetch ``url`` and return a rich preview, using the TTL cache.

    Args:
        url (str): The URL to unfurl.

    Returns:
        LinkPreview: The preview for the URL.

    Raises:
        UnsafeURLError: If the URL is unsafe to fetch.
        LinkUnfurlError: If the URL could not be fetched or parsed.
    """
    url = url.strip()
    if not url:
        raise UnsafeURLError("URL is empty")

    cached = _cache_get(url)
    if cached is not None:
        return cached

    resolved_url, body = await _fetch_document(url)
    html = body.decode("utf-8", errors="replace")
    preview = extract_link_preview(html, resolved_url, url)
    _cache_put(url, preview, get_config().LINK_UNFURL_CACHE_TTL_SECONDS)
    return preview
