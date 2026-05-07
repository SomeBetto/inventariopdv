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
                WHERE p.CODIGO CONTAINING ? OR p.DESCRIPCION CONTAINING ?
                ORDER BY p.DESCRIPCION
            """
            print(f"--- DEBUG search_inventory ---")
            print(f"Parametro de busqueda: '{query}'")
            cur.execute(query_sql, (query, query))
            
            rows = cur.fetchall()
            print(f"Resultados encontrados ({len(rows)}):")
            for r in rows:
                print(r)
            print("------------------------------")
            
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'inventario': float(row[2]) if row[2] is not None else 0.0,
                'departamento': row[3].strip() if row[3] is not None else "Sin Depto"
            } for row in rows]
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
                WHERE p.CODIGO CONTAINING ? OR p.DESCRIPCION CONTAINING ?
                ORDER BY p.DESCRIPCION
            """
            print(f"--- DEBUG search_prices ---")
            print(f"Parametro de busqueda: '{query}'")
            cur.execute(query_sql, (query, query))
            
            rows = cur.fetchall()
            print(f"Resultados encontrados ({len(rows)}):")
            for r in rows:
                print(r)
            print("------------------------------")
            
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'precio': float(row[2]) if row[2] is not None else 0.0,
                'p_costo': float(row[3]) if row[3] is not None else 0.0,
                'departamento': row[4].strip() if row[4] is not None else "Sin Depto"
            } for row in rows]
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

def search_catalog(query):
    try:
        with get_connection() as con:
            cur = con.cursor()
            query_sql = """
                SELECT p.CODIGO, p.DESCRIPCION, d.NOMBRE 
                FROM PRODUCTOS p 
                LEFT JOIN DEPARTAMENTOS d ON p.DEPT = d.ID 
                WHERE p.CODIGO CONTAINING ? OR p.DESCRIPCION CONTAINING ?
                ORDER BY p.DESCRIPCION
            """
            cur.execute(query_sql, (query, query))
            
            rows = cur.fetchall()
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'departamento': row[2].strip() if row[2] is not None else "Sin Depto"
            } for row in rows]
    except Exception as e:
        print(f"Error en search_catalog: {e}")
        return []

