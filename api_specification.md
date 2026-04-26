# Especificación de API REST - Inventario PDV

Esta especificación detalla las rutas disponibles para interactuar con la Base de Datos de Abarrotes PDV. La arquitectura está dividida verticalmente en **Inventario** y **Precios** para optimizar la transferencia de datos.

Todas las respuestas y peticiones utilizan formato `application/json`.

---

## Módulo: Inventario (Inventory POST/GET)
Rutas dedicadas exclusivamente a la lectura y modificación de existencias.

### 1. Obtener todo el inventario
Retorna la lista de todos los productos pero extrayendo únicamente los campos necesarios de inventario.
- **Ruta:** `GET /api/inventory`
- **Respuesta Exitosa (200 OK):**
```json
[
  {
    "codigo": "7501055310883",
    "descripcion": "COCA COLA 600ML",
    "departamento": "Abarrotes",
    "inventario": 24.0
  }
]
```

### 2. Buscar en Inventario
Busca productos por código (exacto o parcial) o descripción, retornando solo datos de inventario.
- **Ruta:** `POST /api/inventory/search`
- **Body:**
```json
{
  "query": "coca cola"
}
```
- **Respuesta Exitosa (200 OK):** Mismo formato que la obtención total pero filtrada.

### 3. Actualizar Stock
Sobrescribe la cantidad en inventario actual y guarda un registro en `HISTORIAL_INVENTARIO`.
- **Ruta:** `POST /api/inventory/update`
- **Body:**
```json
{
  "codigo": "7501055310883",
  "cantidad": 30.5
}
```
- **Respuesta Exitosa (200 OK):**
```json
{ "message": "Inventario actualizado exitosamente" }
```

---

## Módulo: Precios (Prices POST/GET)
Rutas dedicadas a los costos y ganancias financieras de los productos.

### 1. Obtener todos los precios
- **Ruta:** `GET /api/prices`
- **Respuesta Exitosa (200 OK):**
```json
[
  {
    "codigo": "7501055310883",
    "descripcion": "COCA COLA 600ML",
    "departamento": "Abarrotes",
    "precio": 18.0,
    "p_costo": 12.5
  }
]
```

### 2. Buscar Precios
- **Ruta:** `POST /api/prices/search`
- **Body:**
```json
{
  "query": "coca cola"
}
```
- **Respuesta Exitosa (200 OK):** Mismo formato de precios filtrado.

### 3. Actualizar Precios
Permite actualizar el Precio de Compra (`p_costo`), el Precio de Venta (`p_venta`), o ambos simultáneamente.
- **Ruta:** `POST /api/prices/update`
- **Body:**
```json
{
  "codigo": "7501055310883",
  "p_venta": 19.5,
  "p_costo": 13.0
}
```
*(Nota: Si omites `p_venta` o `p_costo`, solo se actualizará el campo que propociones).*
- **Respuesta Exitosa (200 OK):**
```json
{ "message": "Precios actualizados exitosamente" }
```

---
> [!NOTE]
> **Autenticación:**
> Actualmente la API opera dentro de una Red Local y no expone métodos de autenticación (`Tokens` o `CORS`). Si el *"otro front"* será hosteado en un servidor externo real y no consumido desde un APK / Web en la misma red o mismo servidor Flask, será necesario que implementes CORS en `app.py` mediante la librería `flask-cors`.
