$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$HostName = $env:JIANYING_WEB_HOST
if (-not $HostName) {
    $HostName = "0.0.0.0"
}

$Port = $env:JIANYING_WEB_PORT
if (-not $Port) {
    $Port = "8765"
}

& $Python -B -m webui --host $HostName --port $Port --open
