@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHONW_EXE=%~dp0.venv\Scripts\pythonw.exe"
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if exist "%PYTHONW_EXE%" (
    set "RUNNER=%PYTHONW_EXE%"
) else (
    set "RUNNER=%PYTHON_EXE%"
)

if not exist "%RUNNER%" (
    echo Ambiente virtuale non trovato.
    echo Esegui prima setup.bat e scegli l'installazione.
    pause
    exit /b 1
)

if not exist ".env" if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
)

start "" "%RUNNER%" main.py
exit /b 0
