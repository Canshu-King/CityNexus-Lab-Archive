Import-Module Visio -Force
$outDir = 'D:\moodle\CityNexus-Tools\smoke'
$path = Join-Path $outDir 'visioautomation-capability-smoke.vsdx'
$resultPath = Join-Path $outDir 'vsdx-capability-matrix.json'
$null = New-VisioApplication
$doc = New-VisioDocument
$page = Get-VisioPage -Document $doc | Select-Object -First 1
$a = New-VisioShape -Rectangle -BoundingBox ([VisioAutomation.Core.Rectangle]::new(1, 5, 3, 7))
$b = New-VisioShape -Rectangle -BoundingBox ([VisioAutomation.Core.Rectangle]::new(6, 5, 8, 7))
Set-VisioUserDefinedCell -Shape $a -Name TEST_USER -Value TEST-USER
Set-VisioCustomProperty -Shape $a -Name SpecId -Value TEST-CAPABILITY-SPEC-ID
$connector = Connect-VisioShape -From $a -To $b
Save-VisioDocument -Document $doc -Filename $path
Close-VisioDocument -Document $doc
Close-VisioApplication

$py = 'D:\moodle\CityNexus-Tools\.venv\Scripts\python.exe'
$probe = & $py -c @"
import json, zipfile
from vsdx import VisioFile
p=r'$path'
out={"reader":"vsdx 0.6.1","target":p}
try:
    with VisioFile(p) as v:
        page=v.get_page(0)
        shapes=list(page.child_shapes)
        out.update({"page_count":len(v.pages),"shape_count":len(shapes),"shape_text":all(hasattr(s,'text') for s in shapes),"child_shape_traversal":all(hasattr(s,'child_shapes') for s in shapes),"connector_count":len(page.connects),"connector_api":"PASS"})
        out["connector_source_target"]="UNSUPPORTED"
        out["master_information"]="UNSUPPORTED"
        out["user_cell_support"]="UNSUPPORTED"
        out["custom_property_support"]="UNSUPPORTED"
except Exception as e:
    out.update({"error":type(e).__name__+': '+str(e)})
print(json.dumps(out))
"@
$parsed = $probe | Select-Object -Last 1 | ConvertFrom-Json
$parsed | Add-Member -NotePropertyName glue_attempt -NotePropertyValue 'Connect-VisioShape executed' -Force
$parsed | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $resultPath
$parsed | ConvertTo-Json -Depth 8
