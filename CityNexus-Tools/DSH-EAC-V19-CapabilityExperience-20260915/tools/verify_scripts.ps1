$files = @("tools\continue_v19_at_noon.ps1", "tools\package_v19_windows.ps1", "tools\register_noon_task.ps1")
foreach ($f in $files) {
  try {
    [void][scriptblock]::Create((Get-Content -LiteralPath $f -Raw))
    Write-Output ("PARSE_OK " + $f)
  } catch {
    Write-Output ("PARSE_FAIL " + $f + ": " + $_.Exception.Message)
  }
}
$a = (Get-ScheduledTask -TaskName "CityNexus_DSH_EAC_V19_Noon_Continuation").Actions[0]
Write-Output ("ACTION_EXEC=" + $a.Execute)
Write-Output ("ACTION_ARGS=" + $a.Arguments)
