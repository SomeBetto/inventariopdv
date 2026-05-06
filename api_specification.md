# Especificación de API REST - Inventario PDV

Esta especificación detalla las rutas disponibles para interactuar con la Base de Datos de Abarrotes PDV. La arquitectura está dividida verticalmente en **Inventario** y **Precios** para optimizar la transferencia de datos y mejorar la experiencia de usuario.

El objetivo de este documento es proporcionar el contexto funcional necesario (incluyendo el comportamiento que se espera del lado del frontend) para poder recrear clientes alternativos (por ejemplo, una app en React Native, Android nativo, o Angular) consumiendo este backend.

Todas las respuestas y peticiones utilizan formato `application/json`.

---

## 1. Módulo: Inventario (Inventory POST/GET)
Rutas dedicadas exclusivamente a la lectura y modificación de existencias (Stock).

### 1.1. Obtener todo el inventario
Retorna la lista de todos los productos en la base de datos extrayendo únicamente los campos necesarios de inventario.

- **Ruta:** `GET /api/inventory`
- **Uso en el Frontend:** 
  - Se manda llamar al inicializar la aplicación o al cambiar a la pestaña de "Inventario" (si no se tiene la data en caché local).
  - El frontend procesa esta lista para rellenar de manera dinámica el selector de departamentos (`filterDept`), extrayendo los valores únicos.
  - El frontend utiliza estos datos base para hacer filtros locales (por departamento o si el stock está bajo/en ceros) si el usuario no ha escrito nada en la barra de búsqueda.
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

### 1.2. Buscar en Inventario
Busca productos por código (exacto o parcial) o descripción, retornando solo datos de inventario. El backend maneja lógica de búsqueda de subcadenas insensible a mayúsculas/minúsculas.

- **Ruta:** `POST /api/inventory/search`
- **Uso en el Frontend:**
  - Integrado a la barra de búsqueda (`masterSearch`).
  - **Debounce:** Cuando el usuario teclea, se debe esperar un lapso corto (ej. 400ms) antes de llamar a este endpoint para evitar saturar el servidor. Si el usuario presiona "Enter", la petición se hace inmediatamente.
  - **Escáner de Códigos de Barras:** Cuando la cámara lee un código QR o de barras, envía la lectura exacta a este endpoint.
  - Los resultados recibidos se cruzan en el cliente con los filtros de "Departamento" y "Niveles de Stock" seleccionados actualmente.
- **Body:**
```json
{
  "query": "coca cola"
}
```
- **Respuesta Exitosa (200 OK):** Arreglo de productos, con el mismo formato que `GET /api/inventory`.

### 1.3. Actualizar Stock
Sobrescribe la cantidad en inventario actual y guarda un registro interno en la tabla `HISTORIAL_INVENTARIO` del sistema Punto de Venta.

- **Ruta:** `POST /api/inventory/update`
- **Uso en el Frontend:**
  - Se desencadena desde un modal o Bottom Sheet al tocar el botón "Ajustar Stock" en una tarjeta de producto.
  - El frontend proporciona controles de `+` y `-` para modificar la cantidad, o permite la introducción manual de texto.
  - Tras obtener un 200 OK, el frontend puede cerrar el modal, mostrar una notificación ("Toast") de éxito y disparar una re-carga silenciosa (`GET /api/inventory` o búsqueda) para refrescar el estado.
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

## 2. Módulo: Precios (Prices POST/GET)
Rutas dedicadas a los costos y ganancias financieras de los productos.

### 2.1. Obtener todos los precios
- **Ruta:** `GET /api/prices`
- **Uso en el Frontend:**
  - Llamada principal cuando el usuario cambia a la pestaña "Precios".
  - Se aprovecha para recalcular de manera local la **Ganancia (Profit)** de cada producto: `((precio_venta - precio_costo) / precio_costo) * 100`.
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

### 2.2. Buscar Precios
Similar a la búsqueda de inventario, pero retorna el objeto adaptado al formato de precios.

- **Ruta:** `POST /api/prices/search`
- **Uso en el Frontend:**
  - Operación idéntica a la barra de búsqueda del inventario (incluyendo debounce), pero apuntando a este endpoint cuando la pestaña activa es "Precios".
- **Body:**
```json
{
  "query": "coca cola"
}
```
- **Respuesta Exitosa (200 OK):** Mismo formato de precios filtrado.

### 2.3. Actualizar Precios
Permite actualizar el Precio de Compra (`p_costo`), el Precio de Venta (`p_venta`), o ambos simultáneamente.

- **Ruta:** `POST /api/prices/update`
- **Uso en el Frontend:**
  - Disparado desde un Modal específico de precios que pide ingresar el "Costo" y el "Precio de Venta".
  - El frontend calcula de forma reactiva (en tiempo real) la **"Ganancia Proyectada %"** conforme el usuario teclea en los inputs.
  - Al enviar la petición, se puede mandar uno u ambos valores.
- **Body:**
```json
{
  "codigo": "7501055310883",
  "p_venta": 19.5,
  "p_costo": 13.0
}
```
*(Nota: Si omites `p_venta` o `p_costo` enviando nulos o no enviando la llave, solo se actualizará el campo proporcionado).*
- **Respuesta Exitosa (200 OK):**
```json
{ "message": "Precios actualizados exitosamente" }
```

