@echo off
setlocal
echo ===================================================
echo COMPILADOR DE INVENTARIO PDV (Generador de bin/exe)
echo ===================================================
echo.

if exist "venv\Scripts\pyinstaller.exe" (
    set "PYI=venv\Scripts\pyinstaller.exe"
) else (
    echo [INFO] Instalando PyInstaller en el entorno virtual de 32 bits...
    py -3-32 -m pip install pyinstaller
    set "PYI=py -3-32 -m PyInstaller"
)

echo [INFO] Compilando Inventario PDV a bin\InventarioPDV.exe...
%PYI% --distpath bin --workpath build --clean -y InventarioPDV.spec

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La compilacion ha fallado con codigo %errorlevel%.
    pause
    exit /b %errorlevel%
)

if not exist "bin\logo.ico" (
    copy logo.ico bin\logo.ico >nul
)

echo.
echo ===================================================
echo [EXITO] Compilacion completada con exito.
echo Ejecutable generado en: %~dp0bin\InventarioPDV.exe
echo ===================================================
pause
