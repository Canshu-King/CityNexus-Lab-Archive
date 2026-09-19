$ErrorActionPreference = "Continue"
$work = "D:\moodle\CityNexus-Tools\DSH-EAC-V19-CapabilityExperience-20260915"
$zip = "D:\moodle\CityNexus-Tools\CityNexus-DSH-EAC-V19-CapabilityExperience-20260915.zip"
$stage = Join-Path $work "_final_stage_noon"
$buildLog = Join-Path $work "evidence\noon_build_results.txt"
Set-Location $work
"=== V19 noon packaging run: $(Get-Date -Format o) ===" | Out-File -FilePath $buildLog -Append -Encoding utf8

function Add-Log([string]$text) {
  $text | Out-File -FilePath $buildLog -Append -Encoding utf8
}
function Run-Step([string]$label, [scriptblock]$body) {
  Add-Log ""
  Add-Log "--- $label ---"
  try {
    & $body *>> $buildLog
    Add-Log "exit=$LASTEXITCODE"
  } catch {
    Add-Log "exception=$($_.Exception.Message)"
  }
}

Run-Step "TypeScript" { npx tsc -p tsconfig.capability.json --noEmit }
Run-Step "Vite build" { npx vite build --config reference-app/vite.config.ts }
Run-Step "Playwright" { npx playwright test --config tests/playwright.config.ts }

Add-Log ""
Add-Log "--- Patch apply check against main tree (read-only) ---"
$main = "D:\moodle\CityNexus"
Get-ChildItem -Path (Join-Path $work "patches") -Filter "*.patch" | Sort-Object Name | ForEach-Object {
  Push-Location $main
  $result = & git apply --check $_.FullName 2>&1
  $code = $LASTEXITCODE
  Pop-Location
  Add-Log "$($_.Name): exit=$code $result"
}

if (Test-Path $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null

$items = @(
  "citynexus_eac_v19_capability_experience",
  "patches",
  "reference-app",
  "tests",
  "evidence",
  "DSH_EAC_V19_CAPABILITY_EXPERIENCE_REPORT.md",
  "CAPABILITY_UI_CONTRACT.md",
  "ACCESSIBILITY_EVIDENCE_UX.md",
  "MOBILE_CAPABILITY_UX.md",
  "A11Y_VALIDATION.md",
  "CODEX_MERGE_GUIDE_V19.md",
  "tsconfig.capability.json"
)
foreach ($item in $items) {
  $src = Join-Path $work $item
  if (Test-Path $src) {
    Copy-Item -LiteralPath $src -Destination $stage -Recurse -Force
  } else {
    Add-Log "missing from package: $item"
  }
}

# Remove development-only artifacts from the staged copy.
foreach ($exclude in @("reference-app\dist", "tests\test-results", "reference-app\node_modules")) {
  $target = Join-Path $stage $exclude
  if (Test-Path $target) { Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue }
}

if (Test-Path $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -Force -CompressionLevel Optimal
Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path $zip) {
  $info = Get-Item -LiteralPath $zip
  Add-Log "FINAL_ZIP=$($info.FullName)"
  Add-Log "FINAL_ZIP_BYTES=$($info.Length)"
} else {
  Add-Log "FINAL_ZIP_MISSING"
}
Add-Log "=== packaging finished: $(Get-Date -Format o) ==="
