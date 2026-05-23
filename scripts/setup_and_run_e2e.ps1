# Portable Python + local E2E (SQLite backend, heuristic AI)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Tools = Join-Path $Root ".tools"
$PyDir = Join-Path $Tools "python311"
$PyZip = Join-Path $Tools "python-3.11.9-embed-amd64.zip"
$PyUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
$GetPip = Join-Path $Tools "get-pip.py"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$DbPath = Join-Path $Root "e2e.db"
$DbUrl = "sqlite:///" + ($DbPath -replace "\\", "/")

function Ensure-Python {
    if (Test-Path (Join-Path $PyDir "python.exe")) { return (Join-Path $PyDir "python.exe") }
    New-Item -ItemType Directory -Force -Path $Tools | Out-Null
    if (-not (Test-Path $PyZip)) {
        Write-Host "Downloading portable Python 3.11..."
        curl.exe -L -o $PyZip $PyUrl
    }
    if (Test-Path $PyDir) { Remove-Item $PyDir -Recurse -Force }
    Expand-Archive -Path $PyZip -DestinationPath $PyDir -Force
    $pth = Get-ChildItem $PyDir -Filter "python*._pth" | Select-Object -First 1
    if ($pth) {
        (Get-Content $pth.FullName) -replace "#import site", "import site" | Set-Content $pth.FullName
    }
    if (-not (Test-Path $GetPip)) {
        curl.exe -L -o $GetPip $GetPipUrl
    }
    $pyExe = Join-Path $PyDir "python.exe"
    & $pyExe $GetPip --no-warn-script-location 2>&1 | Out-Null
    return $pyExe
}

$python = Ensure-Python
if (-not (Test-Path $python)) { throw "Python not found at $python" }
Write-Host "Python: $python"

& $python -m pip install -q -r (Join-Path $Root "backend\requirements-dev.txt")
& $python -m pip install -q -r (Join-Path $Root "ai-service\requirements-dev.txt")

$backendLog = Join-Path $Root ".tools\backend.log"
$aiLog = Join-Path $Root ".tools\ai.log"
New-Item -ItemType Directory -Force -Path (Join-Path $Root ".tools") | Out-Null

$beCmd = "set DATABASE_URL=$DbUrl&& set SECRET_KEY=e2e-secret&& set AI_SERVICE_URL=http://127.0.0.1:8001&& set CORS_ORIGINS=http://localhost:3000&& `"$python`" `"$($Root)\backend\run_server.py`" > `"$backendLog`" 2>&1"
$aiCmd = "set MODEL_PATH=$($Root)\models\nonexistent.gguf&& `"$python`" `"$($Root)\ai-service\run_server.py`" > `"$aiLog`" 2>&1"

$beProc = Start-Process cmd.exe -ArgumentList "/c", $beCmd -PassThru -WindowStyle Hidden
$aiProc = Start-Process cmd.exe -ArgumentList "/c", $aiCmd -PassThru -WindowStyle Hidden

Write-Host "Waiting for services (15s)..."
Start-Sleep -Seconds 15

Push-Location $Root
node scripts\e2e_test.mjs
$code = $LASTEXITCODE
Pop-Location

Stop-Process -Id $beProc.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $aiProc.Id -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*\.tools\python311*" } | Stop-Process -Force -ErrorAction SilentlyContinue

if ($code -ne 0) {
    Write-Host "--- backend log ---"
    Get-Content $backendLog -ErrorAction SilentlyContinue | Select-Object -Last 30
    Write-Host "--- ai log ---"
    Get-Content $aiLog -ErrorAction SilentlyContinue | Select-Object -Last 30
}
exit $code
