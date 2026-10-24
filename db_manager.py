import ctypes
import os
import sys
import fdb
from datetime import datetime, timedelta
import config
import event_logger

db_logger = event_logger.get_logger('db')

# --- PARCHE DE COMPATIBILIDAD (MONKEYPATCH PARA FIREBRID) ---
original_cdll = ctypes.CDLL
original_windll = ctypes.WinDLL

def robust_load(original_func, name, *args, **kwargs):
    lib = original_func(name, *args, **kwargs)
    if name and ('fbclient' in name.lower() or 'gds32' in name.lower()):
        functions_to_mock = [
            'fb_shutdown_callback', 'fb_shutdown', 
            'fb_cancel_operation', 'fb_ping', 'fb_get_master_interface'
        ]
        for func_name in functions_to_mock:
            if not hasattr(lib, func_name):
                def dummy_func(*args): return 0
                mock = ctypes.WINFUNCTYPE(ctypes.c_int)(dummy_func)
                setattr(lib, func_name, mock)
    return lib

ctypes.CDLL = lambda name, *args, **kwargs: robust_load(original_cdll, name, *args, **kwargs)
ctypes.WinDLL = lambda name, *args, **kwargs: robust_load(original_windll, name, *args, **kwargs)
# -------------------------------------------------------------

def get_connection():
    """Retorna una conexión activa a la base de datos Firebird configurada."""
    return fdb.connect(
        database=config.DB_PATH,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        fb_library_name=config.FB_CLIENT_LIBRARY
    )

# --- Consultas Genéricas y Reutilizables de Productos ---

def _query_products(filter_query=None, mode='inventory'):
    """
    Función unificada para consultar productos de Firebird.
    mode puede ser: 'inventory', 'prices', o 'catalog'.
    """
    sql = """
        SELECT p.CODIGO, p.DESCRIPCION, p.DINVENTARIO, p.PVENTA, p.PCOSTO, d.NOMBRE 
        FROM PRODUCTOS p 
        LEFT JOIN DEPARTAMENTOS d ON p.DEPT = d.ID
    """
    params = ()
    if filter_query is not None and str(filter_query).strip() != "":
        clean_q = str(filter_query).strip()
        sql += " WHERE p.CODIGO CONTAINING ? OR p.DESCRIPCION CONTAINING ?"
        params = (clean_q, clean_q)

    sql += " ORDER BY p.DESCRIPCION"

    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()

            results = []
            for row in rows:
                codigo = row[0].strip() if row[0] else ""
                descripcion = row[1].strip() if row[1] else ""
                depto = row[5].strip() if row[5] else "Sin Depto"

                if mode == 'inventory':
                    results.append({
                        'codigo': codigo,
                        'descripcion': descripcion,
                        'inventario': float(row[2]) if row[2] is not None else 0.0,
                        'departamento': depto
                    })
                elif mode == 'prices':
                    results.append({
                        'codigo': codigo,
                        'descripcion': descripcion,
                        'precio': float(row[3]) if row[3] is not None else 0.0,
                        'p_costo': float(row[4]) if row[4] is not None else 0.0,
                        'departamento': depto
                    })
                elif mode == 'catalog':
                    results.append({
                        'codigo': codigo,
                        'descripcion': descripcion,
                        'departamento': depto
                    })
            return results
    except Exception as e:
        db_logger.error(f"Error en _query_products(mode={mode}, query={filter_query}): {e}")
        return []

# --- Módulo: Inventario ---

def get_inventory_all():
    return _query_products(filter_query=None, mode='inventory')

def search_inventory(query):
    return _query_products(filter_query=query, mode='inventory')

