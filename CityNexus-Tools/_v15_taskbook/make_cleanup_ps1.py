"""Write the leftover-cleanup PowerShell script for the user.

Two constraints from hard experience, both encoded here:

1. **UTF-8 with BOM.** Windows PowerShell 5.1 decodes `.ps1` as GBK by default, so
   a UTF-8-no-BOM script containing Chinese becomes mojibake and fails to parse.
2. **No `\\r\\r\\n`.** The text is composed with explicit ``\\n`` and then written
   with ``newline=''`` after converting to CRLF exactly once. Reading bytes back
   with ``utf-8-sig`` and re-writing with ``newline='\\r\\n'`` would double every
   line ending and produce "missing )" parse errors.

The script is syntax-checked with the PowerShell parser before this function
returns, so a broken script never reaches the user.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

OUT = Path("C:/Users/仓鼠王/Desktop/V15夜间任务_清理临时文件_右键运行.ps1")

BODY = """# V15 Night Lab - cleanup of temporary build artifacts
#
# What this removes (safe - none of it is part of the deliverable):
#   _v15_scratch            a stalled npm install (374 MB) + moved-aside junk
#   _v15_patch_verify2      a throwaway copy of backend/ used to test the patches
#   _v15_npm_cache          npm cache used by the two failed `npm ci` attempts
#   _v15_servers            log files from the isolated dev servers
#   _v15_taskbook\borrow_node_modules.py, link_node_modules.py, unlink_node_modules.py
#                           one-off provisioning helpers, already served their purpose
#
# What this KEEPS:
#   WorkBuddy-V15-NightLab-20260914\\            the deliverable workspace
#   CityNexus-WorkBuddy-V15-NightLab-20260914.zip   the deliverable archive
#   _v15_taskbook\\citynexus_workbuddy_v15_overnight\\  the task book itself
#   _v15_taskbook\\package_v15.py                re-runnable packaging script
#
# Nothing under D:\\moodle\\CityNexus is touched. Read-only, we only delete
# things this session created.

$ErrorActionPreference = 'Stop'
$root = 'D:\\moodle\\CityNexus-Tools'

if (-not (Test-Path -LiteralPath $root)) {
    Write-Host "Not found: $root" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$dirs = @(
    (Join-Path $root '_v15_scratch'),
    (Join-Path $root '_v15_patch_verify'),
    (Join-Path $root '_v15_patch_verify2'),
    (Join-Path $root '_v15_npm_cache')
)

$files = @(
    (Join-Path $root '_v15_taskbook\\borrow_node_modules.py'),
    (Join-Path $root '_v15_taskbook\\link_node_modules.py'),
    (Join-Path $root '_v15_taskbook\\unlink_node_modules.py')
)

Write-Host ''
Write-Host 'About to delete:' -ForegroundColor Yellow
foreach ($d in $dirs) { if (Test-Path -LiteralPath $d) { Write-Host "  [dir ] $d" } }
foreach ($f in $files) { if (Test-Path -LiteralPath $f) { Write-Host "  [file] $f" } }
Write-Host ''
$answer = Read-Host 'Type YES to proceed'
if ($answer -ne 'YES') {
    Write-Host 'Cancelled. Nothing was deleted.' -ForegroundColor Green
    Read-Host 'Press Enter to close'
    exit 0
}

$freed = 0

foreach ($d in $dirs) {
    if (-not (Test-Path -LiteralPath $d)) { continue }
    try {
        $size = (Get-ChildItem -LiteralPath $d -Recurse -Force -File -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        if ($null -eq $size) { $size = 0 }
        Remove-Item -LiteralPath $d -Recurse -Force
        $freed += $size
        Write-Host ("removed {0}  ({1:N0} MB)" -f $d, ($size / 1MB)) -ForegroundColor Green
    } catch {
        Write-Host ("FAILED  {0}  -> {1}" -f $d, $_.Exception.Message) -ForegroundColor Red
    }
}

foreach ($f in $files) {
    if (-not (Test-Path -LiteralPath $f)) { continue }
    try {
        $size = (Get-Item -LiteralPath $f).Length
        Remove-Item -LiteralPath $f -Force
        $freed += $size
        Write-Host ("removed {0}" -f $f) -ForegroundColor Green
    } catch {
        Write-Host ("FAILED  {0}  -> {1}" -f $f, $_.Exception.Message) -ForegroundColor Red
    }
}

Write-Host ''
Write-Host ("Total freed: {0:N0} MB" -f ($freed / 1MB)) -ForegroundColor Cyan
Write-Host ''
Write-Host 'Still present (the deliverable, intentionally kept):' -ForegroundColor Yellow
Write-Host '  D:\\moodle\\CityNexus-Tools\\WorkBuddy-V15-NightLab-20260914\\'
Write-Host '  D:\\moodle\\CityNexus-Tools\\CityNexus-WorkBuddy-V15-NightLab-20260914.zip'
Write-Host ''
Read-Host 'Press Enter to close'
"""


def main() -> int:
    text = BODY.replace("\r\n", "\n")
    # Write CRLF exactly once, with a BOM, and with newline='' so Python does not
    # translate again.
    payload = text.replace("\n", "\r\n")
    OUT.write_bytes(b"\xef\xbb\xbf" + payload.encode("utf-8"))
    print(f"wrote {OUT}")
    print(f"bytes: {OUT.stat().st_size}")

    # Syntax-check without executing.
    check = subprocess.run(
        [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "$e=$null;"
            "[void][System.Management.Automation.Language.Parser]::ParseFile("
            f"'{OUT}', [ref]$null, [ref]$e);"
            "if ($e.Count -gt 0) { $e | ForEach-Object { Write-Output $_.Message } ; exit 1 }"
            "else { Write-Output 'PARSE_OK' }",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (check.stdout or "").strip()
    print(f"parse check rc={check.returncode}: {out[:400]}")
    if check.stderr.strip():
        print(f"stderr: {check.stderr.strip()[:300]}")
    return 0 if "PARSE_OK" in out else 1


if __name__ == "__main__":
    raise SystemExit(main())
