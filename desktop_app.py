import os
import sys
import time
import threading
import urllib.request
import subprocess

# Asegurar compatibilidad cuando se ejecuta con pythonw (sin consola)
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')

# Configurar ID de modelo de aplicación para que Windows muestre el icono en la barra de tareas
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('com.abarrotequintero.inventariopdv')
    except Exception:
        pass

from app import app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, 'logo.ico')
APP_PORT = 5000
SERVER_URL = f"http://127.0.0.1:{APP_PORT}/desktop"
HEALTH_CHECK_URL = f"http://127.0.0.1:{APP_PORT}/health"

def run_flask():
    """Inicia el servidor Flask en segundo plano escuchando en 0.0.0.0 para admitir también conexiones móviles."""
    app.run(host='0.0.0.0', port=APP_PORT, debug=False, use_reloader=False)

def wait_for_server(timeout=10):
    """Espera a que el servidor Flask responda antes de abrir la ventana de escritorio."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(HEALTH_CHECK_URL, timeout=1) as resp:
                if resp.status in (200, 302, 401):
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def open_desktop_window():
    """Abre la aplicación en una ventana de escritorio nativa mostrando el código QR para el celular."""
    # Intentar con pywebview para ventana nativa dedicada
    try:
        import webview
        print("[INFO] Iniciando ventana nativa de escritorio con pywebview...")
        window = webview.create_window(
            title='Inventario PDV - Conectar Celular',
            url=SERVER_URL,
            width=500,
            height=720,
            min_size=(440, 620),
            resizable=True,
            text_select=True,
            background_color='#030712'
        )
        if os.path.exists(ICON_PATH):
            webview.start(icon=ICON_PATH)
        else:
            webview.start()
        print("[INFO] Ventana de escritorio cerrada.")
        return
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo iniciar con pywebview ({e}). Iniciando modo ventana dedicada...")

    # Fallback: Abrir en ventana de aplicación independiente (Edge / Chrome App Mode sin barra de URLs)
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        "msedge"
    ]
    for edge in edge_paths:
        try:
            p = subprocess.Popen([edge, f"--app={SERVER_URL}", "--window-size=500,720"])
            p.wait()
            return
        except Exception:
            continue

    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        "chrome"
    ]
    for chrome in chrome_paths:
        try:
            p = subprocess.Popen([chrome, f"--app={SERVER_URL}", "--window-size=500,720"])
            p.wait()
            return
        except Exception:
            continue

    # Último recurso: navegador por defecto
    import webbrowser
    webbrowser.open(SERVER_URL)

if __name__ == '__main__':
    print("=" * 55)
    print("  INVENTARIO PDV - MODO ESCRITORIO")
    print("=" * 55)
    print(f"[INFO] Servidor backend iniciando en {SERVER_URL}...")

    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()

    if wait_for_server():
        print("[OK] Servidor listo. Abriendo interfaz de escritorio...")
        open_desktop_window()
    else:
        print("[ERROR] El servidor no respondió a tiempo.")
        sys.exit(1)
