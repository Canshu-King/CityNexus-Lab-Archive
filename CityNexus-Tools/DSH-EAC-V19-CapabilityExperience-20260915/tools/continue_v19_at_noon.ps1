$ErrorActionPreference = "Continue"
$work = "D:\moodle\CityNexus-Tools\DSH-EAC-V19-CapabilityExperience-20260915"
$startLog = Join-Path $work "evidence\noon_continuation_started.txt"
$doneLog = Join-Path $work "evidence\noon_continuation_completed.txt"
$codexLog = Join-Path $work "evidence\noon_codex.log"
Set-Location $work
"Started scheduled V19 continuation at $(Get-Date -Format o)" | Out-File -FilePath $startLog -Encoding utf8

$codex = Get-Command codex -ErrorAction SilentlyContinue
if ($codex) {
  "Running Codex exec with half-price-API continuation prompt at $(Get-Date -Format o)" | Out-File -FilePath $codexLog -Encoding utf8
  $promptPath = Join-Path $work "tools\noon_prompt.txt"
  $prompt = Get-Content -LiteralPath $promptPath -Raw -Encoding utf8
  & codex -C $work -a never -s workspace-write exec $prompt *>> $codexLog
  "codex_exit=$LASTEXITCODE" | Out-File -FilePath $codexLog -Append -Encoding utf8
} else {
  "codex CLI not found; running deterministic package/validation only." | Out-File -FilePath $codexLog -Encoding utf8
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $work "tools\package_v19_windows.ps1") *>> $codexLog
"Completed scheduled V19 continuation at $(Get-Date -Format o)" | Out-File -FilePath $doneLog -Encoding utf8
