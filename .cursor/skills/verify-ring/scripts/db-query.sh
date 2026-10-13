#!/usr/bin/env bash
# Read-only SQL against the local ring-cockroach container.
#
# Usage:
#   db-query.sh "SELECT api_identifier, name FROM \"group\" WHERE name = 'Verify-empty-RUN'"
#
# Accepts one SELECT, WITH, SHOW, or EXPLAIN statement. Refuses writes.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo 'Usage: db-query.sh "SELECT ..."' >&2
  exit 2
fi

sql="$1"
python3 - "${sql}" <<'PY'
import re
import sys

statement = sys.argv[1].strip().rstrip(";").strip()
if not statement:
    sys.exit("empty SQL")
if ";" in statement:
    sys.exit("only one statement is allowed")
if not re.match(r"(?is)^(select|with|show|explain)\b", statement):
    sys.exit("read-only SELECT, WITH, SHOW, or EXPLAIN only")
if re.search(
    r"(?is)\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy)\b",
    statement,
):
    sys.exit("refusing a statement that contains a write keyword")
PY

sudo docker exec ring-cockroach ./cockroach sql \
  --certs-dir=/root/.cockroach-certs \
  -d ring \
  --format=table \
  -e "${sql}"
