#!/usr/bin/env bash
# Full backend rollout on the prod EC2 host.
#
# This is the one command humans and (later) Actions should run on the box.
# prod.sh only pulls images; this script also syncs git (compose/nginx),
# migrates, recreates Compose, and checks GET /api/v1/version.
# Prod runs the image filesystem (no ./ring bind-mount, no --reload).
#
# Usage:
#   ./dev_util/deploy_host.sh <published-sha>
#   ./dev_util/deploy_host.sh --rollback-on-fail <published-sha>
#
# The sha must exist as public.ecr.aws/z2k1e8p1/ring-api:<sha> (a
# publish_api.yml run). Docs-only origin/dev tips have no image tag.
#
# First apply of the image-filesystem cutover (old script still on disk):
#   git fetch origin && git checkout -f -B dev <this-sha>
#   ./dev_util/deploy_host.sh --skip-git <this-sha>
# --rollback-on-fail captures live /version image_build.sha *before*
# mutating. The pre-cutover script on the box still asserts git.sha and
# rolls back to HEAD — do not use that flag until this script is on disk.
#
# Rollback to a pre-cutover image without remounting ./ring:
#   ./dev_util/deploy_host.sh --skip-git <previous-image-sha>

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION_URL="${RING_VERSION_URL:-https://ring.neilsriv.tech/api/v1/version}"
BRANCH="${RING_DEPLOY_BRANCH:-dev}"
SHA=""
SKIP_GIT=0
SKIP_PULL=0
SKIP_MIGRATE=0
SKIP_VERIFY=0
ROLLBACK_ON_FAIL=0
VERIFY_ATTEMPTS="${RING_VERSION_ATTEMPTS:-30}"
VERIFY_SLEEP_SECS="${RING_VERSION_SLEEP_SECS:-2}"

usage() {
  cat <<'EOF'
Usage: deploy_host.sh [options] [sha]

Full host rollout: git sync, pull ECR image, migrate, compose up, verify.

  sha                   Published image tag / commit (default: origin/dev tip)
  --skip-git            Do not fetch/checkout (use to roll back the image
                        without reverting compose to a pre-cutover SHA)
  --skip-pull           Do not run prod.sh
  --skip-migrate        Do not run `uv run ring db upgrade --profile prod`
  --skip-verify         Do not curl GET /api/v1/version
  --rollback-on-fail    On verify failure, re-run against the pre-deploy
                        image SHA (live image_build.sha; HEAD if probe fails)
  -h, --help            Show this help

Env:
  RING_VERSION_URL      Default https://ring.neilsriv.tech/api/v1/version
  RING_DEPLOY_BRANCH    Branch to keep checked out (default: dev)

Rollback:
  ./dev_util/deploy_host.sh <previous-published-sha>
  ./dev_util/deploy_host.sh --skip-git <pre-cutover-image-sha>
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --skip-git)
      SKIP_GIT=1
      shift
      ;;
    --skip-pull)
      SKIP_PULL=1
      shift
      ;;
    --skip-migrate)
      SKIP_MIGRATE=1
      shift
      ;;
    --skip-verify)
      SKIP_VERIFY=1
      shift
      ;;
    --rollback-on-fail)
      ROLLBACK_ON_FAIL=1
      shift
      ;;
    --no-rollback-on-fail)
      ROLLBACK_ON_FAIL=0
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$SHA" ]]; then
        echo "Only one sha argument is allowed" >&2
        exit 1
      fi
      SHA="$1"
      shift
      ;;
  esac
done

ring_cmd() {
  if command -v uv >/dev/null 2>&1; then
    uv run ring "$@"
  else
    ring "$@"
  fi
}

