@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_DIR=%~dp0.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"
set "INSTALL_TARGET=-e ."
set "FAIL_MESSAGE="

if /I "%~1"=="install" goto :install
if /I "%~1"=="uninstall" goto :uninstall
if /I "%~1"=="factory-reset" goto :factory_reset

:main_menu
cls
echo ==========================================
echo           Gestionale Filtri
echo              setup.bat
echo ==========================================
echo.
echo   [1] Installa / aggiorna l'app
echo   [2] Disinstalla il pacchetto dalla .venv
echo   [3] Factory reset repo
echo   [4] Esci
echo.
set /p choice="Scegli un'opzione [1-4]: "

if "%choice%"=="1" goto :install
if "%choice%"=="2" goto :uninstall
if "%choice%"=="3" goto :factory_reset
if "%choice%"=="4" goto :end
goto :main_menu

:install
cls
if not "%~2"=="" (
    set "EXTRAS_INPUT=%~2"
    goto :resolve_extras
)

echo ==========================================
echo         Selezione profili installazione
echo ==========================================
echo.
echo Seleziona i profili da installare.
echo.
echo   [1] standard
echo   [2] dev
echo   [3] audit
echo   [4] security
echo   [5] quality
echo   [8] all
echo.
echo   [6] Indietro
echo   [7] Esci
echo.
echo Inserisci uno o piu numeri separati da virgola.
echo Esempi: 1   2,3   2,3,4,5   8
echo.
set /p EXTRAS_INPUT="Profili da installare [1,6,7,8]: "
if "%EXTRAS_INPUT%"=="" set "EXTRAS_INPUT=1"
if "%EXTRAS_INPUT%"=="6" goto :main_menu
if "%EXTRAS_INPUT%"=="7" goto :end
if "%EXTRAS_INPUT%"=="8" set "EXTRAS_INPUT=2,3,4,5"

:resolve_extras
call :build_install_target "%EXTRAS_INPUT%"
if errorlevel 1 (
    echo.
    pause
    goto :install
)

cls
echo ==========================================
echo            Installazione in corso
echo ==========================================
echo.
echo [1/5] Verifica Python...
where py >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python non trovato nel PATH.
        echo Installa Python 3.10+ e riprova.
        goto :fail
    )
    set "PY_CMD=python"
) else (
    set "PY_CMD=py -3"
)

if not exist "%VENV_DIR%" (
    echo [2/5] Creo ambiente virtuale...
    call %PY_CMD% -m venv ".venv"
    if errorlevel 1 goto :fail
) else (
    echo [2/5] Ambiente virtuale gia presente.
)

if not exist "%PYTHON_EXE%" (
    echo Python della .venv non trovato.
    goto :fail
)

echo [3/5] Aggiorno pip...
call "%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo Avviso: aggiornamento pip non riuscito, continuo con la versione corrente.
)

echo [4/5] Installo il progetto (%INSTALL_TARGET%)...
call "%PIP_EXE%" install "%INSTALL_TARGET%"
if errorlevel 1 goto :fail

if not exist ".env" (
    if exist ".env.example" (
        echo [5/5] Creo .env da .env.example...
        copy /Y ".env.example" ".env" >nul
    ) else (
        echo [5/5] Nessun .env.example trovato, salto copia .env.
    )
) else (
    echo [5/5] File .env gia presente.
)

echo.
echo Installazione completata.
echo Per avviare l'app usa: start.bat
goto :success

:uninstall
cls
echo ==========================================
echo             Disinstallazione
echo ==========================================
echo.
if not exist "%PIP_EXE%" (
    echo Nessuna .venv trovata. Niente da disinstallare.
    goto :success
)

echo Disinstallo il pacchetto "gestionale-filtri" dalla .venv...
call "%PIP_EXE%" uninstall -y gestionale-filtri
if errorlevel 1 goto :fail

echo.
echo Disinstallazione completata.
echo La cartella .venv non e stata rimossa.
goto :success