def update_inventory(codigo, nueva_cantidad, user_name='Directo', ip_address=''):
    try:
        nueva_cantidad = float(nueva_cantidad)
    except (ValueError, TypeError):
        return False, "La cantidad especificada no es un número válido"

    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("SELECT DESCRIPCION, DINVENTARIO FROM PRODUCTOS WHERE CODIGO = ?", (codigo,))
            row = cur.fetchone()
            if not row:
                return False, "Producto no encontrado"

            descripcion = row[0].strip() if row[0] else codigo
            cantidad_actual = float(row[1]) if row[1] is not None else 0.0

            cur.execute("UPDATE PRODUCTOS SET DINVENTARIO = ? WHERE CODIGO = ?", (nueva_cantidad, codigo))

            # Registro nativo en HISTORIAL_INVENTARIO de Abarrotes PDV
            insert_history = """
                INSERT INTO HISTORIAL_INVENTARIO (USUARIO_ID, CUANDO_FUE, TIPO, HABIA, CANTIDAD, CODIGO_PRODUCTO, CAJA_ID)
                VALUES (1, CURRENT_TIMESTAMP, 'a', ?, ?, ?, 1)
            """
            cur.execute(insert_history, (cantidad_actual, nueva_cantidad, codigo))
            con.commit()

            # Auditoría en event_logger
            event_logger.log_event(
                category='INVENTARIO',
                action='ACTUALIZAR_STOCK',
                entity_id=codigo,
                entity_name=descripcion,
                details=f"Stock ajustado: {cantidad_actual} -> {nueva_cantidad} (dif: {nueva_cantidad - cantidad_actual:+.2f})",
                user_name=user_name,
                ip_address=ip_address
            )
            return True, "Inventario actualizado exitosamente"
    except Exception as e:
        db_logger.error(f"Error actualizando inventario para {codigo}: {e}")
        return False, str(e)

# --- Módulo: Precios ---

def get_prices_all():
    return _query_products(filter_query=None, mode='prices')

def search_prices(query):
    return _query_products(filter_query=query, mode='prices')

def update_prices(codigo, p_venta, p_costo, user_name='Directo', ip_address=''):
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("SELECT DESCRIPCION, PVENTA, PCOSTO FROM PRODUCTOS WHERE CODIGO = ?", (codigo,))
            row = cur.fetchone()
            if not row:
                return False, "Producto no encontrado"

            descripcion = row[0].strip() if row[0] else codigo
            old_venta = float(row[1]) if row[1] is not None else 0.0
            old_costo = float(row[2]) if row[2] is not None else 0.0

            details_list = []
            if p_venta is not None and p_costo is not None:
                cur.execute("UPDATE PRODUCTOS SET PVENTA = ?, PCOSTO = ? WHERE CODIGO = ?", (p_venta, p_costo, codigo))
                details_list.append(f"Venta: ${old_venta:.2f} -> ${p_venta:.2f}, Costo: ${old_costo:.2f} -> ${p_costo:.2f}")
            elif p_venta is not None:
                cur.execute("UPDATE PRODUCTOS SET PVENTA = ? WHERE CODIGO = ?", (p_venta, codigo))
                details_list.append(f"Venta: ${old_venta:.2f} -> ${p_venta:.2f}")
            elif p_costo is not None:
                cur.execute("UPDATE PRODUCTOS SET PCOSTO = ? WHERE CODIGO = ?", (p_costo, codigo))
                details_list.append(f"Costo: ${old_costo:.2f} -> ${p_costo:.2f}")

            con.commit()

            # Auditoría en event_logger
            event_logger.log_event(
                category='PRECIOS',
                action='ACTUALIZAR_PRECIO',
                entity_id=codigo,
                entity_name=descripcion,
                details=", ".join(details_list),
                user_name=user_name,
                ip_address=ip_address
            )
            return True, "Precios actualizados exitosamente"
    except Exception as e:
        db_logger.error(f"Error actualizando precios para {codigo}: {e}")
        return False, str(e)

# --- Módulo: Catálogo ---

def get_catalog_all():
    return _query_products(filter_query=None, mode='catalog')

def search_catalog(query):
    return _query_products(filter_query=query, mode='catalog')

def update_description(codigo, nueva_descripcion, user_name='Directo', ip_address=''):
    if not nueva_descripcion or not nueva_descripcion.strip():
        return False, "La descripción no puede estar vacía"

    nueva_descripcion = nueva_descripcion.strip()
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("SELECT DESCRIPCION FROM PRODUCTOS WHERE CODIGO = ?", (codigo,))
            row = cur.fetchone()
            if not row:
                return False, "Producto no encontrado"

            old_desc = row[0].strip() if row[0] else ""
            cur.execute("UPDATE PRODUCTOS SET DESCRIPCION = ? WHERE CODIGO = ?", (nueva_descripcion, codigo))
            con.commit()

            event_logger.log_event(
                category='CATALOGO',
                action='ACTUALIZAR_DESCRIPCION',
                entity_id=codigo,
                entity_name=nueva_descripcion,
                details=f"Descripción cambiada: '{old_desc}' -> '{nueva_descripcion}'",
                user_name=user_name,
                ip_address=ip_address
            )
            return True, "Descripción actualizada exitosamente"
    except Exception as e:
        db_logger.error(f"Error actualizando descripción para {codigo}: {e}")
        return False, str(e)

