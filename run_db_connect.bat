@echo off
setlocal

echo ################################################
echo # Firebird 2.0 (32-bit) Inventory Web App      #
echo ################################################

:: ==================================================
:: 1. VERIFICAR E INSTALAR GIT (Si es necesario)
:: ==================================================
git --version >nul 2>&1
if %errorlevel% equ 0 goto check_updates

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
:: 2. AUTO-ACTUALIZACION DEL CODIGO
:: ==================================================
:check_updates
echo Verificando actualizaciones en el repositorio...

:: Si no es un repositorio Git (carpeta .git no existe), inicializarlo
if not exist .git (
    echo [INFO] Inicializando repositorio para habilitar actualizaciones...
    git init >nul
    git remote add origin https://github.com/somebetto/inventariopdv.git >nul
    git fetch origin >nul
    git reset --hard origin/main >nul
) else (
    :: Intentar traer las novedades
    git fetch origin main >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Sincronizando con la ultima version de GitHub...
        git pull origin main
    ) else (
        echo [WARNING] No se pudo conectar a GitHub para actualizar.
    )
)

:: ==================================================
:: 3. VERIFICAR E INSTALAR PYTHON (32-bit)
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
:: 4. Validar Arquitectura
for /f "tokens=*" %%i in ('py -3-32 -c "import struct; print(8 * struct.calcsize('P'))" 2^>nul') do set bitness=%%i
if "%bitness%" neq "32" (
    echo [ERROR] Se requiere Python de 32 bits.
    pause
    exit /b 1
)

:: 5. Dependencias
echo Instalando dependencias (Flask + fdb)...
py -3-32 -m pip install -r requirements.txt

:: 6. Ejecucion
echo.
echo Generando codigo QR...
py -3-32 show_qr.py

echo.
echo Iniciando Servidor Web...
echo --- Accede en: http://localhost:5000
py -3-32 app.py

echo.
echo Servidor finalizado.
pause