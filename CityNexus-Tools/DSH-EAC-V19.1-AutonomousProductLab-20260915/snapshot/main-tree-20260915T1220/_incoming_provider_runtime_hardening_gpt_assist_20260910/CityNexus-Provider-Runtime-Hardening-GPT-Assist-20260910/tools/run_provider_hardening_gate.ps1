$ErrorActionPreference = "Stop"

$repo = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$backend = Join-Path $repo "backend"
$frontend = Join-Path $repo "frontend"

Push-Location $backend
try {
    python -m pytest -q tests/test_provider_runtime_gate.py tests/test_gpt_adversarial_provider_hardening.py
    python -m pytest -q
    python -m compileall -q app tests
    ruff check .
    ruff format --check .
}
finally { Pop-Location }

Push-Location $repo
try { python tools/verify_openapi_parity.py }
finally { Pop-Location }

Push-Location $frontend
try {
    npm run build
    npm run test:e2e
}
finally { Pop-Location }
