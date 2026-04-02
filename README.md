# Netalyst — Validación y limpieza de creadores

Plataforma **La Neta** para cargar listas de creadores (CSV/Excel), ejecutar **flujos de validación** por **programa** (oportunidad), enriquecer datos de **redes sociales** (Instagram, TikTok, YouTube, Facebook), puntuar perfiles y separar **creadores válidos** vs **excluidos**, con exportación a Excel.

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, integraciones (Supabase auth, Apify, Hunter.io, YouTube Data API, etc.).
- **Frontend:** React, Vite, TypeScript.

---

## Programas y oportunidades

En el modelo de datos, un **programa** (`programs`) es el contenedor de una **oportunidad** de validación: tiene nombre, descripción opcional, marca, imagen, estado activo/inactivo y una lista ordenada de **criterios**.

- **Crear programa vacío:** `POST /api/v1/programs` con datos de cabecera.
- **Crear programa con flujo desde plantillas:** `POST /api/v1/programs/from-flow` enviando `nombre`, `descripcion`, etc. y **`criterio_slugs`**: una lista ordenada de identificadores del catálogo (ver tabla abajo). El orden de la lista es el **orden de ejecución** de los criterios en el pipeline.
- **Sustituir todo el flujo** de un programa existente: `PUT /api/v1/programs/{id}/flow` con un nuevo arreglo `criterio_slugs` (se borran los criterios anteriores y se vuelven a crear desde el catálogo).
- **Editar solo la cabecera** (nombre, descripción, activo…): `PATCH /api/v1/programs/{id}`.

En la interfaz web, la gestión de programas y el armado del flujo suelen hacerse desde las pantallas de **Programas** y **detalle / flujo del programa**, consumiendo el **catálogo de criterios** (`GET /api/v1/programs/criterion-catalog`).

---

## ¿Qué es un criterio?

Un **criterio** (`criteria`) es un **bloque lógico** dentro de un programa: representa una **etapa** del proceso (por ejemplo “Redes y score”, “Limpieza de nombres”, “Email Hunter”).

Cada criterio tiene:

| Campo | Descripción |
|--------|-------------|
| **nombre** | Título visible del bloque. |
| **objetivo** | Descripción de qué se persigue en esa etapa. |
| **orden** | Entero: posición del criterio en el pipeline global del programa (`1`, `2`, `3`…). Se ejecutan en ese orden. |
| **template_slug** | Si el criterio se creó desde el catálogo, guarda el slug de la plantilla (p. ej. `redes_puntaje_y_filtros`). |
| **steps** | Lista de **pasos** que se ejecutan **dentro** de ese criterio, en orden de `paso_num`. |

Los criterios se generan a partir de **plantillas** definidas en código (`backend/app/constants/criterion_catalog.py`). No se “programan” a mano fila a fila en la API salvo extensiones futuras: se elige **qué plantillas** incluir y en **qué orden**.

---

## ¿Qué es un paso?

Un **paso** (`criterion_steps`) es la **unidad mínima ejecutable**: una función Python registrada en el backend que recibe el contexto de validación (DataFrame, logs, caché del pipeline) y devuelve el contexto actualizado.

Cada paso tiene:

| Campo | Descripción |
|--------|-------------|
| **paso_num** | Orden dentro del criterio (`1`, `2`, `3`…). |
| **nombre** | Título corto del paso (para UI y logs). |
| **definicion** | Texto explicativo de qué hace. |
| **funcion_a_ejecutar** | Nombre clave que enlaza con el código: debe existir en `STEP_REGISTRY` (`backend/app/utils/step_registry.py`). |

Ejemplos de `funcion_a_ejecutar`: `fetch_instagram_profiles`, `compute_creator_social_score`, `gate_social_followers_and_min_score`, `hunter_verify_emails`, etc.

**Regla importante:** el motor de validación recorre **primero todos los criterios por `orden`**, y dentro de cada uno **todos los pasos por `paso_num`**. Un paso que falle o excluya filas puede afectar filas que luego ya no pasan a criterios posteriores (según la lógica de cada función).

---

## Catálogo de plantillas (`criterio_slugs`)

Al armar el flujo (`criterio_slugs`), solo son válidos los slugs definidos en el catálogo. Los actuales son:

| Slug | Nombre (resumen) |
|------|-------------------|
| `redes_puntaje_y_filtros` | Redes (IG/TT/YT), identidad, score 0–16, sync con `creator_main_platform`, filtro por seguidores y puntaje. |
| `facebook_reels` | Consulta página Facebook / Reels y exclusión por actividad reciente. |
| `limpieza_nombres` | Normalización de `full_name` / `first_name` con reglas y nameparser. |
| `email_hunter` | Patrones de email, verificación Hunter.io y exclusión de no válidos. |

Cada plantilla incluye en código los campos **entrega_usuario** y **salida_esperada** (qué columnas debe traer el archivo y qué columnas o efectos produce). Úsalos como guía al preparar el CSV/Excel.

**Programas ya existentes:** si añades pasos nuevos en el catálogo (p. ej. un paso extra en `redes_puntaje_y_filtros`), los programas creados **antes** no se actualizan solos. Hay que **volver a guardar el flujo** con `PUT .../flow` (o recrear el programa desde flujo) para regenerar criterios y pasos desde las plantillas actuales.

---

## Configuración técnica (resumen)

1. **Variables de entorno:** ver `backend/app/core/config.py` y un `.env` en la raíz o en `backend/` (p. ej. `DATABASE_URL`, Supabase, `JWT_SECRET`, Apify, Hunter, YouTube API, etc.).
2. **Base de datos:** PostgreSQL; al arrancar la API se crean tablas si no existen (`init_db_schema`).
3. **Ejecución local:** en la raíz del repo, `docker compose up` (servicios `api` y `web` según `compose.yaml`).
4. **Validación:** `POST /api/v1/validation/upload-stream` (SSE con progreso) o `POST /api/v1/validation/upload` (JSON o ZIP).

Para despliegue (Railway, Vercel, etc.) puedes seguir la guía que comentaste en el equipo: backend con URL pública y frontend con `VITE_API_BASE` apuntando a `https://<tu-api>/api/v1`.

---

## Documentación de negocio en el repo

Encontrarás criterios detallados en Markdown en la raíz (p. ej. criterios de Instagram, TikTok, YouTube, nombres) que alinean las reglas con los pasos implementados.

---

## Licencia y uso

Uso interno / La Neta salvo que el repositorio indique otra licencia explícitamente.
