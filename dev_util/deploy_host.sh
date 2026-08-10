#!/usr/bin/env bash
# Roll out the latest ECR images on the prod EC2 host.
#
# Typical usage (from the ring repo checkout on the host):
#   ./dev_util/deploy_host.sh
#   ./dev_util/deploy_host.sh --ref abc123 --image ring-api --image ring-frontend
#
# Or via the CLI wrapper:
#   ring deploy host --ref abc123

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ECR_URI_BASE="public.ecr.aws/z2k1e8p1/"
REF=""
SKIP_GIT=0
SKIP_MIGRATE=0
IMAGES=()

usage() {
  cat <<'EOF'
Usage: deploy_host.sh [options]

Options:
  --ref <git-ref>       Fetch and check out this ref before rolling out
  --skip-git            Do not run git fetch/checkout
  --skip-migrate        Do not run `ring db upgrade`
  --image <name>        Image to pull (repeatable). Default: ring-api ring-frontend
  -h, --help            Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ref)
      REF="${2:-}"
      shift 2
      ;;
    --skip-git)
      SKIP_GIT=1
      shift
      ;;
    --skip-migrate)
      SKIP_MIGRATE=1
      shift
      ;;
    --image)
      IMAGES+=("${2:-}")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ${#IMAGES[@]} -eq 0 ]]; then
  IMAGES=("ring-api" "ring-frontend")
fi

ring_cmd() {
  if command -v uv >/dev/null 2>&1; then
    uv run ring "$@"
  else
    ring "$@"
  fi
}

if [[ "$SKIP_GIT" -eq 0 ]]; then
  echo "==> Syncing git checkout"
  git fetch --prune origin
  if [[ -n "$REF" ]]; then
    git checkout --detach "$REF"
  else
    # Stay on the current branch tip if one is checked out; otherwise leave HEAD.
    if branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" && [[ "$branch" != "HEAD" ]]; then
      git pull --ff-only origin "$branch"
    fi
  fi
fi

echo "==> Pulling images from ECR Public"
for image in "${IMAGES[@]}"; do
  remote="${ECR_URI_BASE}${image}:latest"
  docker pull "$remote"
  docker tag "$remote" "prod-${image}:latest"
  docker rmi "$remote" || true
done

if printf '%s\n' "${IMAGES[@]}" | grep -qx "ring-frontend"; then
  echo "==> Syncing react/dist from prod-ring-frontend (SW / manifest for nginx)"
  mkdir -p react/dist
  cid="$(docker create prod-ring-frontend:latest)"
  docker cp "${cid}:/usr/share/nginx/html/." react/dist/
  docker rm "$cid" >/dev/null
fi

if [[ "$SKIP_MIGRATE" -eq 0 ]]; then
  echo "==> Running migrations"
  ring_cmd db upgrade
fi

echo "==> Starting Compose (prod profile)"
ring_cmd compose any --profile prod up -d
ring_cmd compose any --profile prod restart nginx

echo "==> Deploy complete"
ring_cmd compose any --profile prod ps
