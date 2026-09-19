#!/usr/bin/env bash
set -u
export PYTHONIOENCODING=utf-8
REPO="D:/moodle/CityNexus"
PY="$REPO/.venv/Scripts/python.exe"
NODE="C:/Users/仓鼠王/.workbuddy-ai/binaries/node/versions/22.22.2-2/node.exe"
DB="D:/moodle/_v1922_work/rescue_evidence/_db/rescue.db"
mkdir -p "$(dirname "$DB")"
rm -f "$DB"
cd "$REPO/backend" || exit 1
CITYNEXUS_DATABASE_URL="sqlite:///$DB" CITYNEXUS_AI_ENABLED=false \
  "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/rescue_be.log 2>&1 &
BE=$!
cd "$REPO/frontend" || exit 1
"$NODE" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort > /tmp/rescue_fe.log 2>&1 &
FE=$!
for i in $(seq 1 90); do
  if (echo > /dev/tcp/127.0.0.1/8000) >/dev/null 2>&1 && (echo > /dev/tcp/127.0.0.1/5173) >/dev/null 2>&1; then break; fi
  sleep 1
done
echo "backend_up=$( (echo > /dev/tcp/127.0.0.1/8000) >/dev/null 2>&1 && echo yes || echo no )"
echo "frontend_up=$( (echo > /dev/tcp/127.0.0.1/5173) >/dev/null 2>&1 && echo yes || echo no )"
echo "BE_PID=$BE FE_PID=$FE"
