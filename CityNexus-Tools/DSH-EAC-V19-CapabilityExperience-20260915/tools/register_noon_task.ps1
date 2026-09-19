$ErrorActionPreference = "Stop"
$work = "D:\moodle\CityNexus-Tools\DSH-EAC-V19-CapabilityExperience-20260915"
$script = Join-Path $work "tools\continue_v19_at_noon.ps1"
$taskName = "CityNexus_DSH_EAC_V19_Noon_Continuation"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"$script`"")
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date "2026-09-15 12:00:00")
$principal = New-ScheduledTaskPrincipal -UserId ("$env:USERDOMAIN\$env:USERNAME") -LogonType Interactive
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Description "Resume V19 Capability Experience at noon half-price API window" -Force | Out-Null
Write-Output "registered"
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State | Format-Table -AutoSize
Get-ScheduledTaskInfo -TaskName $taskName | Select-Object NextRunTime, LastRunTime, LastTaskResult | Format-Table -AutoSize
