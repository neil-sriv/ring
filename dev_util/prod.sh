#!/bin/bash

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
    PYTHON="${PYTHON3:-python3}"
fi

# ring-frontend is served by Cloudflare Workers (auto-deployed on dev
# merges), not from an image on this host.
declare -a images=("ring-api" "ring-llm")

for i in "${images[@]}"
do
    docker pull public.ecr.aws/z2k1e8p1/"$i":latest
    docker tag public.ecr.aws/z2k1e8p1/"$i":latest "prod-$i":latest
    docker rmi public.ecr.aws/z2k1e8p1/"$i":latest
done

# Snapshot pulled image identity for GET /version. Compose up refreshes
# this with running container ids after --force-recreate.
"$PYTHON" "${ROOT}/dev_util/runtime_version.py" write \
    --images prod-ring-api,prod-ring-llm \
    || true