$ErrorActionPreference = "Stop"

Write-Host "=== AutomaticExcelFill - instalacao de dependencias ===" -ForegroundColor Cyan

$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
  $py = "py -3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $py = "python"
} else {
  throw "Python nao encontrado. Instale Python 3.9+ em https://www.python.org/downloads/"
}

$version = Invoke-Expression "$py -c `"import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')`""
Write-Host "Python detectado: $version"

Invoke-Expression "$py -c `"import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)`""
if ($LASTEXITCODE -ne 0) {
  throw "E necessario Python 3.9 ou superior."
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path ".venv")) {
  Write-Host "Criando ambiente virtual .venv ..."
  Invoke-Expression "$py -m venv .venv"
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

Write-Host ""
Write-Host "OK! Para executar:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python main.py"
