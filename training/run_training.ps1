$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Py = Join-Path $Root ".tools\python311\python.exe"
if (-not (Test-Path $Py)) { throw "Portable Python not found at $Py" }

& $Py -m pip install -q -r (Join-Path $Root "training\requirements.txt")

Write-Host "=== Prepare datasets ==="
& $Py (Join-Path $Root "training\prepare_datasets.py")

Write-Host "=== Train normativity ==="
& $Py (Join-Path $Root "training\train_normativity.py")

Write-Host "=== Train logic ==="
& $Py (Join-Path $Root "training\train_logic.py")

Write-Host "=== Done ==="
