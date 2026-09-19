#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-/path/to/CityNexus}"
cd "$REPO_ROOT"

echo '== Non-destructive Git inspection =='
git status --short
git diff --stat

cd backend
PYTHON="${PYTHON:-python}"

echo '== Focused post-Goal semantic gate =='
"$PYTHON" -m pytest -q tests/test_post_goal_five_defects.py tests/test_backend_connected_golden_contract.py

echo '== Full backend regression =='
"$PYTHON" -m pytest -q

echo '== Compileall =='
"$PYTHON" -m compileall -q app tests

echo 'Run Ruff and the repository OpenAPI exact-match validator in the actual project environment.'
