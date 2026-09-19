Import-Module Visio -Force
$null = New-VisioApplication
$app = Get-VisioApplication
$doc = New-VisioDocument
$page = Get-VisioPage -Document $doc | Select-Object -First 1
$rect = [VisioAutomation.Core.Rectangle]::new(1, 1, 5, 3)
$shape = New-VisioShape -Rectangle -BoundingBox $rect
Set-VisioUserDefinedCell -Shape $shape -Name TEST_SPEC_ID -Value TEST-SPEC-ID
$path = 'D:\moodle\CityNexus-Tools\smoke\visioautomation-smoke.vsdx'
Save-VisioDocument -Document $doc -Filename $path
$cell = $shape.CellsU('User.TEST_SPEC_ID').FormulaU
$result = [pscustomobject]@{
    application = ($null -ne $app)
    document = ($null -ne $doc)
    page = ($null -ne $page)
    shape = ($null -ne $shape)
    pathExists = (Test-Path -LiteralPath $path)
    userCell = [string]$cell
}
$result | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 'D:\moodle\CityNexus-Tools\smoke\visioautomation-smoke.json'
Close-VisioDocument -Document $doc
Close-VisioApplication
$result | ConvertTo-Json -Depth 4
