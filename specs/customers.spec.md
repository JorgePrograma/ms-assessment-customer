# Spec: Customers API

> Spec-Driven Development: este documento es la fuente de verdad del comportamiento.
> Cada criterio de aceptación (`AC-xx`) está cubierto por al menos una prueba
> automatizada en `tests/`, referenciada por su identificador.

## 1. Contexto

API para registrar y consultar clientes de una plataforma financiera.

## 2. Modelo de dominio

| Campo        | Tipo              | Reglas                                                     |
|--------------|-------------------|------------------------------------------------------------|
| `id`         | UUID v4           | Generado por el sistema. Inmutable.                         |
| `name`       | string            | Requerido, 1–120 caracteres, sin espacios al inicio/final. |
| `email`      | string (email)    | Requerido, formato válido, único (case-insensitive), se almacena en minúsculas. |
| `status`     | enum              | `ACTIVE` \| `PENDING` \| `BLOCKED`.                         |
| `created_at` | datetime (UTC)    | Generado por el sistema al crear. Inmutable.                |

## 3. Formato de respuesta

Todas las respuestas de `/customers` usan un sobre (envelope) uniforme.

### 3.1 Éxito — recurso individual

```json
{
  "success": true,
  "data": { "id": "…", "name": "Juan Pérez", "email": "juan@example.com", "status": "PENDING", "created_at": "…" }
}
```

### 3.2 Éxito — colección paginada

```json
{
  "success": true,
  "data": [ { "id": "…" } ],
  "meta": { "page": 1, "size": 20, "total": 42, "pages": 3 }
}
```

### 3.3 Error

```json
{
  "success": false,
  "error": {
    "code": "CUSTOMER_NOT_FOUND",
    "message": "Customer '…' not found",
    "details": null
  }
}
```

| `code`                 | HTTP | Cuándo                                                       |
|------------------------|------|--------------------------------------------------------------|
| `VALIDATION_ERROR`     | 422  | Body, query o path inválidos. `details` lista `{field, message}`. |
| `CUSTOMER_NOT_FOUND`   | 404  | El cliente no existe.                                         |
| `EMAIL_ALREADY_EXISTS` | 409  | El email ya está registrado.                                  |
| `NOT_FOUND`, `METHOD_NOT_ALLOWED`, … | 4xx | Errores HTTP genéricos (ruta inexistente, método no permitido). |
| `INTERNAL_ERROR`       | 500  | Error inesperado. Nunca expone detalles internos.             |

`GET /health` queda fuera del sobre: responde exactamente `{ "status": "ok" }` para ser consumido por balanceadores y orquestadores.

## 4. Endpoints

### 4.1 `POST /customers` — Crear cliente

Request:

```json
{ "name": "Juan Pérez", "email": "juan@example.com" }
```

| ID    | Criterio de aceptación                                                                 |
|-------|----------------------------------------------------------------------------------------|
| AC-01 | Con datos válidos responde `201 Created` con el cliente creado y `status = PENDING`.    |
| AC-02 | Si el email ya existe (sin importar mayúsculas) responde `409` con código `EMAIL_ALREADY_EXISTS`. |
| AC-03 | Si el email tiene formato inválido responde `422` con código `VALIDATION_ERROR` indicando el campo `email`. |
| AC-04 | Si `name` falta o está vacío responde `422` con código `VALIDATION_ERROR`.              |
| AC-05 | El cliente no puede fijar `status`, `id` ni `created_at` desde el request (`422`).      |

### 4.2 `GET /customers` — Listar clientes (paginado)

Query params:

| Param    | Tipo   | Default | Reglas                         |
|----------|--------|---------|--------------------------------|
| `status` | enum   | —       | Opcional. Filtra por estado.   |
| `search` | string | —       | Opcional, máx. 100 caracteres. Coincidencia parcial, sin distinguir mayúsculas, en `name` o `email`. |
| `page`   | int    | `1`     | `>= 1`                         |
| `size`   | int    | `20`    | `1 – 100`                      |

