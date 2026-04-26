import ctypes
import os
import fdb
import sys

# --- PARCHE DE COMPATIBILIDAD (MONKEYPATCH) ---
original_cdll = ctypes.CDLL
original_windll = ctypes.WinDLL

def robust_load(original_func, name, *args, **kwargs):
    lib = original_func(name, *args, **kwargs)
    if name and ('fbclient' in name.lower() or 'gds32' in name.lower()):
        functions_to_mock = ['fb_shutdown_callback', 'fb_shutdown', 'fb_cancel_operation', 'fb_ping', 'fb_get_master_interface']
        for func_name in functions_to_mock:
            if not hasattr(lib, func_name):
                def dummy_func(*args): return 0
                mock = ctypes.WINFUNCTYPE(ctypes.c_int)(dummy_func)
                setattr(lib, func_name, mock)
    return lib

ctypes.CDLL = lambda name, *args, **kwargs: robust_load(original_cdll, name, *args, **kwargs)
ctypes.WinDLL = lambda name, *args, **kwargs: robust_load(original_windll, name, *args, **kwargs)
# ----------------------------------------------

DB_PATH = r'C:\Program Files (x86)\AbarrotesPDV\db\PDVDATA.FDB'
USER = 'SYSDBA'
PASSWORD = 'masterkey'
FB_CLIENT_LIBRARY = r'C:\Program Files (x86)\AbarrotesPDV\fbclient.dll'

def get_connection():
    return fdb.connect(
        database=DB_PATH,
        user=USER,
        password=PASSWORD,
        fb_library_name=FB_CLIENT_LIBRARY
    )

def search_inventory(query):
    try:
        with get_connection() as con:
            cur = con.cursor()
            query_sql = """
                SELECT p.CODIGO, p.DESCRIPCION, p.DINVENTARIO, d.NOMBRE 
                FROM PRODUCTOS p 
                LEFT JOIN DEPARTAMENTOS d ON p.DEPT = d.ID 
                WHERE p.CODIGO = ? OR p.CODIGO LIKE ? OR p.DESCRIPCION CONTAINING ?
                ORDER BY p.DESCRIPCION
            """
            like_pattern = f"%{query}" if query.isdigit() and len(query) > 5 else query
            cur.execute(query_sql, (query, like_pattern, query))
            
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'inventario': float(row[2]) if row[2] is not None else 0.0,
                'departamento': row[3].strip() if row[3] is not None else "Sin Depto"
            } for row in cur.fetchall()]
    except Exception as e:
        print(f"Error en search_inventory: {e}")
        return []

def get_inventory_all():
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT p.CODIGO, p.DESCRIPCION, p.DINVENTARIO, d.NOMBRE 
                FROM PRODUCTOS p 
                LEFT JOIN DEPARTAMENTOS d ON p.DEPT = d.ID 
                ORDER BY p.DESCRIPCION
            """)
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'inventario': float(row[2]) if row[2] is not None else 0.0,
                'departamento': row[3].strip() if row[3] is not None else "Sin Depto"
            } for row in cur.fetchall()]
    except Exception as e:
        print(f"Error en get_inventory_all: {e}")
        return []

def search_prices(query):
    try:
        with get_connection() as con:
            cur = con.cursor()
            query_sql = """
                SELECT p.CODIGO, p.DESCRIPCION, p.PVENTA, p.PCOSTO, d.NOMBRE 
                FROM PRODUCTOS p 
                LEFT JOIN DEPARTAMENTOS d ON p.DEPT = d.ID 
                WHERE p.CODIGO = ? OR p.CODIGO LIKE ? OR p.DESCRIPCION CONTAINING ?
                ORDER BY p.DESCRIPCION
            """
            like_pattern = f"%{query}" if query.isdigit() and len(query) > 5 else query
            cur.execute(query_sql, (query, like_pattern, query))
            
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'precio': float(row[2]) if row[2] is not None else 0.0,
                'p_costo': float(row[3]) if row[3] is not None else 0.0,
                'departamento': row[4].strip() if row[4] is not None else "Sin Depto"
            } for row in cur.fetchall()]
    except Exception as e:
        print(f"Error en search_prices: {e}")
        return []

def get_prices_all():
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT p.CODIGO, p.DESCRIPCION, p.PVENTA, p.PCOSTO, d.NOMBRE 
                FROM PRODUCTOS p 
                LEFT JOIN DEPARTAMENTOS d ON p.DEPT = d.ID 
                ORDER BY p.DESCRIPCION
            """)
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'precio': float(row[2]) if row[2] is not None else 0.0,
                'p_costo': float(row[3]) if row[3] is not None else 0.0,
                'departamento': row[4].strip() if row[4] is not None else "Sin Depto"
            } for row in cur.fetchall()]
    except Exception as e:
        print(f"Error en get_prices_all: {e}")
        return []

def update_inventory(codigo, nueva_cantidad):
    try:
        with get_connection() as con:
            cur = con.cursor()
            
            cur.execute("SELECT DINVENTARIO FROM PRODUCTOS WHERE CODIGO = ?", (codigo,))
            row = cur.fetchone()
            if not row:
                return False, "Producto no encontrado"
            
            cantidad_actual = float(row[0]) if row[0] is not None else 0.0
            
            cur.execute("UPDATE PRODUCTOS SET DINVENTARIO = ? WHERE CODIGO = ?", (nueva_cantidad, codigo))
            
            insert_history = """
                INSERT INTO HISTORIAL_INVENTARIO (USUARIO_ID, CUANDO_FUE, TIPO, HABIA, CANTIDAD, CODIGO_PRODUCTO, CAJA_ID)
                VALUES (1, CURRENT_TIMESTAMP, 'a', ?, ?, ?, 1)
            """
            cur.execute(insert_history, (cantidad_actual, nueva_cantidad, codigo))
            
            con.commit()
            return True, "Inventario actualizado exitosamente"
    except Exception as e:
        print(f"Error actualizando inventario para {codigo}: {e}")
        return False, str(e)

def update_prices(codigo, p_venta, p_costo):
    try:
        with get_connection() as con:
            cur = con.cursor()
            
            cur.execute("SELECT CODIGO FROM PRODUCTOS WHERE CODIGO = ?", (codigo,))
            if not cur.fetchone():
                return False, "Producto no encontrado"
            
            # Use safe updates to avoid issues if any parameter is None, though usually handled by validation in app.py
            if p_venta is not None and p_costo is not None:
                cur.execute("UPDATE PRODUCTOS SET PVENTA = ?, PCOSTO = ? WHERE CODIGO = ?", (p_venta, p_costo, codigo))
            elif p_venta is not None:
                cur.execute("UPDATE PRODUCTOS SET PVENTA = ? WHERE CODIGO = ?", (p_venta, codigo))
            elif p_costo is not None:
                cur.execute("UPDATE PRODUCTOS SET PCOSTO = ? WHERE CODIGO = ?", (p_costo, codigo))

            con.commit()
            return True, "Precios actualizados exitosamente"
    except Exception as e:
        print(f"Error actualizando precios para {codigo}: {e}")
        return False, str(e)
