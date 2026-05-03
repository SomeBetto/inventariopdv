# Reglas del Agente - Inventario PDV

Este documento define el contexto, las reglas de arquitectura y las directrices de desarrollo para esta aplicación. **Cualquier agente de IA que trabaje en este proyecto debe leer y adherirse a las siguientes reglas.**

## 1. Contexto del Proyecto
- **Tecnologías Principales**: Python (Flask) en el backend, conexión a base de datos Firebird (usando `fdb`), y frontend web (HTML/JS) ubicado en `templates/`.
- **Propósito**: Extender la funcionalidad del sistema "Abarrotes PDV" proporcionando una API REST y una interfaz web para gestionar de manera remota el **Inventario** y los **Precios**.
- **Base de Datos**: Firebird 2.5/3.0. Se conecta localmente (`C:\Program Files (x86)\AbarrotesPDV\db\PDVDATA.FDB`). **Solo usa sintaxis SQL compatible con Firebird** (ej. `CONTAINING` para búsquedas tipo LIKE insensibles a mayúsculas/minúsculas).

## 2. Arquitectura de la API
- Toda la estructura de endpoints está definida en `api_specification.md`. Este archivo es la *fuente única de verdad* (Single Source of Truth) para la comunicación Frontend-Backend.
- Existe una **Separación Vertical Estricta** entre Módulos:
  - **Inventario**: Endpoints bajo `/api/inventory`. Solo manejan cantidades, stock (`DINVENTARIO`) y registros en el historial.
  - **Precios**: Endpoints bajo `/api/prices`. Solo manejan costos (`PCOSTO`), precios de venta (`PVENTA`) y ganancias.
  - **Catálogo**: Endpoints bajo `/api/catalog`. Solo manejan datos maestros del producto como la descripción (`DESCRIPCION`) y departamento.
  - **Ventas**: Endpoints bajo `/api/sales`. Dedicados al análisis y reportes históricos cruzando datos de tickets.
  - Nunca mezcles la lógica de estos módulos en un solo endpoint.

## 3. Reglas de Código
- **Separación de Responsabilidades**:
  - `app.py`: Dedicado EXCLUSIVAMENTE a definir rutas de Flask, recibir parámetros (JSON), validar peticiones y retornar respuestas HTTP (status codes).
  - `db_manager.py`: Dedicado EXCLUSIVAMENTE a conexiones, consultas y transacciones SQL con Firebird. `app.py` no debe contener sentencias SQL bajo ninguna circunstancia.
- **Manejo de Errores**:
  - `db_manager.py` debe retornar tuplas de éxito/error `(True/False, "Mensaje")` o arreglos vacíos `[]` en caso de fallo, capturando las excepciones (`try/except`).
  - `app.py` debe manejar correctamente los códigos HTTP (200 para éxito, 400 para errores de cliente/datos incompletos, 500 para errores del servidor/base de datos).

## 4. Instrucción de Auto-Actualización
- Si realizas **cambios significativos** en el proyecto, como:
  1. Agregar, modificar o eliminar endpoints.
  2. Modificar la estructura de respuesta/petición JSON.
  3. Cambiar la arquitectura de módulos o base de datos.
  4. Agregar nuevas tecnologías o dependencias.
- **DEBES** hacer lo siguiente antes de finalizar tu tarea:
  - Actualizar `api_specification.md` para reflejar con precisión el nuevo estado de la API.
  - Actualizar este archivo `agent.md` si cambian las reglas generales del sistema o la arquitectura.
