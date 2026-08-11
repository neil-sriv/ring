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
#   git fetch origin && git checkout -B dev <this-sha>
#   ./dev_util/deploy_host.sh --skip-git <this-sha>
# Do not use --rollback-on-fail with the pre-cutover script — it asserts
# checkout git.sha, which goes away when ./.git is unmounted.
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
  --rollback-on-fail    On verify failure, re-run against the pre-deploy SHA
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

previous_sha="$(git rev-parse HEAD)"

if [[ "$SKIP_GIT" -eq 0 ]]; then
  echo "==> Syncing git"
  git fetch --prune origin
  if [[ -z "$SHA" ]]; then
    SHA="$(git rev-parse "origin/${BRANCH}")"
  else
    SHA="$(git rev-parse --verify "${SHA}^{commit}")"
  fi
  # Stay on a named branch so later `git pull` still works.
  git checkout -B "$BRANCH" "$SHA"
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
ring_cmd compose any --profile prod up -d --force-recreate

verify_version() {
  local want="$1"
  python3 - "$VERSION_URL" "$want" "$VERIFY_ATTEMPTS" "$VERIFY_SLEEP_SECS" <<'PY'
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

url, want, attempts_s, sleep_s = sys.argv[1:5]
attempts = int(attempts_s)
sleep = float(sleep_s)
last_error = "no attempts"
payload: dict[str, object] = {}

for attempt in range(1, attempts + 1):
    try:
        # Cloudflare blocks the default Python-urllib User-Agent (1010 / 403).
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ring-deploy-host/1.0"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        last_error = str(exc)
        time.sleep(sleep)
        continue

    image = (
        payload.get("image_build")
        if isinstance(payload.get("image_build"), dict)
        else {}
    )
    image_sha = image.get("sha")
    print(json.dumps(payload, indent=2))
    # After the image-filesystem cutover, checkout git.sha tracks host
    # git pull (or is unavailable). The running API is image_build.sha.
    if image_sha == want:
        sys.exit(0)
    last_error = (
        f"version mismatch (attempt {attempt}/{attempts}): "
        f"image_build.sha={image_sha!r} want={want!r}"
    )
    time.sleep(sleep)

print(last_error, file=sys.stderr)
sys.exit(1)
PY
}

if [[ "$SKIP_VERIFY" -eq 0 ]]; then
  echo "==> Verifying ${VERSION_URL} == ${SHA}"
  if ! verify_version "$SHA"; then
    if [[ "$ROLLBACK_ON_FAIL" -eq 1 && "$previous_sha" != "$SHA" ]]; then
      echo "==> Verify failed; rolling back to ${previous_sha}" >&2
      "$0" --no-rollback-on-fail "$previous_sha" || true
    fi
    exit 1
  fi
fi

echo "==> Deploy complete (${SHA})"
