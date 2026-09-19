$out = 'D:\moodle\CityNexus-Tools\network-diagnostics\github-direct-test.txt'
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('timestamp=' + [DateTime]::UtcNow.ToString('o'))
$lines.Add('=== Environment Proxy ===')
foreach ($n in 'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY') {
    $e = Get-Item ('Env:' + $n) -ErrorAction SilentlyContinue
    $lines.Add($n + '=' + $(if ($null -eq $e) { 'NOT_SET' } else { 'SET' }))
}
$internet = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
$lines.Add('=== Windows Internet Settings ===')
$lines.Add('ProxyEnable=' + [string]$internet.ProxyEnable)
$lines.Add('ProxyServer=' + $(if ($internet.ProxyServer) { [string]$internet.ProxyServer } else { 'NOT_SET' }))
$lines.Add('AutoConfigURL=' + $(if ($internet.AutoConfigURL) { [string]$internet.AutoConfigURL } else { 'NOT_SET' }))
$lines.Add('=== WinHTTP ===')
$lines.Add((netsh winhttp show proxy | Out-String).Trim())
$lines.Add('=== Git Proxy ===')
foreach ($scope in @('--global','--system')) {
    foreach ($key in 'http.proxy','https.proxy') {
        $v = git config $scope --get $key 2>$null
        $lines.Add($scope + ' ' + $key + '=' + $(if ($v) { 'SET' } else { 'NOT_SET' }))
    }
}
$lines.Add('=== Relevant Processes ===')
$proc = Get-Process | Where-Object { $_.ProcessName -match 'clash|mihomo|v2ray|sing-box|singbox|nekoray|hiddify|surge' } | Select-Object ProcessName,Id,Path
$lines.Add($(if ($proc) { ($proc | Out-String).Trim() } else { 'NONE' }))
function Test-Url($u) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $err = (& curl.exe -I --connect-timeout 10 --max-time 20 -sS $u 2>&1 | Out-String).Trim()
    $code = $LASTEXITCODE
    $sw.Stop()
    $state = if ($code -eq 0) { 'PASS' } elseif ($err -match 'timed out|Timeout') { 'TIMEOUT' } elseif ($err -match 'reset') { 'CONNECTION_RESET' } elseif ($err -match 'HTTP/') { 'HTTP_STATUS' } else { 'OTHER_ERROR' }
    return "$u`t$state`tcode=$code`tseconds=$([math]::Round($sw.Elapsed.TotalSeconds,1))`terr=$err"
}
$lines.Add('=== Direct URL Tests ===')
foreach ($u in 'https://github.com','https://api.github.com','https://codeload.github.com','https://raw.githubusercontent.com') { $lines.Add((Test-Url $u)) }
$lines.Add('=== Git ls-remote ===')
$g = git ls-remote https://github.com/hiung/skills.git HEAD 2>&1
$lines.Add('exit=' + $LASTEXITCODE)
$lines.Add(($g | Out-String).Trim())
$lines | Set-Content -Encoding UTF8 $out
$lines
