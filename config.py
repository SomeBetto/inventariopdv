import os
import sys

# Directorio base del proyecto (usar directorio del ejecutable si está congelado como exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuración de Base de Datos Firebird
DB_PATH = os.environ.get('PDV_DB_PATH', r'C:\Program Files (x86)\AbarrotesPDV\db\PDVDATA.FDB')
DB_USER = os.environ.get('PDV_DB_USER', 'SYSDBA')
DB_PASSWORD = os.environ.get('PDV_DB_PASSWORD', 'masterkey')
FB_CLIENT_LIBRARY = os.environ.get('PDV_FB_CLIENT', r'C:\Program Files (x86)\AbarrotesPDV\fbclient.dll')

# Configuración del Servidor Flask
SECRET_KEY = os.environ.get('PDV_SECRET_KEY', 'inventario_pdv_secret_key_123')
APP_HOST = os.environ.get('PDV_HOST', '0.0.0.0')
APP_PORT = int(os.environ.get('PDV_PORT', 5000))
DEBUG = os.environ.get('PDV_DEBUG', 'False').lower() in ('true', '1')

# Configuración de Logs y Auditoría
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

APP_LOG_PATH = os.path.join(LOG_DIR, 'app.log')
EVENTS_DB_PATH = os.path.join(LOG_DIR, 'events.db')

# Modo de Acceso Abierto (Sin pantalla de login obligatoria)
OPEN_ACCESS_MODE = True
DEFAULT_USER_ID = 1
DEFAULT_USER_NAME = 'Admin'