| ID    | Criterio de aceptación                                                                 |
|-------|----------------------------------------------------------------------------------------|
| AC-06 | Responde `200 OK` con los clientes ordenados del más reciente al más antiguo.           |
| AC-07 | Con `?status=ACTIVE` devuelve únicamente los clientes con ese estado; `meta.total` refleja el filtro. |
| AC-08 | Con un `status` no permitido responde `422`.                                            |
| AC-16 | Devuelve como máximo `size` elementos de la página `page`, con `meta` = `{page, size, total, pages}`. |
| AC-17 | Una página posterior a la última devuelve `data = []` con `meta` correcto.              |
| AC-18 | `page < 1`, `size < 1` o `size > 100` responden `422`.                                  |
| AC-22 | Con `?search=` devuelve los clientes cuyo nombre o email contienen el texto, sin distinguir mayúsculas; se combina con `status`. |
| AC-23 | Los caracteres `%` y `_` en `search` se buscan literalmente (no actúan como comodines). |

### 4.3 `GET /customers/{customer_id}` — Obtener cliente

| ID    | Criterio de aceptación                                                                 |
|-------|----------------------------------------------------------------------------------------|
| AC-09 | Si existe responde `200 OK` con el cliente.                                              |
| AC-10 | Si no existe responde `404` con código `CUSTOMER_NOT_FOUND`.                             |
| AC-11 | Si `customer_id` no es un UUID válido responde `422`.                                    |

### 4.4 `PATCH /customers/{customer_id}/status` — Actualizar estado

Request:

```json
{ "status": "ACTIVE" }
```

| ID    | Criterio de aceptación                                                                 |
|-------|----------------------------------------------------------------------------------------|
| AC-12 | Con un estado permitido responde `200 OK` con el cliente actualizado.                    |
| AC-13 | Con un estado no permitido responde `422`.                                               |
| AC-14 | Si el cliente no existe responde `404` con código `CUSTOMER_NOT_FOUND`.                  |

### 4.5 `GET /health` — Health check

| ID    | Criterio de aceptación                                                                 |
|-------|----------------------------------------------------------------------------------------|
| AC-15 | Responde `200 OK` con `{ "status": "ok" }`.                                              |

### 4.6 `GET /customers/summary` — Resumen para el dashboard

Query params: `days` (int, `7 – 90`, default `14`).

```json
{
  "success": true,
  "data": {
    "total": 29,
    "by_status": { "ACTIVE": 15, "PENDING": 10, "BLOCKED": 4 },
    "registrations": [{ "date": "2026-10-12", "count": 0 }, { "date": "2026-10-13", "count": 3 }]
  }
}
```

| ID    | Criterio de aceptación                                                                 |
|-------|----------------------------------------------------------------------------------------|
| AC-25 | `total` y `by_status` reflejan a todos los clientes; los tres estados aparecen siempre, aunque tengan 0. |
| AC-26 | `registrations` contiene exactamente `days` días consecutivos (en UTC) que terminan hoy, ordenados del más antiguo al más reciente, con 0 en los días sin altas. |
| AC-27 | `days` fuera de `7 – 90` responde `422`.                                                 |

## 5. Comportamiento transversal

| ID    | Criterio de aceptación                                                                 |
|-------|----------------------------------------------------------------------------------------|
| AC-19 | Una ruta inexistente responde `404` con el sobre de error y código `NOT_FOUND`.          |
| AC-20 | Un error inesperado responde `500` con código `INTERNAL_ERROR` sin exponer detalles internos, y se registra en el log con su traza. |
| AC-21 | Toda respuesta incluye el header `X-Request-ID`. Si el cliente envía uno válido se reutiliza; si no, se genera. |
| AC-24 | CORS: en desarrollo se acepta cualquier puerto de `localhost` / `127.0.0.1`; cualquier otro origen se rechaza salvo que esté en `CORS_ORIGINS`. El header `X-Request-ID` queda expuesto al navegador. |

### Logging

- Cada petición genera una línea de log con método, ruta, status y duración en ms.
- Todas las líneas de log de una petición incluyen su `request_id` para poder correlacionarlas.
- Los eventos de negocio (cliente creado, estado actualizado) se registran en nivel `INFO`.
- Las violaciones de reglas de negocio se registran en `WARNING`; los errores inesperados en `ERROR` con traza.
- No se registran datos personales (nombre, email) en los logs: solo identificadores.
- El nivel es configurable con `LOG_LEVEL`.

### Conexión a base de datos

- Existe una única instancia de `Engine` (y de su pool de conexiones) por proceso, creada de forma perezosa y thread-safe.
- Cada petición obtiene su propia `Session`, que se cierra al terminar la petición.
- El pool se libera al apagar la aplicación.

## 6. Fuera de alcance

- Autenticación/autorización.
- Reglas de transición entre estados (cualquier estado permitido puede asignarse).
