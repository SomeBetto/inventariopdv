@echo off
setlocal

echo ################################################
echo # Firebird 2.0 (32-bit) Inventory Web App     #
echo ################################################

:: 1. Check for 32-bit Python via the launcher
echo Checking for Python 32-bit (via py -3-32)...
py -3-32 --version >nul 2>&1
if %errorlevel% equ 0 goto check_bitness

echo [INFO] Python 32-bit not found. Starting automatic installation...

set PYTHON_URL="https://www.python.org/ftp/python/3.12.2/python-3.12.2.exe"
set INSTALLER="python_installer_32.exe"

echo Downloading Python 3.12.2 (32-bit) installer...
curl -L -o %INSTALLER% %PYTHON_URL%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download Python. Please check your internet connection.
    pause
    exit /b 1
)

echo Installing Python silently (requires Administrator privileges)...
start /wait "" %INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=1 TargetDir="C:\Python312-32"

if %errorlevel% neq 0 (
    echo [ERROR] Installation failed. Error code: %errorlevel%
    if exist %INSTALLER% del %INSTALLER%
    pause
    exit /b 1
)

echo [OK] Python 32-bit installed successfully.
if exist %INSTALLER% del %INSTALLER%
timeout /t 3 /nobreak >nul

:check_bitness
:: 2. Verify bitness
for /f "tokens=*" %%i in ('py -3-32 -c "import struct; print(8 * struct.calcsize('P'))" 2^>nul') do set bitness=%%i
if "%bitness%" neq "32" (
    echo [ERROR] Se requiere Python de 32 bits. Reinicie la terminal.
    pause
    exit /b 1
)

:: 3. Install dependencies
echo Instalando dependencias (Flask + fdb)...
py -3-32 -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] No se pudieron instalar las dependencias. Verifique su conexión.
)

:: 4. Show QR Code
echo.
echo Generando codigo QR para conexion movil...
py -3-32 show_qr.py

:: 5. Run the Flask App
echo.
echo Iniciando Servidor Web de Inventario...
echo --- Accede en: http://localhost:5000
echo ------------------------------------------------
py -3-32 app.py

echo.
echo Servidor finalizado.
pause
