@echo off
setlocal

echo ################################################
echo # Firebird 2.0 (32-bit) Inventory Web App      #
echo ################################################

:: ==================================================
:: 1. AUTO-ACTUALIZACION DEL CODIGO
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
:: 2. Ejecucion
:: ==================================================

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