:factory_reset
cls
echo ==========================================
echo              Factory reset repo
echo ==========================================
echo.
echo Questa operazione riportera il repository allo stato del commit corrente.
echo Verranno eliminati:
echo   - modifiche ai file tracciati
echo   - file non tracciati
echo   - file e cartelle ignorati da .gitignore
echo.
echo Esempi tipici rimossi: .venv, .env, cache, log, database locali.
echo.
choice /C SN /M "Continuare con il factory reset? [S/N]"
if errorlevel 2 goto :main_menu

echo.
choice /C SN /M "Conferma finale: eliminare tutto e ripartire da repo pulito? [S/N]"
if errorlevel 2 goto :main_menu

where git >nul 2>nul
if errorlevel 1 (
    set "FAIL_MESSAGE=Git non trovato nel PATH."
    goto :fail
)

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
    set "FAIL_MESSAGE=Questa cartella non sembra essere un repository Git valido."
    goto :fail
)

cls
echo ==========================================
echo            Factory reset in corso
echo ==========================================
echo.
echo [1/2] Ripristino file tracciati...
git reset --hard HEAD
if errorlevel 1 (
    set "FAIL_MESSAGE=git reset --hard HEAD non riuscito."
    goto :fail
)

echo [2/2] Rimozione file non tracciati e ignorati...
git clean -ffdx
if errorlevel 1 (
    set "FAIL_MESSAGE=git clean -ffdx non riuscito."
    goto :fail
)

echo.
echo Factory reset completato.
echo Il repository ora e allineato al commit corrente.
goto :success

:fail
echo.
echo ==========================================
echo                  Errore
echo ==========================================
echo.
if not "%FAIL_MESSAGE%"=="" echo %FAIL_MESSAGE%
echo Operazione non completata.
echo.
pause
exit /b 1

:success
set "FAIL_MESSAGE="
echo.
echo ==========================================
echo                 Completato
echo ==========================================
echo.
pause
exit /b 0

:build_install_target
set "RAW=%~1"
set "RAW=%RAW: =%"
set "RAW=%RAW:;=,%"
set "RAW=%RAW:+=,%"
set "RAW=%RAW:,= %"

if "%RAW%"=="" set "RAW=1"

set "WANT_STANDARD="
set "WANT_DEV="
set "WANT_AUDIT="
set "WANT_SECURITY="
set "WANT_QUALITY="
set "EXTRAS_LIST="

for %%T in (%RAW%) do (
    if "%%~T"=="1" (
        set "WANT_STANDARD=1"
    ) else if "%%~T"=="2" (
        set "WANT_DEV=1"
    ) else if "%%~T"=="3" (
        set "WANT_AUDIT=1"
    ) else if "%%~T"=="4" (
        set "WANT_SECURITY=1"
    ) else if "%%~T"=="5" (
        set "WANT_QUALITY=1"
    ) else (
        goto :invalid_install_profile
    )
)

if defined WANT_STANDARD (
    if defined WANT_DEV goto :invalid_install_profile
    if defined WANT_AUDIT goto :invalid_install_profile
    if defined WANT_SECURITY goto :invalid_install_profile
    if defined WANT_QUALITY goto :invalid_install_profile
    set "INSTALL_TARGET=-e ."
    exit /b 0
)

if defined WANT_DEV call :append_extra dev
if defined WANT_AUDIT call :append_extra audit
if defined WANT_SECURITY call :append_extra security
if defined WANT_QUALITY call :append_extra quality

if not defined EXTRAS_LIST goto :invalid_install_profile

set "INSTALL_TARGET=-e .[%EXTRAS_LIST%]"
exit /b 0

:append_extra
if defined EXTRAS_LIST (
    set "EXTRAS_LIST=%EXTRAS_LIST%,%~1"
) else (
    set "EXTRAS_LIST=%~1"
)
exit /b 0

:invalid_install_profile
cls
echo ==========================================
echo            Profilo non valido
echo ==========================================
echo.
echo Profilo non valido: %RAW%
echo.
echo Valori ammessi:
echo   1 = standard
echo   2 = dev
echo   3 = audit
echo   4 = security
echo   5 = quality
echo   6 = indietro
echo   7 = esci
echo   8 = all
echo.
echo Esempi validi:
echo   1
echo   2,3
echo   2,4
echo   2,3,4
echo   2,3,4,5
echo   8
exit /b 1

:end
cls
echo Operazione annullata.
exit /b 0
