$ErrorActionPreference = "Stop"
$taskName = "CityNexus_DSH_EAC_V19_Noon_Continuation"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 6)
Set-ScheduledTask -TaskName $taskName -Settings $settings | Out-Null
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State | Format-Table -AutoSize
Get-ScheduledTaskInfo -TaskName $taskName | Select-Object NextRunTime, LastRunTime, LastTaskResult | Format-Table -AutoSize
