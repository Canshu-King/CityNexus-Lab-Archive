#!/usr/bin/env bash
set -u
export PYTHONIOENCODING=utf-8
LAB="D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915"
PY="D:/moodle/CityNexus/.venv/Scripts/python.exe"
NODE="C:/Users/仓鼠王/.workbuddy-ai/binaries/node/versions/22.22.2-2/node.exe"
cd "$LAB" || exit 1
mkdir -p evidence/_db
export CITYNEXUS_DATABASE_URL="sqlite:///$LAB/evidence/_db/web_lab_d.db"
export CITYNEXUS_AI_ENABLED=false
export PYTHONDONTWRITEBYTECODE=1
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir snapshot_d/backend > /tmp/be.log 2>&1 &
BE=$!
cd snapshot_d/frontend || exit 1
"$NODE" "D:/moodle/CityNexus/frontend/node_modules/vite/bin/vite.js" --host 127.0.0.1 --port 4214 --strictPort > /tmp/fe.log 2>&1 &
FE=$!
cd "$LAB" || exit 1
for i in $(seq 1 90); do
  if (echo > /dev/tcp/127.0.0.1/8000) >/dev/null 2>&1 && (echo > /dev/tcp/127.0.0.1/4214) >/dev/null 2>&1; then break; fi
  sleep 1
done
echo "LAB_READY be=$BE fe=$FE"
# 准备中途恢复场景（必须走 HTTP，与浏览器共用同一个数据库）
API=http://127.0.0.1:8000/api/v1
JID=22222222-2222-4222-8222-222222222222
curl -s -X POST $API/demo/reset > /dev/null
curl -s -X POST $API/journeys/$JID/plans/generate -H "Content-Type: application/json" -d '{}' > /dev/null
PID=$(curl -s $API/journeys/$JID/plans | "$PY" -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
curl -s -X POST $API/journeys/$JID/plans/$PID/select > /dev/null
curl -s -X POST $API/journeys/$JID/start > /dev/null
echo "confirm=$(curl -s -X POST $API/journeys/$JID/capabilities/confirm -H 'Content-Type: application/json' -d '[{"code":"STEP_FREE_REQUIRED","severity":"HARD","params":{}}]' | head -c 120)"
"$NODE" /tmp/dbg_ui.cjs
kill $BE $FE >/dev/null 2>&1
netstat -ano 2>/dev/null | grep -E ":8000|:4214" | grep LISTENING | awk '{print $NF}' | sort -u | while read pid; do taskkill //F //PID "$pid" >/dev/null 2>&1; done
