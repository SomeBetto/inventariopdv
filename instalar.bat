@echo off
setlocal EnableDelayedExpansion

:: ===================================================
:: SOLICITAR PRIVILEGIOS DE ADMINISTRADOR
:: ===================================================
REM Verificar si el script ya tiene privilegios de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Solicitando privilegios de administrador...
    REM Crear un script VBS temporal para reiniciar el batch como admin
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0""", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /b
)

echo ===================================================
echo INSTALADOR Y CONFIGURADOR DE ACCESOS Y PERMISOS
echo ===================================================
echo.

:: ==================================================
:: 1. VERIFICAR E INSTALAR GIT (Si es necesario)
:: ==================================================
git --version >nul 2>&1
if %errorlevel% equ 0 goto python_check

echo [INFO] Git no esta instalado. Iniciando instalacion automatica...

set GIT_URL="https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-32-bit.exe"
set GIT_INSTALLER="git_installer.exe"

echo Descargando Git for Windows (32-bit)...
curl -L -o %GIT_INSTALLER% %GIT_URL%
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la descarga de Git. Verifique su conexion.
    pause
    exit /b 1
)

echo Instalando Git silenciosamente...
start /wait "" %GIT_INSTALLER% /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS

if %errorlevel% neq 0 (
    echo [ERROR] La instalacion de Git fallo. Codigo: %errorlevel%
    if exist %GIT_INSTALLER% del %GIT_INSTALLER%
    pause
    exit /b 1
)

echo [OK] Git instalado con exito.
if exist %GIT_INSTALLER% del %GIT_INSTALLER%
:: Refrescar el PATH para que el comando 'git' sea reconocido de inmediato
set "PATH=%PATH%;C:\Program Files\Git\cmd"

:: ==================================================
:: 2. VERIFICAR E INSTALAR PYTHON (32-bit)
:: ==================================================
:python_check
echo Checking for Python 32-bit (via py -3-32)...
py -3-32 --version >nul 2>&1
if %errorlevel% equ 0 goto check_bitness

echo [INFO] Python 32-bit no encontrado. Instalando...
set PYTHON_URL="https://www.python.org/ftp/python/3.12.2/python-3.12.2.exe"
set INSTALLER="python_installer_32.exe"

echo Downloading Python 3.12.2 (32-bit)...
curl -L -o %INSTALLER% %PYTHON_URL%
if %errorlevel% neq 0 (
    echo [ERROR] Error al descargar Python.
    pause
    exit /b 1
)

echo Instalando Python (C:\Python312-32)...
start /wait "" %INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1 TargetDir="C:\Python312-32"

if %errorlevel% neq 0 (
    echo [ERROR] Instalacion de Python fallida.
    if exist %INSTALLER% del %INSTALLER%
    pause
    exit /b 1
)

echo [OK] Python instalado.
if exist %INSTALLER% del %INSTALLER%
timeout /t 2 /nobreak >nul

:check_bitness
:: 3. Validar Arquitectura
for /f "tokens=*" %%i in ('py -3-32 -c "import struct; print(8 * struct.calcsize('P'))" 2^>nul') do set bitness=%%i
if "%bitness%" neq "32" (
    echo [ERROR] Se requiere Python de 32 bits.
    pause
    exit /b 1
)

:: 4. Dependencias
echo Instalando dependencias (Flask + fdb)...
py -3-32 -m pip install -r requirements.txt
echo.

:: 1. Dar permisos a Everyone en la carpeta de AbarrotesPDV (para la DB)
set "PDV_FOLDER=C:\Program Files (x86)\AbarrotesPDV"
echo Configurando permisos para la carpeta de la Base de Datos...
echo Ruta: "%PDV_FOLDER%"
if exist "%PDV_FOLDER%" (
    icacls "%PDV_FOLDER%" /grant "Everyone:(OI)(CI)F" /T
    echo Permisos asignados correctamente.
) else (
    echo [ADVERTENCIA] No se encontro la carpeta "%PDV_FOLDER%"
    echo Es posible que la base de datos este en otra ubicacion.
)
echo.

:: 2. Crear acceso directo en el escritorio
echo Creando acceso directo en el escritorio...

:: Definir rutas
set "TARGET_BAT=%~dp0run_db_connect.bat"
set "TARGET_ICON=%~dp0logo.ico"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\Inventario PDV.lnk"
set "WORKING_DIR=%~dp0"

:: Script temporal de VBScript para crear el acceso directo de forma nativa
set "VBS_SCRIPT=%temp%\create_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sLinkFile = "%SHORTCUT_PATH%" >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%TARGET_BAT%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%WORKING_DIR%" >> "%VBS_SCRIPT%"
echo oLink.IconLocation = "%TARGET_ICON%" >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

:: Ejecutar el script VBScript
cscript //nologo "%VBS_SCRIPT%"

:: Limpiar script temporal
del "%VBS_SCRIPT%"

echo Acceso directo creado en el escritorio con el logo.ico.
echo.
echo ===================================================
echo Instalacion completada exitosamente.
echo ===================================================
pause
