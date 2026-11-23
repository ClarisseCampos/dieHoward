@echo off
title Instalador DieHoward (Windows)
cd /d "%~dp0"

echo ==========================================
echo   Instalando DieHoward Audiobook Pipeline
echo ==========================================
echo.

:: Tenta usar o Python 3.12 especificamente (via launcher py)
py -3.12 -V >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3.12"
    echo [OK] Python 3.12 detectado.
) else (
    set "PYTHON_CMD=python"
    echo [Aviso] Tentando usar o Python padrao do sistema...
)

if not exist ".venv" (
    echo [1/3] Criando ambiente virtual...
    %PYTHON_CMD% -m venv .venv
) else (
    echo [1/3] Ambiente virtual ja existe. Pulando criacao.
)

echo [2/3] Instalando dependencias...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Garantindo estrutura de pastas...
if not exist "data\input" mkdir "data\input"
if not exist "data\output" mkdir "data\output"
if not exist "data\temp" mkdir "data\temp"
if not exist "models\kokoro" mkdir "models\kokoro"
if not exist "models\piper" mkdir "models\piper"

echo.
echo ==========================================
echo   Instalacao concluida com sucesso!
echo ==========================================
echo Para iniciar, de um duplo clique no arquivo 'diehoward.bat'
echo.
pause