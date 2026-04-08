# Cambios recientes y resultados esperados

Este documento resume mejoras aplicadas al proyecto (backend, frontend, proxy) y qué comportamiento deberías observar al usarlas.

---

## 1. Columnas de identidad en exportaciones (`picture`, `username`, `max_followers`, `main_platform`, `category`)

### Problema
En archivos finales a veces aparecían vacíos o incoherentes respecto a las columnas `instagram_*` / `tiktok_*` / `youtube_*`.

### Cambios
- **Conteo de seguidores unificado**: se usan los mismos alias (`ig_followers` / `instagram_followers`, etc.) al elegir la red principal y al calcular el score, para no desincronizar si faltan columnas `ig_*`.
- **Sincronización tras el score** (`sync_identity_columns_from_creator_main_platform`): se rellenan `main_platform` (Instagram / Tiktok / Youtube), `username`, `picture`, `max_followers`, `vertical` y `category` alineados con `creator_main_platform`, con normalización de valores inválidos en esa columna y misma lógica de categoría que el paso de identidad principal.

### Resultado esperado
- `picture` y `username` corresponden a la **cuenta principal** (la de más seguidores según los datos coalescidos).
- `max_followers` refleja el **máximo coherente** con esa cuenta (no un valor vieño del Excel si el pipeline ya calculó otro).
- `main_platform` con capitalización acordada (**Instagram**, **Tiktok**, **Youtube**).
- `category` alineada con la lógica de vertical de la red principal.

**Archivos principales**: `backend/app/utils/social_account_steps.py`, `backend/app/utils/social_creator_scoring.py`.

---

## 2. Validaciones muy largas (varias horas)

### Problema
Una sola conexión HTTP abierta (SSE o upload) suele cortarse por timeouts de proxy (~1 h), inadecuado para listas enormes (4–6+ h).

### Cambios
- **API asíncrona**: `POST /api/v1/validation/jobs` (202) con `response_mode=json|zip`; el cliente hace **polling** con `GET /api/v1/validation/jobs/{job_id}` hasta `complete` o `error`. Para ZIP: `GET .../jobs/{job_id}/download` cuando `download_ready` es verdadero.
- **Frontend**: la validación con progreso y la descarga ZIP usan este flujo (peticiones cortas repetidas en lugar de un stream de horas).
- **Nginx** (plantilla del front que hace proxy al API): `proxy_read_timeout` y `proxy_send_timeout` elevados (~7 h) por si aún se usa SSE u otras rutas largas.

### Variables de entorno (opcionales)
| Variable | Default | Uso |
|----------|---------|-----|
| `VALIDATION_ASYNC_MAX_CONCURRENT` | 5 | Máximo de validaciones simultáneas en el servidor |
| `VALIDATION_JOB_EVENTS_TAIL_MAX` | 100 | Tamaño del historial de eventos por job |
| `VALIDATION_JOB_MAX_AGE_HOURS` | 48 | Limpieza de jobs terminados en memoria |
| `VALIDATION_JOB_POLL_INTERVAL_SECONDS` | 2.5 | Intervalo sugerido de polling (también lo devuelve el 202) |

### Resultado esperado
- La UI puede seguir una corrida de muchas horas **sin depender de una sola conexión larga**.
- **Limitación**: los jobs están **en memoria** en el proceso; un redeploy o reinicio del servicio los pierde (hay que volver a lanzar la validación).

**Archivos principales**: `backend/app/services/validation_jobs.py`, `backend/app/api/routers/validation.py`, `backend/app/schemas/validation.py`, `backend/app/core/config.py`, `frontend/src/api/validation.ts`, `frontend/nginx/templates/default.conf.template`.

---

## 3. Instagram: varias URLs por run de Apify

### Problema
Se lanzaba **un run de Apify por perfil** (`directUrls` con una sola URL).

### Cambios
- Lotes de URLs en un solo `directUrls`, con `resultsLimit` acotado según el tamaño del lote.
- Agregación de items del dataset (posts) **por autor** para reconstruir perfil + engagement por URL/handle.
- Configuración: `INSTAGRAM_APIFY_BATCH_SIZE` (default 35), `INSTAGRAM_APIFY_BATCH_RESULTS_LIMIT_CAP` (default 8000).