def get_catalog_all():
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT p.CODIGO, p.DESCRIPCION, d.NOMBRE 
                FROM PRODUCTOS p 
                LEFT JOIN DEPARTAMENTOS d ON p.DEPT = d.ID 
                ORDER BY p.DESCRIPCION
            """)
            return [{
                'codigo': row[0].strip(),
                'descripcion': row[1].strip(),
                'departamento': row[2].strip() if row[2] is not None else "Sin Depto"
            } for row in cur.fetchall()]
    except Exception as e:
        print(f"Error en get_catalog_all: {e}")
        return []

def update_description(codigo, nueva_descripcion):
    try:
        with get_connection() as con:
            cur = con.cursor()
            
            cur.execute("SELECT CODIGO FROM PRODUCTOS WHERE CODIGO = ?", (codigo,))
            if not cur.fetchone():
                return False, "Producto no encontrado"
            
            if nueva_descripcion is not None and nueva_descripcion.strip() != "":
                cur.execute("UPDATE PRODUCTOS SET DESCRIPCION = ? WHERE CODIGO = ?", (nueva_descripcion.strip(), codigo))
                con.commit()
                return True, "Descripción actualizada exitosamente"
            else:
                return False, "La descripción no puede estar vacía"
    except Exception as e:
        print(f"Error actualizando descripción para {codigo}: {e}")
        return False, str(e)

def get_sales_report(time_range, group_by, depto_filter=None):
    from datetime import datetime, timedelta
    
    now = datetime.now()
    if time_range == 'day':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif time_range == 'week':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        end = start + timedelta(days=7)
    elif time_range == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 12:
            end = start.replace(year=start.year+1, month=1)
        else:
            end = start.replace(month=start.month+1)
    elif time_range == 'year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year+1)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

    try:
        with get_connection() as con:
            cur = con.cursor()
            
            if group_by == 'department':
                query = """
                    SELECT 
                        COALESCE(d.NOMBRE, 'Sin Departamento') as depto,
                        SUM(vta.CANTIDAD) as cantidad,
                        SUM(vta.TOTAL_ARTICULO) as ingreso
                    FROM VENTATICKETS_ARTICULOS vta
                    JOIN VENTATICKETS vt ON vt.ID = vta.TICKET_ID
                    LEFT JOIN PRODUCTOS p ON p.CODIGO = vta.PRODUCTO_CODIGO
                    LEFT JOIN DEPARTAMENTOS d ON d.ID = p.DEPT
                    WHERE vt.ESTA_CANCELADO = 0 
                      AND vt.VENDIDO_EN >= ? AND vt.VENDIDO_EN < ?
                """
                params = [start, end]
                
                query += """
                    GROUP BY d.NOMBRE
                    ORDER BY SUM(vta.TOTAL_ARTICULO) DESC
                """
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [{
                    'nombre': row[0].strip() if row[0] else 'Sin Departamento',
                    'cantidad': float(row[1]) if row[1] is not None else 0.0,
                    'ingreso': float(row[2]) if row[2] is not None else 0.0
                } for row in rows]
                
            else: # group by product
                query = """
                    SELECT 
                        vta.PRODUCTO_CODIGO,
                        vta.PRODUCTO_NOMBRE,
                        COALESCE(d.NOMBRE, 'Sin Departamento') as depto,
                        SUM(vta.CANTIDAD) as cantidad,
                        SUM(vta.TOTAL_ARTICULO) as ingreso
                    FROM VENTATICKETS_ARTICULOS vta
                    JOIN VENTATICKETS vt ON vt.ID = vta.TICKET_ID
                    LEFT JOIN PRODUCTOS p ON p.CODIGO = vta.PRODUCTO_CODIGO
                    LEFT JOIN DEPARTAMENTOS d ON d.ID = p.DEPT
                    WHERE vt.ESTA_CANCELADO = 0 
                      AND vt.VENDIDO_EN >= ? AND vt.VENDIDO_EN < ?
                """
                params = [start, end]
                
                if depto_filter and depto_filter.strip() != "":
                    query += " AND d.NOMBRE = ?"
                    params.append(depto_filter.strip())
                    
                query += """
                    GROUP BY vta.PRODUCTO_CODIGO, vta.PRODUCTO_NOMBRE, d.NOMBRE
                    ORDER BY SUM(vta.TOTAL_ARTICULO) DESC
                """
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [{
                    'codigo': row[0].strip() if row[0] else '',
                    'nombre': row[1].strip() if row[1] else 'Articulo Sin Nombre',
                    'departamento': row[2].strip() if row[2] else 'Sin Departamento',
                    'cantidad': float(row[3]) if row[3] is not None else 0.0,
                    'ingreso': float(row[4]) if row[4] is not None else 0.0
                } for row in rows]
                
    except Exception as e:
        print(f"Error en get_sales_report: {e}")
        return []


def search_clients(query):
    try:
        with get_connection() as con:
            cur = con.cursor()
            query_sql = """
                SELECT NUMERO, NOMBRE, DIRECCION, TELEFONO, LIMITE_CREDITO, DSALDOACTUAL 
                FROM CLIENTES 
                WHERE CAST(NUMERO AS VARCHAR(10)) CONTAINING ? OR NOMBRE CONTAINING ?
                ORDER BY NOMBRE
            """
            cur.execute(query_sql, (query, query))
            
            rows = cur.fetchall()
            return [{
                'numero': row[0],
                'nombre': row[1].strip() if row[1] else '',
                'direccion': row[2].strip() if row[2] else '',
                'telefono': row[3].strip() if row[3] else '',
                'limite_credito': float(row[4]) if row[4] is not None else 0.0,
                'saldo_actual': float(row[5]) if row[5] is not None else 0.0
            } for row in rows]
    except Exception as e:
        print(f"Error en search_clients: {e}")
        return []

def get_clients_all():
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                SELECT NUMERO, NOMBRE, DIRECCION, TELEFONO, LIMITE_CREDITO, DSALDOACTUAL 
                FROM CLIENTES 
                ORDER BY NOMBRE
            """)
            return [{
                'numero': row[0],
                'nombre': row[1].strip() if row[1] else '',
                'direccion': row[2].strip() if row[2] else '',
                'telefono': row[3].strip() if row[3] else '',
                'limite_credito': float(row[4]) if row[4] is not None else 0.0,
                'saldo_actual': float(row[5]) if row[5] is not None else 0.0
            } for row in cur.fetchall()]
    except Exception as e:
        print(f"Error en get_clients_all: {e}")
        return []

