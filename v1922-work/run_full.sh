#!/usr/bin/env bash
set -u
export PYTHONIOENCODING=utf-8
PY="D:/moodle/CityNexus/.venv/Scripts/python.exe"
NODE="C:/Users/仓鼠王/.workbuddy-ai/binaries/node/versions/22.22.2-2/node.exe"
cd /d/moodle/_v1922_work || exit 1

# backend (live credentials, keeps DB)
nohup "$PY" launch_be.py > /tmp/be_launch.txt 2>&1 &
# frontend
( cd /d/moodle/CityNexus/frontend && "$NODE" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort > /tmp/fe.log 2>&1 ) &
for i in $(seq 1 90); do
  if (echo > /dev/tcp/127.0.0.1/8000) >/dev/null 2>&1 && (echo > /dev/tcp/127.0.0.1/5173) >/dev/null 2>&1; then break; fi
  sleep 1
done
echo "be_up=$( (echo > /dev/tcp/127.0.0.1/8000) >/dev/null 2>&1 && echo yes || echo no )"
echo "fe_up=$( (echo > /dev/tcp/127.0.0.1/5173) >/dev/null 2>&1 && echo yes || echo no )"