# --- Módulo: Clientes ---

def _query_clients(filter_query=None):
    sql = """
        SELECT NUMERO, NOMBRE, DIRECCION, TELEFONO, LIMITE_CREDITO, DSALDOACTUAL 
        FROM CLIENTES
    """
    params = ()
    if filter_query is not None and str(filter_query).strip() != "":
        clean_q = str(filter_query).strip()
        sql += " WHERE CAST(NUMERO AS VARCHAR(10)) CONTAINING ? OR NOMBRE CONTAINING ?"
        params = (clean_q, clean_q)

    sql += " ORDER BY NOMBRE"

    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(sql, params)
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
        db_logger.error(f"Error consultando clientes (query={filter_query}): {e}")
        return []

def get_clients_all():
    return _query_clients(filter_query=None)

def search_clients(query):
    return _query_clients(filter_query=query)

def update_client(numero, nombre, direccion, telefono, limite_credito, user_name='Directo', ip_address=''):
    try:
        limite_credito = float(limite_credito) if limite_credito is not None else 0.0
    except (ValueError, TypeError):
        limite_credito = 0.0

    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute("SELECT NUMERO, NOMBRE FROM CLIENTES WHERE NUMERO = ?", (numero,))
            row = cur.fetchone()
            if not row:
                return False, "Cliente no encontrado"

            cur.execute("""
                UPDATE CLIENTES 
                SET NOMBRE = ?, DIRECCION = ?, TELEFONO = ?, LIMITE_CREDITO = ? 
                WHERE NUMERO = ?
            """, (nombre, direccion, telefono, limite_credito, numero))
            con.commit()

            event_logger.log_event(
                category='CLIENTES',
                action='ACTUALIZAR_CLIENTE',
                entity_id=str(numero),
                entity_name=nombre or '',
                details=f"Datos actualizados: Tel: {telefono or 'N/A'}, Límite: ${limite_credito:.2f}",
                user_name=user_name,
                ip_address=ip_address
            )
            return True, "Cliente actualizado exitosamente"
    except Exception as e:
        db_logger.error(f"Error actualizando cliente {numero}: {e}")
        return False, str(e)

# --- Módulo: Reportes de Ventas ---

def get_sales_report(time_range, group_by, depto_filter=None):
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
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    elif time_range == 'year':
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
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
                    GROUP BY d.NOMBRE
                    ORDER BY SUM(vta.TOTAL_ARTICULO) DESC
                """
                cur.execute(query, [start, end])
                rows = cur.fetchall()

                return [{
                    'nombre': row[0].strip() if row[0] else 'Sin Departamento',
                    'cantidad': float(row[1]) if row[1] is not None else 0.0,
                    'ingreso': float(row[2]) if row[2] is not None else 0.0
                } for row in rows]
            else:
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
        db_logger.error(f"Error en get_sales_report: {e}")
        return []

# --- Módulo: Usuarios y Permisos ---

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
        db_logger.error(f"Error en authenticate_user: {e}")
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
        db_logger.error(f"Error en get_all_users: {e}")
        return []

def save_user(data, user_name='Directo', ip_address=''):
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
                cur.execute("""
                    UPDATE USUARIOS 
                    SET NOMBRE_COMPLETO = ?, USUARIO = ?, CLAVE = ?, PERMISOS = ?, ACTIVO = ?
                    WHERE ID = ?
                """, (nombre, usuario, clave, permisos, activo, user_id))
                action_text = f"Usuario actualizado: @{usuario}"
            else:
                cur.execute("SELECT COALESCE(MAX(ID), 0) + 1 FROM USUARIOS")
                user_id = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO USUARIOS (ID, NOMBRE_COMPLETO, USUARIO, CLAVE, PERMISOS, ACTIVO, CREATED_ON)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, nombre, usuario, clave, permisos, activo))
                action_text = f"Nuevo usuario creado: @{usuario}"

            con.commit()

            event_logger.log_event(
                category='USUARIOS',
                action='GUARDAR_USUARIO',
                entity_id=str(user_id),
                entity_name=nombre or usuario,
                details=action_text,
                user_name=user_name,
                ip_address=ip_address
            )
            return True, "Usuario guardado exitosamente"
    except Exception as e:
        db_logger.error(f"Error en save_user: {e}")
        return False, str(e)
