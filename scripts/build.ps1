# AutomaticExcelFill — build do executável com PyInstaller
param(
  [switch]$Clean,
  [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host '=== AutomaticExcelFill - build PyInstaller ===' -ForegroundColor Cyan
Write-Host "Pasta do projeto: $ProjectRoot"

$SpecFile = Join-Path $ProjectRoot 'AutomaticExcelFill.spec'
if (-not (Test-Path $SpecFile)) {
  throw "Arquivo spec nao encontrado: $SpecFile"
}

$py = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
  $py = 'py -3'
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $py = 'python'
} else {
  throw 'Python nao encontrado. Instale Python 3.9+ ou rode scripts\install_deps.ps1 antes.'
}

Invoke-Expression "$py -c `"import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)`""
if ($LASTEXITCODE -ne 0) {
  throw 'E necessario Python 3.9 ou superior.'
}

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

$VenvActivate = Join-Path $ProjectRoot '.venv\Scripts\Activate.ps1'
if (-not (Test-Path $VenvActivate)) {
  Write-Host 'Ambiente virtual .venv nao encontrado. Criando e instalando dependencias...' -ForegroundColor Yellow
  & (Join-Path $ProjectRoot 'scripts\install_deps.ps1')
}

. $VenvActivate

if (-not $SkipInstall) {
  Write-Host 'Verificando dependencias (requirements.txt)...'
  python -m pip install -r requirements.txt --quiet
}

python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
  throw 'PyInstaller nao instalado. Rode: python -m pip install -r requirements.txt'
}

$BuildDirs = @(
  (Join-Path $ProjectRoot 'build'),
  (Join-Path $ProjectRoot 'dist')
)

if ($Clean) {
  Write-Host 'Limpando pastas build/ e dist/...' -ForegroundColor Yellow
  foreach ($dir in $BuildDirs) {
    if (Test-Path $dir) {
      try {
        Remove-Item -Recurse -Force $dir -ErrorAction Stop
      } catch {
        Write-Warning "Nao foi possivel limpar $dir (feche AutomaticExcelFill.exe se estiver aberto)."
      }
    }
  }
}

Write-Host 'Executando PyInstaller...' -ForegroundColor Cyan
python -m PyInstaller --noconfirm AutomaticExcelFill.spec
if ($LASTEXITCODE -ne 0) {
  throw 'PyInstaller falhou.'
}

function Copy-ResourceFolder {
  param(
    [string]$SourceRoot,
    [string]$FolderName,
    [string]$DestinationRoot
  )
  $source = Join-Path $SourceRoot $FolderName
  if (-not (Test-Path $source)) {
    return
  }
  $destination = Join-Path $DestinationRoot $FolderName
  Write-Host "Copiando $FolderName -> $destination"
  if (Test-Path $destination) {
    Remove-Item -Recurse -Force $destination
  }
  Copy-Item -Recurse -Force $source $destination
}

$BundleDir = Join-Path $ProjectRoot 'dist\AutomaticExcelFill'
if (-not (Test-Path $BundleDir)) {
  throw "Pasta de distribuicao nao encontrada: $BundleDir"
}

Write-Host 'Copiando pastas de recursos para a distribuicao...' -ForegroundColor Cyan
foreach ($folderName in @('theme', 'img')) {
  Copy-ResourceFolder -SourceRoot $ProjectRoot -FolderName $folderName -DestinationRoot $BundleDir
}

$ExePath = Join-Path $BundleDir 'AutomaticExcelFill.exe'
if (-not (Test-Path $ExePath)) {
  throw "Executavel nao encontrado: $ExePath"
}

$PresetsPath = Join-Path $BundleDir 'theme\presets.json'
if (-not (Test-Path $PresetsPath)) {
  throw "Arquivo obrigatorio ausente apos o build: $PresetsPath"
}

Write-Host ''
Write-Host 'Build concluido com sucesso!' -ForegroundColor Green
$sizeMb = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
Write-Host "Pasta de distribuicao: $BundleDir"
Write-Host "Executavel: $ExePath ($sizeMb MB)"
Write-Host ''
Write-Host 'Distribua a pasta inteira dist\AutomaticExcelFill (nao apenas o .exe).' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Opcoes:' -ForegroundColor DarkGray
Write-Host '  .\scripts\build.ps1 -Clean          # limpa build/dist antes'
Write-Host '  .\scripts\build.ps1 -SkipInstall    # nao reinstala requirements'
