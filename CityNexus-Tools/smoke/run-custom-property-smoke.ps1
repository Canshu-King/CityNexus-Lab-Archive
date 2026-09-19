Import-Module Visio -Force
$outDir = 'D:\moodle\CityNexus-Tools\smoke'
$path = Join-Path $outDir 'visioautomation-custom-property-smoke.vsdx'
$resultPath = Join-Path $outDir 'custom-property-smoke-result.json'

$null = New-VisioApplication
$app = Get-VisioApplication
$doc = New-VisioDocument
$page = Get-VisioPage -Document $doc | Select-Object -First 1
$shape = New-VisioShape -Rectangle -BoundingBox ([VisioAutomation.Core.Rectangle]::new(1, 1, 5, 3))
Set-VisioCustomProperty -Name 'SpecId' -Value 'TEST-PROP-SPEC-ID' -Shape $shape
Save-VisioDocument -Document $doc -Filename $path

$comFormula = $shape.CellsU('Prop.SpecId').FormulaU
$comValue = $shape.CellsU('Prop.SpecId').ResultStr(0)
$comStatus = if ([string]$comValue -eq 'TEST-PROP-SPEC-ID') { 'PASS' } else { 'FAIL' }
$null = $shape
Close-VisioDocument -Document $doc
Close-VisioApplication
$xmlValue = $null
$xmlRowFound = $false
$xmlFormulaErrors = @{ VALUE = 0; REF = 0; NAME = 0 }
$errors = @()
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($path)
try {
    $entry = $zip.GetEntry('visio/pages/page1.xml')
    if ($null -ne $entry) {
        $reader = New-Object System.IO.StreamReader($entry.Open())
        try { $xml = [xml]$reader.ReadToEnd() } finally { $reader.Dispose() }
        foreach ($attr in $xml.SelectNodes('//@V|//@F')) {
            foreach ($kind in @('VALUE','REF','NAME')) {
                if ([string]$attr.Value -eq "#$kind!") { $xmlFormulaErrors[$kind]++ }
            }
        }
        $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
        $ns.AddNamespace('v', 'http://schemas.microsoft.com/office/visio/2012/main')
        $row = $xml.SelectSingleNode("//*[local-name()='Section' and @N='Property']/*[local-name()='Row' and @N='SpecId']", $ns)
        if ($null -ne $row) {
            $xmlRowFound = $true
            $cell = $row.SelectSingleNode("*[local-name()='Cell' and @N='Value']")
            if ($null -ne $cell) { $xmlValue = [string]$cell.V }
            if ([string]::IsNullOrEmpty($xmlValue)) {
                $cell = $row.SelectSingleNode("*[local-name()='Cell' and @N='Label']")
                if ($null -ne $cell) { $xmlValue = [string]$cell.F }
            }
        }
    }
} finally { $zip.Dispose() }

$vsdxValue = $null
$vsdxStatus = 'unsupported'
try {
    $py = 'D:\moodle\CityNexus-Tools\.venv\Scripts\python.exe'
    $probe = & $py -c "from vsdx import VisioFile; v=VisioFile(r'$path'); p=v.get_page(0); s=p.child_shapes[0]; print('UNSUPPORTED')" 2>&1
    $vsdxValue = ($probe | Select-Object -Last 1).ToString()
    if ($vsdxValue -notin @('UNSUPPORTED', 'None', '')) { $vsdxStatus = 'pass' }
} catch { $errors += $_.Exception.Message }

$result = [pscustomobject]@{
    path = $path
    property = 'Prop.SpecId'
    expected = 'TEST-PROP-SPEC-ID'
    comFormulaU = [string]$comFormula
    comResult = [string]$comValue
    comStatus = $comStatus
    xmlRowFound = $xmlRowFound
    xmlValueFormula = [string]$xmlValue
    xmlStatus = $(if ([string]$xmlValue -match 'TEST-PROP-SPEC-ID') { 'PASS' } else { 'FAIL' })
    vsdxValue = [string]$vsdxValue
    vsdxStatus = $vsdxStatus.ToUpperInvariant()
    formulaErrors = $xmlFormulaErrors
    errors = @($errors)
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $resultPath
$result | ConvertTo-Json -Depth 8
