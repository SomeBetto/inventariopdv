#!/bin/bash

echo "################################################"
echo "# Firebird Inventory Web App (Linux)           #"
echo "################################################"

# ==================================================
# 1. AUTO-ACTUALIZACION DEL CODIGO
# ==================================================
echo "Verificando actualizaciones en el repositorio..."

# Si no es un repositorio Git (carpeta .git no existe), inicializarlo
if [ ! -d ".git" ]; then
    echo "[INFO] Inicializando repositorio para habilitar actualizaciones..."
    git init >/dev/null 2>&1
    git remote add origin https://github.com/somebetto/inventariopdv.git >/dev/null 2>&1
    git fetch origin >/dev/null 2>&1
    git reset --hard origin/main >/dev/null 2>&1
else
    # Intentar traer las novedades
    if git fetch origin main >/dev/null 2>&1; then
        echo "[INFO] Sincronizando con la ultima version de GitHub..."
        git pull origin main
    else
        echo "[WARNING] No se pudo conectar a GitHub para actualizar."
    fi
fi

# ==================================================
# 2. Ejecucion
# ==================================================

echo ""
echo "Generando codigo QR..."
python3 show_qr.py

echo ""
echo "Iniciando Servidor Web..."
echo "--- Accede en: http://localhost:5000"
python3 app.py

echo ""
echo "Servidor finalizado."
read -p "Presiona Enter para continuar..."
