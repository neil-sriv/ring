#!/usr/bin/env python3
"""Mobile horizontal-overflow smoke check for the Ring frontend.

Logs into the local app, visits key routes at phone viewports, and fails if
any element extends past the right edge of the viewport without a horizontally
scrollable ancestor to reach it. Because app.css sets `overflow-x: hidden` on
<body>, such content is silently clipped and unreachable on phones, so every
report is a real regression.

Requires the dev stack (API on :8001 behind the Vite proxy, Vite on :5173)
and the seeded test user:

    bash .cursor/cloud-start.sh        # cloud VM
    # or: ring compose up && ring fe dev

    uv run --group dev python dev_util/mobile_overflow_check.py
    uv run --group dev python -m playwright install chromium  # first run only
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "http://localhost:5173"
DEFAULT_EMAIL = "test@example.com"
DEFAULT_PASSWORD = "testpassword123"
VIEWPORTS = [(320, 568), (375, 812)]
STATIC_ROUTES = ["/", "/groups", "/settings", "/search"]

# An element past the right edge is only a bug when nothing lets the user
# scroll it into view: content inside an overflow-x auto/scroll ancestor
# (tab bars, table wrappers) is reachable by design and skipped, as are the
# TanStack devtools overlays, which are dev-only chrome hugging the edge.
OVERFLOW_SCAN_JS = """
() => {
  const vw = window.innerWidth;
  const offenders = [];
  const inScrollableX = (el) => {
    let node = el.parentElement;
    while (node && node !== document.body) {
      // The layout <main> is overflow-auto, but letting the whole content
      // area pan sideways is exactly the defect this scan exists to catch,
      // so it does not count as an intentional scroll container.
      if (node.tagName !== 'MAIN') {
        const style = getComputedStyle(node);
        if (
          (style.overflowX === 'auto' || style.overflowX === 'scroll') &&
          node.scrollWidth > node.clientWidth + 1
        ) {
          return true;
        }
      }
      node = node.parentElement;
    }
    return false;
  };
  for (const el of document.querySelectorAll('*')) {
    if (el.closest('.TanStackRouterDevtools, [class*="tsqd"]')) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width > 24 && rect.right > vw + 1 && !inScrollableX(el)) {
      offenders.push({
        tag: el.tagName.toLowerCase(),
        cls: (typeof el.className === 'string' ? el.className : '').slice(0, 80),
        right: Math.round(rect.right),
        width: Math.round(rect.width),
        text: (el.textContent || '').trim().slice(0, 50),
      });
    }
  }
  return offenders;
}
"""


def api_get(base_url: str, path: str, token: str) -> object:
    request = urllib.request.Request(
        f"{base_url}/api/v1{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def api_login(base_url: str, email: str, password: str) -> str:
    form = urllib.parse.urlencode({"username": email, "password": password})
    request = urllib.request.Request(
        f"{base_url}/api/v1/login/access-token",
        data=form.encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)["access_token"]


def discover_routes(base_url: str, email: str, password: str) -> list[str]:
    """Static routes plus one instance of each dynamic detail route."""
    routes = list(STATIC_ROUTES)
    token = api_login(base_url, email, password)

    me = api_get(base_url, "/parties/me", token)
    if me.get("admin"):
        routes.append("/admin")

    groups = api_get(
        base_url, f"/parties/groups/?user_api_id={me['api_identifier']}", token
    )
    if not groups:
        return routes

    group_id = groups[0]["api_identifier"]
    routes.append(f"/groups/{group_id}/loops")
    routes.append(f"/groups/{group_id}/settings")

    letters = api_get(
        base_url, f"/letters/letters/?group_api_id={group_id}", token
    )
    if letters:
        routes.append(f"/loops/{letters[0]['api_identifier']}")

    documents = api_get(
        base_url, f"/notebook/documents?group_api_id={group_id}", token
    )
    if documents:
        routes.append(f"/documents/{documents[0]['api_identifier']}")

    return routes


def scan_routes(
    base_url: str, email: str, password: str, routes: list[str]
) -> dict[str, list[dict]]:
    from playwright.sync_api import sync_playwright

    failures: dict[str, list[dict]] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width, height in VIEWPORTS:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                is_mobile=True,
                has_touch=True,
            )
            page = context.new_page()

            page.goto(f"{base_url}/login", wait_until="networkidle")
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.get_by_role("button", name="Sign In").click()
            page.wait_for_url(f"{base_url}/", timeout=15000)

            for route in routes:
                page.goto(f"{base_url}{route}", wait_until="networkidle")
                page.wait_for_timeout(800)
                offenders = page.evaluate(OVERFLOW_SCAN_JS)
                label = f"{route} @ {width}px"
                status = "FAIL" if offenders else "ok"
                print(f"{status:4} {label}")
                if offenders:
                    failures[label] = offenders

            context.close()
        browser.close()
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    args = parser.parse_args()

    routes = discover_routes(args.base_url, args.email, args.password)
    print(f"Scanning {len(routes)} routes at {len(VIEWPORTS)} viewports\n")

    failures = scan_routes(args.base_url, args.email, args.password, routes)
    if not failures:
        print("\nNo horizontal overflow detected.")
        return 0

    print(f"\n{len(failures)} route/viewport combinations overflow:")
    for label, offenders in failures.items():
        print(f"\n  {label}")
        for offender in offenders[:8]:
            print(
                f"    <{offender['tag']}> right={offender['right']} "
                f"width={offender['width']} cls={offender['cls']!r} "
                f"text={offender['text']!r}"
            )
    return 1


if __name__ == "__main__":
    sys.exit(main())
