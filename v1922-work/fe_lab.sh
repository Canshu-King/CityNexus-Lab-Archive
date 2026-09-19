#!/usr/bin/env bash
set -u
export PYTHONIOENCODING=utf-8
REPO="D:/moodle/CityNexus"
NODE="C:/Users/仓鼠王/.workbuddy-ai/binaries/node/versions/22.22.2-2/node.exe"
cd "$REPO/frontend" || exit 1
"$NODE" node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort > /tmp/fe.log 2>&1 &
echo "FE_PID=$!"
for i in $(seq 1 60); do (echo > /dev/tcp/127.0.0.1/5173) >/dev/null 2>&1 && break; sleep 1; done
(echo > /dev/tcp/127.0.0.1/5173) >/dev/null 2>&1 && echo "frontend UP" || echo "frontend DOWN"
wait
