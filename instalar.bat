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
