#!/bin/bash
# Pull ECR images onto the prod host and retag as prod-*.
#
# Usage:
#   ./dev_util/prod.sh                  # ring-api:latest
#   ./dev_util/prod.sh <git-sha>        # ring-api:<sha> (deps / image pin)
#   ./dev_util/prod.sh --image ring-api --image ring-llm <sha>
#
# This only swaps the image (deps + RING_BUILD_GIT_* + baked Python).
# Prod no longer bind-mounts ./ring, so a SHA pull is a code rollback.
# Prefer deploy_host.sh so migrate / compose / verify stay in lockstep.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
    PYTHON="${PYTHON3:-python3}"
fi

ECR_URI_BASE="public.ecr.aws/z2k1e8p1/"
TAG="latest"
IMAGES=()

usage() {
  cat <<'EOF'
Usage: prod.sh [--image name]... [sha]

Pull ECR Public images and retag them as prod-<name>:latest for Compose.

  --image <name>   Image to pull (repeatable). Default: ring-api
  sha              Tag to pull instead of :latest (usually a git SHA)

Prefer the full host rollout (git + pull + migrate + up + verify):
  ./dev_util/deploy_host.sh <sha>
  ./dev_util/deploy_host.sh <previous-sha>   # rollback

This script only pulls/retags images.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --image)
      IMAGES+=("${2:-}")
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ "$TAG" != "latest" ]]; then
        echo "Only one sha argument is allowed" >&2
        exit 1
      fi
      TAG="$1"
      shift
      ;;
  esac
done

if [[ ${#IMAGES[@]} -eq 0 ]]; then
  IMAGES=("ring-api")
fi

for image in "${IMAGES[@]}"; do
  remote="${ECR_URI_BASE}${image}:${TAG}"
  docker pull "$remote"
  docker tag "$remote" "prod-${image}:latest"
  docker rmi "$remote" || true
done

# Snapshot pulled image identity for GET /version. Compose up refreshes
# this with running container ids after --force-recreate.
snapshot_images=""
for image in "${IMAGES[@]}"; do
  if [[ -n "$snapshot_images" ]]; then
    snapshot_images+=","
  fi
  snapshot_images+="prod-${image}"
done
"$PYTHON" "${ROOT}/dev_util/runtime_version.py" write \
    --images "$snapshot_images" \
    || true
