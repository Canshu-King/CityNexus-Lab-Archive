#!/bin/bash
# Start exactly ONE backend that reads the launch_be environment contract.
cd /d/moodle/CityNexus/backend
export CITYNEXUS_DATABASE_URL="sqlite:///D:/moodle/_v1922_work/fc_evidence/_db/live.db"
export PYTHONDONTWRITEBYTECODE=1
export CITYNEXUS_AI_ENABLED=true
export CITYNEXUS_AI_PROVIDER=deepseek
export CITYNEXUS_PHOTON_ENABLED=true
export CITYNEXUS_OPEN_METEO_ENABLED=true
export CITYNEXUS_REAL_CITY_ENABLED=true
export CITYNEXUS_REAL_CITY_MODE=live
export CITYNEXUS_REAL_CITY_TIMEOUT_SECONDS=60
exec /d/moodle/CityNexus/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