# Cloudflare blocks the default Python-urllib User-Agent (1010 / 403).
version_request_python() {
  python3 - "$@" <<'PY'
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

url = sys.argv[1]
want = sys.argv[2] if len(sys.argv) > 2 else ""
attempts = int(sys.argv[3]) if len(sys.argv) > 3 else 1
sleep = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
last_error = "no attempts"
payload: dict[str, object] = {}

for attempt in range(1, attempts + 1):
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ring-deploy-host/1.0"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        last_error = str(exc)
        if sleep:
            time.sleep(sleep)
        continue

    image = (
        payload.get("image_build")
        if isinstance(payload.get("image_build"), dict)
        else {}
    )
    image_sha = image.get("sha")
    if want:
        print(json.dumps(payload, indent=2))
        if image_sha == want:
            sys.exit(0)
        last_error = (
            f"version mismatch (attempt {attempt}/{attempts}): "
            f"image_build.sha={image_sha!r} want={want!r}"
        )
        if sleep:
            time.sleep(sleep)
        continue
    if isinstance(image_sha, str) and image_sha.strip():
        print(image_sha.strip())
        sys.exit(0)
    last_error = "image_build.sha missing from /version"
    break

print(last_error, file=sys.stderr)
sys.exit(1)
PY
}

read_live_image_sha() {
  version_request_python "$VERSION_URL"
}

previous_image_sha=""
if [[ "$ROLLBACK_ON_FAIL" -eq 1 ]]; then
  echo "==> Capturing live image_build.sha from ${VERSION_URL}"
  if previous_image_sha="$(read_live_image_sha)"; then
    echo "==> Rollback target is live image ${previous_image_sha}"
  else
    previous_image_sha="$(git rev-parse HEAD)"
    echo "==> /version probe failed; falling back to checkout ${previous_image_sha}" >&2
  fi
fi

if [[ "$SKIP_GIT" -eq 0 ]]; then
  echo "==> Syncing git"
  git fetch --prune origin
  if [[ -z "$SHA" ]]; then
    SHA="$(git rev-parse "origin/${BRANCH}")"
  else
    SHA="$(git rev-parse --verify "${SHA}^{commit}")"
  fi
  # Stay on a named branch so later `git pull` still works.
  # -f: discard local edits to tracked files (e.g. a host-side `uv`
  # rewriting uv.lock). Untracked files like .env are left alone. Prod
  # runs the image filesystem; the checkout only supplies compose/nginx.
  git checkout -f -B "$BRANCH" "$SHA"
else
  if [[ -z "$SHA" ]]; then
    SHA="$(git rev-parse HEAD)"
  fi
fi

if [[ "$SKIP_PULL" -eq 0 ]]; then
  echo "==> Pulling images for ${SHA}"
  "${ROOT}/dev_util/prod.sh" "$SHA"
fi

if [[ "$SKIP_MIGRATE" -eq 0 ]]; then
  echo "==> Running migrations"
  ring_cmd db upgrade --profile prod
fi

echo "==> Recreating Compose (prod)"
# --remove-orphans: the compose file is the source of truth — containers
# from retired services (e.g. the old ring-frontend SPA container) are
# removed instead of lingering with restart=unless-stopped.
ring_cmd compose any --profile prod up -d --force-recreate --remove-orphans

if [[ "$SKIP_VERIFY" -eq 0 ]]; then
  echo "==> Verifying ${VERSION_URL} image_build.sha == ${SHA}"
  if ! version_request_python "$VERSION_URL" "$SHA" \
      "$VERIFY_ATTEMPTS" "$VERIFY_SLEEP_SECS"; then
    if [[ "$ROLLBACK_ON_FAIL" -eq 1 && -n "$previous_image_sha" &&
          "$previous_image_sha" != "$SHA" ]]; then
      echo "==> Verify failed; rolling back to image ${previous_image_sha}" >&2
      # Image-only restore: do not checkout the old SHA (that can remount
      # ./ring or target an unpublished checkout tag).
      "$0" --no-rollback-on-fail --skip-git "$previous_image_sha" || true
    fi
    exit 1
  fi
fi

echo "==> Deploy complete (${SHA})"
