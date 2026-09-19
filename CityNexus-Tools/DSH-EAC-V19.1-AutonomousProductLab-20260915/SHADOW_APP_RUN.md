# Shadow app run notes

The isolated reference app is `shadow-app/`.  It expects the V19.1 capability
feature source at `lab/runtime/frontend/src/features/capability-experience/`.
That subset is included in the final archive for review.

Backend:

```powershell
cd lab\runtime\backend
$env:CITYNEXUS_DATABASE_URL="sqlite:///./v19_1_shadow.db"
& "D:\moodle\CityNexus\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8052
```

Frontend:

```powershell
npx vite --config shadow-app\vite.config.ts
```

Then open `http://127.0.0.1:4202/`.  The app calls `/api/v1/demo/reset` when
no traveler/journey query parameters are present, and it labels
`LIVE_SHADOW`, `RECORDED_FIXTURE`, and `OFFLINE_STALE` explicitly.
