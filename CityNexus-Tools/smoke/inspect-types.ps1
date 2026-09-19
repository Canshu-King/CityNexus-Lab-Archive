Import-Module Visio -Force
[VisioAutomation.Core.Rectangle].GetConstructors() | ForEach-Object { $_.ToString() }
[VisioAutomation.Core.Rectangle] | Get-Member -Static
