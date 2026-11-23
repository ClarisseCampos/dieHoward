@echo off
title DieHoward TTS
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual (.venv) nao encontrado.
    echo Por favor, execute o 'install.bat' primeiro para configurar o projeto.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python app.py
pause