import os
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import config

# Configuración del Logger de Archivo Estándar
logger = logging.getLogger('inventariopdv')
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Handler con rotación: 5 MB por archivo, máximo 3 archivos de respaldo
    file_handler = RotatingFileHandler(
        config.APP_LOG_PATH, 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3, 
        encoding='utf-8'
    )
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para consola sólo si está en modo DEBUG
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
    logger.addHandler(console_handler)

def get_logger(name='app'):
    """Retorna un logger con el namespace del proyecto."""
    return logging.getLogger(f'inventariopdv.{name}')

# --- Base de Datos SQLite para Historial de Eventos del Aplicativo ---
def _get_db():
    con = sqlite3.connect(config.EVENTS_DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con

def init_event_db():
    """Inicializa la tabla de eventos si no existe."""
    try:
        with _get_db() as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_id TEXT DEFAULT '',
                    entity_name TEXT DEFAULT '',
                    details TEXT DEFAULT '',
                    user_name TEXT DEFAULT 'Directo',
                    ip_address TEXT DEFAULT ''
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_event_cat ON event_log(category)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_event_time ON event_log(timestamp DESC)")
            con.commit()
    except Exception as e:
        logger.error(f"Error inicializando base de datos de eventos: {e}")

# Inicializar al importar
init_event_db()

def log_event(category, action, entity_id='', entity_name='', details='', user_name='Directo', ip_address=''):
    """
    Registra un evento estructurado en SQLite y en el log de archivo.
    Categorías recomendadas: 'INVENTARIO', 'PRECIOS', 'CATALOGO', 'CLIENTES', 'USUARIOS', 'SISTEMA'.
    """
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with _get_db() as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO event_log (timestamp, category, action, entity_id, entity_name, details, user_name, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_str, category.upper(), action, str(entity_id), str(entity_name), str(details), str(user_name), str(ip_address)))
            con.commit()
        
        logger.info(f"[{category.upper()}] {action} | ID: {entity_id} | {details} | Usuario: {user_name} | IP: {ip_address}")
        return True
    except Exception as e:
        logger.error(f"Error registrando evento: {e}")
        return False

def get_events(category=None, search=None, limit=100, offset=0):
    """
    Consulta el historial de eventos con soporte para filtros por categoría, búsqueda y paginación.
    """
    try:
        with _get_db() as con:
            cur = con.cursor()
            query = "SELECT id, timestamp, category, action, entity_id, entity_name, details, user_name, ip_address FROM event_log WHERE 1=1"
            params = []

            if category and category.strip() and category.upper() != 'TODOS':
                query += " AND category = ?"
                params.append(category.strip().upper())

            if search and search.strip():
                query += " AND (entity_id LIKE ? OR entity_name LIKE ? OR details LIKE ? OR action LIKE ?)"
                term = f"%{search.strip()}%"
                params.extend([term, term, term, term])

            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cur.execute(query, params)
            rows = cur.fetchall()

            events = [{
                'id': r['id'],
                'timestamp': r['timestamp'],
                'category': r['category'],
                'action': r['action'],
                'entity_id': r['entity_id'],
                'entity_name': r['entity_name'],
                'details': r['details'],
                'user_name': r['user_name'],
                'ip_address': r['ip_address']
            } for r in rows]

            # Contar total con los mismos filtros
            count_query = "SELECT COUNT(*) as total FROM event_log WHERE 1=1"
            count_params = []
            if category and category.strip() and category.upper() != 'TODOS':
                count_query += " AND category = ?"
                count_params.append(category.strip().upper())
            if search and search.strip():
                count_query += " AND (entity_id LIKE ? OR entity_name LIKE ? OR details LIKE ? OR action LIKE ?)"
                term = f"%{search.strip()}%"
                count_params.extend([term, term, term, term])

            cur.execute(count_query, count_params)
            total = cur.fetchone()['total']

            return {
                'total': total,
                'events': events,
                'limit': limit,
                'offset': offset
            }
    except Exception as e:
        logger.error(f"Error consultando eventos: {e}")
        return {'total': 0, 'events': [], 'limit': limit, 'offset': offset}

def get_event_summary():
    """
    Retorna resumen estadístico de eventos (total general, total hoy, y desglose por categoría).
    """
    try:
        today_prefix = datetime.now().strftime('%Y-%m-%d') + '%'
        with _get_db() as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) as total FROM event_log")
            total_events = cur.fetchone()['total']

            cur.execute("SELECT COUNT(*) as today FROM event_log WHERE timestamp LIKE ?", (today_prefix,))
            today_events = cur.fetchone()['today']

            cur.execute("""
                SELECT category, COUNT(*) as count 
                FROM event_log 
                WHERE timestamp LIKE ? 
                GROUP BY category
            """, (today_prefix,))
            by_category = {r['category']: r['count'] for r in cur.fetchall()}

            return {
                'total_events': total_events,
                'today_events': today_events,
                'by_category': by_category
            }
    except Exception as e:
        logger.error(f"Error calculando resumen de eventos: {e}")
        return {'total_events': 0, 'today_events': 0, 'by_category': {}}
