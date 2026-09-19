$out = 'D:\moodle\CityNexus-Tools\smoke\qa-poc\hiung-qa-poc-result.json'
$scripts = @('check_cross.py','verify_topology.py','verify_label_spacing.py')
$repo = 'D:\moodle\CityNexus-Tools\external\hiung-visio'
$result = [ordered]@{status='NOT_RUN';reason='hiung/skills codeload returned 404; scripts unavailable';valid='NOT_RUN';invalid='NOT_RUN';scripts=$scripts}
$result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $out
$result | ConvertTo-Json -Depth 5
