#!/usr/bin/env bash
# V19.2.2 移动端聚焦探测：启动隔离实验室 -> 逐流程准备状态 -> 浏览器验证 -> 清理
set -u
export PYTHONIOENCODING=utf-8
LAB="D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915"
PY="D:/moodle/CityNexus/.venv/Scripts/python.exe"
NODE="C:/Users/仓鼠王/.workbuddy-ai/binaries/node/versions/22.22.2-2/node.exe"
API="http://127.0.0.1:8000/api/v1"
JID="22222222-2222-4222-8222-222222222222"

cd "$LAB" || exit 1
mkdir -p evidence/_db
rm -f evidence/_db/web_lab_d.db
export CITYNEXUS_DATABASE_URL="sqlite:///$LAB/evidence/_db/web_lab_d.db"
export CITYNEXUS_AI_ENABLED=false

"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  --app-dir snapshot_d/backend > /tmp/be.log 2>&1 &
BE=$!
cd snapshot_d/frontend || exit 1
"$NODE" "D:/moodle/CityNexus/frontend/node_modules/vite/bin/vite.js" \
  --host 127.0.0.1 --port 4214 --strictPort > /tmp/fe.log 2>&1 &
FE=$!
cd "$LAB" || exit 1
for i in $(seq 1 90); do
  if (echo > /dev/tcp/127.0.0.1/8000) >/dev/null 2>&1 && \
     (echo > /dev/tcp/127.0.0.1/4214) >/dev/null 2>&1; then break; fi
  sleep 1
done
echo "backend_up=$( (echo > /dev/tcp/127.0.0.1/8000) >/dev/null 2>&1 && echo yes || echo no )"
echo "frontend_up=$( (echo > /dev/tcp/127.0.0.1/4214) >/dev/null 2>&1 && echo yes || echo no )"

PROBE_MODE="${PROBE_MODE:-all}" \
  WEB_BASE=http://127.0.0.1:4214 \
  API_BASE=http://127.0.0.1:8000 \
  OUT_PATH="evidence/${OUT_NAME:-mobile_probe_d.json}" \
  EXPIRE_SCRIPT="$LAB/expire_evidence.py" \
  LAB_PY="$PY" \
  timeout 900 "$NODE" mobile_probe.cjs
RC=$?

kill $BE $FE >/dev/null 2>&1
sleep 1
netstat -ano 2>/dev/null | grep -E ":8000|:4214" | grep LISTENING | awk '{print $NF}' | sort -u | \
  while read pid; do taskkill //F //PID "$pid" >/dev/null 2>&1; done
exit $RC