### Resultado esperado
- **Menos runs y menos tiempo de cola** en Apify para listas grandes; mismo tipo de columnas `instagram_*` / `ig_*` que antes.
- Si un actor personalizado no soporta lotes: `INSTAGRAM_APIFY_BATCH_SIZE=1`.

**Archivos principales**: `backend/app/utils/instagram_profile.py`, `backend/app/utils/social_account_steps.py`, `backend/app/core/config.py`.

---

## 4. TikTok: varios perfiles por run de Apify

### Problema
Misma idea que Instagram: un run por usuario pese a que el input admite `profiles: [...]`.

### Cambios
- Un run con varios handles en `profiles`, `resultsPerPage` acotado según el lote.
- Agrupación de filas del dataset por autor (`authorMeta`, etc.) y agregación por usuario.
- Configuración: `TIKTOK_APIFY_BATCH_SIZE` (default 35), `TIKTOK_APIFY_RESULTS_PER_PAGE_CAP` (default 5000).

### Resultado esperado
- Menos invocaciones al actor para la misma lista; columnas `tiktok_*` / `tt_*` coherentes.
- Si hiciera falta: `TIKTOK_APIFY_BATCH_SIZE=1`.

**Archivos principales**: `backend/app/utils/tiktok_profile.py`, `backend/app/utils/social_account_steps.py`, `backend/app/core/config.py`.

---

## 5. Limpieza de nombres (`name_cleaning`)

### Casos cubiertos

| Situación | Comportamiento esperado |
|-----------|-------------------------|
| Frase marca **“Epic World”** (según lista interna) | `full_name` y `first_name` = **`@handle`** (p. ej. `@epicworld.travel`); se toma handle de `username`, `instagram_username` o `tiktok_username`. |
| Frase basura **“Bad Child”** + handle tipo `aaroncmoten` | Reconstrucción: **Aaron / Cmoten / Aaron Cmoten** (partiendo el handle con prefijos de nombres comunes o camelCase). |
| Nombre pegado **Danielnunomx** (un solo token) | **Daniel / Nunomx / Daniel Nunomx**. |
| `full_name` vacío o guión (—) pero `first_name` + `last_name` válidos | Se compone el texto a parsear desde esas columnas antes que email/bio. |
| `full_name` placeholder + `ig_full_name_raw` | Se puede preferir el nombre de Instagram cuando corresponda. |

### Listas editables (en código)
- `_BRAND_PHRASES_USE_AT_USERNAME`: frases que fuerzan uso de `@handle`.
- `_GARBAGE_PHRASES_TRY_HANDLE_SPLIT`: frases que disparan el split del handle.
- `_COMMON_FIRST_NAMES_RAW`: prefijos para handles pegados en minúsculas.

### Resultado esperado
- Menos filas con nombres claramente falsos o genéricos mal partidos por `HumanName`.
- Cuentas tipo marca con nombre “Epic World” pasan a mostrar el **@ del perfil** en nombre visible.

**Archivo principal**: `backend/app/utils/name_cleaning.py`.

---

## 6. Notas de UI

- En validación, el aviso de listas largas indica que el trabajo corre en segundo plano y conviene **mantener la pestaña abierta** hasta terminar.

**Archivo**: `frontend/src/components/validation/ValidationFlowNotes.tsx`.

---

## Cómo verificar rápidamente

1. **Identidad / export**: ejecutar un programa con criterio de redes y comprobar columnas agregadas vs. `instagram_*` en un caso con IG dominante.
2. **Jobs largos**: subir lista grande, confirmar que el progreso avanza por polling y que al final hay resultado o ZIP.
3. **Apify**: revisar en consola de Apify **menos runs** por lote en IG/TT para la misma N de perfiles.
4. **Nombres**: filas de prueba con “Bad Child” + `aaroncmoten`, “Epic World” + `epicworld.travel`, y `Danielnunomx` en `full_name`.

---

*Documento generado para acompañar el estado del repo tras las mejoras descritas; ajústalo si añades criterios o variables nuevas.*
