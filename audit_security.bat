@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_DIR=%~dp0.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"
set "PIP_AUDIT_EXE=%VENV_DIR%\Scripts\pip-audit.exe"
set "BANDIT_EXE=%VENV_DIR%\Scripts\bandit.exe"
set "SEMGREP_EXE=%VENV_DIR%\Scripts\semgrep.exe"
set "RUFF_EXE=%VENV_DIR%\Scripts\ruff.exe"
set "MYPY_EXE=%VENV_DIR%\Scripts\mypy.exe"

set "FAILURES=0"

if /I "%~1"=="audit" goto :run_audit_only
if /I "%~1"=="security" goto :run_security_only
if /I "%~1"=="quality" goto :run_quality_only
if /I "%~1"=="all" goto :run_all
if not "%~1"=="" goto :invalid_arg

echo.
echo ==========================================
echo   Gestionale Filtri - audit_security.bat
echo ==========================================
echo.
echo 1. Esegui tutto (audit + security + quality)
echo 2. Solo audit dipendenze (pip-audit)
echo 3. Solo security codice (bandit + semgrep)
echo 4. Solo quality codice (ruff + mypy)
echo 5. Esci
echo.
set /p choice="Scegli un'opzione [1-5]: "

if "%choice%"=="1" goto :run_all
if "%choice%"=="2" goto :run_audit_only
if "%choice%"=="3" goto :run_security_only
if "%choice%"=="4" goto :run_quality_only
if "%choice%"=="5" goto :end_ok
goto :end_ok

:invalid_arg
echo Argomento non valido: %~1
echo Valori ammessi: all, audit, security, quality
goto :fail

:check_venv
if not exist "%PYTHON_EXE%" (
    echo Ambiente virtuale non trovato.
    echo Esegui prima setup.bat e scegli l'installazione.
    goto :fail
)
exit /b 0

:check_audit_tools
if not exist "%PIP_AUDIT_EXE%" (
    echo pip-audit non trovato nella .venv.
    echo Installa il profilo audit con:
    echo   setup.bat install audit
    goto :fail
)
exit /b 0

:check_security_tools
if not exist "%BANDIT_EXE%" (
    echo bandit non trovato nella .venv.
    echo Installa il profilo security con:
    echo   setup.bat install security
    goto :fail
)
if not exist "%SEMGREP_EXE%" (
    echo semgrep non trovato nella .venv.
    echo Installa il profilo security con:
    echo   setup.bat install security
    goto :fail
)
exit /b 0

:check_quality_tools
if not exist "%RUFF_EXE%" (
    echo ruff non trovato nella .venv.
    echo Installa il profilo quality con:
    echo   setup.bat install quality
    goto :fail
)
if not exist "%MYPY_EXE%" (
    echo mypy non trovato nella .venv.
    echo Installa il profilo quality con:
    echo   setup.bat install quality
    goto :fail
)
exit /b 0

:run_audit_only
call :check_venv
if errorlevel 1 goto :fail
call :check_audit_tools
if errorlevel 1 goto :fail
call :run_audit
goto :summary

:run_security_only
call :check_venv
if errorlevel 1 goto :fail
call :check_security_tools
if errorlevel 1 goto :fail
call :run_security
goto :summary

:run_quality_only
call :check_venv
if errorlevel 1 goto :fail
call :check_quality_tools
if errorlevel 1 goto :fail
call :run_quality
goto :summary

:run_all
call :check_venv
if errorlevel 1 goto :fail
call :check_audit_tools
if errorlevel 1 goto :fail
call :check_security_tools
if errorlevel 1 goto :fail
call :check_quality_tools
if errorlevel 1 goto :fail
call :run_audit
call :run_security
call :run_quality
goto :summary

:run_audit
echo.
echo ==========================================
echo   Audit dipendenze - pip-audit
echo ==========================================
echo.
call "%PIP_AUDIT_EXE%"
if errorlevel 1 (
    echo.
    echo pip-audit ha segnalato problemi o errori.
    set /a FAILURES+=1
) else (
    echo.
    echo pip-audit completato senza CVE note.
)
exit /b 0

:run_security
echo.
echo ==========================================
echo   Security codice - bandit
echo ==========================================
echo.
call "%BANDIT_EXE%" -r backend frontend main.py
if errorlevel 1 (
    echo.
    echo bandit ha segnalato problemi o errori.
    set /a FAILURES+=1
) else (
    echo.
    echo bandit completato senza segnalazioni.
)

echo.
echo ==========================================
echo   Security codice - semgrep
echo ==========================================
echo.
call "%SEMGREP_EXE%" --config=auto backend frontend main.py
if errorlevel 1 (
    echo.
    echo semgrep ha segnalato problemi o errori.
    set /a FAILURES+=1
) else (
    echo.
    echo semgrep completato senza segnalazioni.
)
exit /b 0

:run_quality
echo.
echo ==========================================
echo   Quality codice - ruff
echo ==========================================
echo.
call "%RUFF_EXE%" check .
if errorlevel 1 (
    echo.
    echo ruff ha segnalato problemi o errori.
    set /a FAILURES+=1
) else (
    echo.
    echo ruff completato senza segnalazioni.
)

echo.
echo ==========================================
echo   Quality codice - mypy
echo ==========================================
echo.
call "%MYPY_EXE%"
if errorlevel 1 (
    echo.
    echo mypy ha segnalato problemi o errori.
    set /a FAILURES+=1
) else (
    echo.
    echo mypy completato senza segnalazioni.
)
exit /b 0

:summary
echo.
echo ==========================================
if "%FAILURES%"=="0" (
    echo   Controlli completati senza errori.
) else (
    echo   Controlli completati con %FAILURES% segnalazione/i.
)
echo ==========================================
echo.
if not "%FAILURES%"=="0" goto :fail
goto :end_ok

:fail
echo.
pause
exit /b 1

:end_ok
pause
exit /b 0