## 3. Módulo: Catálogo (Catalog POST/GET)
Rutas dedicadas a los datos maestros de los productos, como la descripción y departamento.

### 3.1. Obtener todo el catálogo
- **Ruta:** `GET /api/catalog`
- **Uso en el Frontend:**
  - Llamada principal cuando el usuario cambia a la pestaña "Catálogo".
- **Respuesta Exitosa (200 OK):**
```json
[
  {
    "codigo": "7501055310883",
    "descripcion": "COCA COLA 600ML",
    "departamento": "Abarrotes"
  }
]
```

### 3.2. Buscar en Catálogo
- **Ruta:** `POST /api/catalog/search`
- **Uso en el Frontend:**
  - Operación de búsqueda idéntica a los otros módulos pero apuntando al catálogo.
- **Body:**
```json
{
  "query": "coca cola"
}
```

### 3.3. Actualizar Descripción
Permite actualizar la descripción de un producto.

- **Ruta:** `POST /api/catalog/update`
- **Uso en el Frontend:**
  - Disparado desde un Modal específico (descModal) que pide ingresar la nueva "Descripción".
- **Body:**
```json
{
  "codigo": "7501055310883",
  "descripcion": "COCA COLA 600ML NUEVA"
}
```
- **Respuesta Exitosa (200 OK):**
```json
{ "message": "Descripción actualizada exitosamente" }
```

---

## 4. Módulo: Ventas (Sales POST)
Rutas dedicadas al análisis y lectura de las ventas procesadas (histórico).

### 4.1. Reporte de Ventas Agrupado
- **Ruta:** `POST /api/sales/report`
- **Uso en el Frontend:**
  - Llamado al cambiar a la pestaña "Ventas" o cambiar cualquier filtro de tiempo/agrupación.
- **Body:**
```json
{
  "time_range": "day", 
  "group_by": "product",
  "department": ""
}
```
* `time_range`: "day", "week", "month", "year"
* `group_by`: "product", "department"
* `department`: (Opcional) Filtrar un departamento específico cuando se agrupa por producto.

- **Respuesta Exitosa (Agrupado por Producto):**
```json
[
  {
    "codigo": "7501055310883",
    "nombre": "COCA COLA 600ML",
    "departamento": "Abarrotes",
    "cantidad": 12.0,
    "ingreso": 240.0
  }
]
```
- **Respuesta Exitosa (Agrupado por Departamento):**
```json
[
  {
    "nombre": "Abarrotes",
    "cantidad": 50.0,
    "ingreso": 1500.50
  }
]
```

---


## 5. Módulo: Clientes (Clients POST/GET)
Rutas dedicadas a la lectura y modificación de los datos y límite de crédito de los clientes registrados.

### 5.1. Obtener todos los clientes
- **Ruta:** `GET /api/clients/`
- **Uso en el Frontend:**
  - Se llama al inicializar la pestaña "Clientes".
- **Respuesta Exitosa (200 OK):**
```json
[
  {
    "numero": 33,
    "nombre": "ALONZO PIEDRA",
    "direccion": "Calle 1",
    "telefono": "123456789",
    "limite_credito": 300.0,
    "saldo_actual": 0.0
  }
]
```

### 5.2. Buscar Clientes
Busca clientes por su nombre exacto o parcial.

- **Ruta:** `POST /api/clients/search`
- **Uso en el Frontend:**
  - Se conecta a la barra de búsqueda general cuando se está en la pestaña "Clientes".
- **Body:**
```json
{
  "query": "alonzo"
}
```

### 5.3. Actualizar Cliente
Permite editar el nombre, dirección, teléfono y límite de crédito de un cliente. El saldo actual es de solo lectura y no se modifica por esta vía.

- **Ruta:** `POST /api/clients/update`
- **Uso en el Frontend:**
  - Se dispara al guardar los cambios desde el modal de edición de clientes.
- **Body:**
```json
{
  "numero": 33,
  "nombre": "ALONZO PIEDRA",
  "direccion": "Calle 1",
  "telefono": "123456789",
  "limite_credito": 400.0
}
```
- **Respuesta Exitosa (200 OK):**
```json
{ "message": "Cliente actualizado exitosamente" }
```

---

## 6. Funcionalidades y Consideraciones Generales del Frontend

Para replicar el funcionamiento del frontend original, asegúrate de implementar:

1. **Estado Compartido y Pestañas:**  La UI está segmentada en tres contextos principales (Inventario, Precios, Catálogo). Dependiendo de cuál esté activo, varían los endpoints a consumir y la tarjeta gráfica.
2. **Filtrado Múltiple Híbrido:** El backend procesa las búsquedas por texto (`coca`, `1234`), pero el frontend se hace cargo del filtrado por categorías (ej. departamento="Lácteos") y por umbrales visuales de negocio (ej. "Sin Stock" o "Bajo Stock"). 
3. **Manejo de Errores y Loading:** En cada petición al backend se debe prevenir el spam de clicks mediante estados de "cargando". Además, cualquier código `400` o `500` debe ser atrapado para mostrar alertas al usuario ("Toast").
4. **CORS:** Actualmente la API opera dentro de una Red Local y no expone métodos de autenticación explícitos. Si el *"nuevo front"* será una app que no comparta el origen de puerto y dominio del servidor (ej. React corriendo en el puerto `3000`), será necesario habilitar `flask-cors` en `app.py`.
