@echo off
setlocal enabledelayedexpansion

echo === AutomaticExcelFill - instalacao de dependencias ===

where py >nul 2>&1
if %errorlevel%==0 (
  set PY_CMD=py -3
) else (
  set PY_CMD=python
)

for /f "delims=" %%i in ('%PY_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VER=%%i
echo Python detectado: %PY_VER%

%PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if errorlevel 1 (
  echo ERRO: e necessario Python 3.9 ou superior.
  echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
  exit /b 1
)

chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if not exist .venv (
  echo Criando ambiente virtual .venv ...
  %PY_CMD% -m venv .venv
)

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo Falha ao atualizar pip/setuptools/wheel.
  exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Se aparecer erro de encoding, confira:
  echo   1. Voce esta usando Python 3.9+ ^(nao Python 2^)
  echo   2. Rode este script como administrador ou em pasta sem acentos
  echo   3. Tente: python -m pip install -r requirements.txt
  exit /b 1
)

echo.
echo OK! Para executar o app:
echo   .venv\Scripts\activate
echo   python main.py
exit /b 0