def update_client(numero, nombre, direccion, telefono, limite_credito):
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("SELECT NUMERO FROM CLIENTES WHERE NUMERO = ?", (numero,))
            if not cur.fetchone():
                return False, "Cliente no encontrado"
            
            cur.execute("""
                UPDATE CLIENTES 
                SET NOMBRE = ?, DIRECCION = ?, TELEFONO = ?, LIMITE_CREDITO = ? 
                WHERE NUMERO = ?
            """, (nombre, direccion, telefono, limite_credito, numero))
            con.commit()
            return True, "Cliente actualizado exitosamente"
    except Exception as e:
        print(f"Error actualizando cliente {numero}: {e}")
        return False, str(e)


def authenticate_user(username, password):
    try:
        with get_connection() as con:
            cur = con.cursor()
            query_sql = "SELECT ID, NOMBRE_COMPLETO, ACTIVO, PERMISOS FROM USUARIOS WHERE USUARIO = ? AND CLAVE = ?"
            cur.execute(query_sql, (username, password))
            row = cur.fetchone()
            if row:
                user_id, nombre, activo, permisos = row
                if str(activo).strip() == '1':
                    permisos_str = ""
                    if permisos:
                        # permisos is a BLOB, might need conversion
                        if isinstance(permisos, bytes):
                            permisos_str = permisos.decode('utf-8', errors='ignore')
                        else:
                            permisos_str = str(permisos)
                    
                    is_admin = permisos_str.strip() == ""
                    return True, {
                        "id": user_id, 
                        "nombre": nombre.strip() if nombre else "Usuario",
                        "is_admin": is_admin,
                        "permisos": permisos_str
                    }
                else:
                    return False, "Usuario inactivo"
            return False, "Credenciales incorrectas"
    except Exception as e:
        print(f"Error en authenticate_user: {e}")
        return False, str(e)

def get_all_users():
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("SELECT ID, NOMBRE_COMPLETO, USUARIO, CLAVE, ACTIVO, PERMISOS FROM USUARIOS ORDER BY ID")
            rows = cur.fetchall()
            users = []
            for r in rows:
                permisos = r[5]
                permisos_str = ""
                if permisos:
                    if isinstance(permisos, bytes):
                        permisos_str = permisos.decode('utf-8', errors='ignore')
                    else:
                        permisos_str = str(permisos)
                
                users.append({
                    "id": r[0],
                    "nombre": r[1].strip() if r[1] else "",
                    "usuario": r[2].strip() if r[2] else "",
                    "clave": r[3].strip() if r[3] else "",
                    "activo": str(r[4]).strip() == '1',
                    "permisos": permisos_str
                })
            return users
    except Exception as e:
        print(f"Error en get_all_users: {e}")
        return []

def save_user(data):
    try:
        with get_connection() as con:
            cur = con.cursor()
            user_id = data.get('id')
            nombre = data.get('nombre')
            usuario = data.get('usuario')
            clave = data.get('clave')
            permisos = data.get('permisos', '')
            activo = '1' if data.get('activo') else '0'
            
            if user_id:
                # Update
                cur.execute("""
                    UPDATE USUARIOS 
                    SET NOMBRE_COMPLETO = ?, USUARIO = ?, CLAVE = ?, PERMISOS = ?, ACTIVO = ?
                    WHERE ID = ?
                """, (nombre, usuario, clave, permisos, activo, user_id))
            else:
                # Insert
                cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM USUARIOS")
                new_id = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO USUARIOS (ID, NOMBRE_COMPLETO, USUARIO, CLAVE, PERMISOS, ACTIVO, CREATED_ON)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (new_id, nombre, usuario, clave, permisos, activo))
            
            con.commit()
            return True, "Usuario guardado exitosamente"
    except Exception as e:
        print(f"Error en save_user: {e}")
        return False, str(e)
