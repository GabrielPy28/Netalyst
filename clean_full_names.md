### Regla general de nombres

Actualmente cuento con una base de datos que contiene una lista de creadores de contenido junto con sus plataformas principales. El problema recurrente es la falta de estandarización en el campo `full_name`, lo que dificulta la correcta identificación del nombre real de cada creador y afecta la calidad de las comunicaciones personalizadas.

Entre las inconsistencias más frecuentes se encuentran:

- Uso de nombres incompletos en las cuentas, aunque el nombre completo suele aparecer en la dirección de correo electrónico.
- Inclusión de emojis, signos gramaticales o términos previos al nombre (ej. `Dr.`, `Chef`, `Mr.`, `Mrs.`, `Miss`, `Beby`, `Hot`, `Official`, `Ing.`, `The`, `Come`, `Hello I'm`, `Hey`, `This is`, `Actrice`, `Couch`, `Designer`, `Mg.`, `Lic.`, etc.).
- Escritura en mayúsculas sostenidas.
- Uso del nombre real únicamente en campos alternativos como biografía de perfil, nombre de usuario (ej. `TheOfficialStevenSegler`) o dominio de correo electrónico (ej. `partners@andersonsmith.com`), donde a veces se infiere el nombre (`andersonsmith`).

Esta heterogeneidad genera una columna `full_name` con datos poco confiables, lo que impide extraer de forma consistente el `first_name` del creador y limita la efectividad de las comunicaciones directas.

Ante esto, me gustaría:

1. Normalizar y limpiar automáticamente los valores del campo `full_name`.
2. Extraer de manera confiable el nombre real del creador (especialmente el `first_name`) a partir de múltiples fuentes disponibles (correo, username, dominio, biografía, etc.).
3. Manejar los distintos patrones de suciedad descritos y ofrecer una salida estructurada y estandarizada.

El flujo seria el siguiente: 
- Se parte de `full_name`
- Se limpia emoji/ruido, se normalizan espacios y se aplican reglas para detectar:
  - nombres validos,
  - bios o frases comerciales,
  - marcas,
  - casos con prefijos/titulos (`dr`, `mr`, `chef`, etc.).

### Limpieza extra (casos reales)
Antes de decidir si un nombre es usable, se recomienda limpiar:
- emojis y símbolos decorativos: `❤️SAS❤️`, `🔵Camille`
- signos repetidos o ruido al inicio: `!! Jennifer`, `...Alex`
- unicode “small caps” / estilos: `ᴄᴀʀɪɴᴇ-ᴀɴɴᴇ`
- separadores raros y guiones: `carine-anne`, `carine_anne`

Si tras limpiar el resultado sigue pareciendo bio/marca o queda vacío, aplicar fallback a `@username`.

### Casos adicionales (nombres que no son persona)
Aunque `fullName` venga relleno, conviene forzar fallback `@username` cuando:
- el primer token es **solo una inicial** seguida de apodo/marca (ej. `J Mist Official`).
- el nombre empieza como **titular de marca o frase** (ej. `Home of Angry Pikachu BTS`, `Its All That Jazz`).
- el primer token parece **usuario / handle mezclado con símbolos** (ej. `icm_triplets *…`).
- el nombre es claramente **título + apodo** tipo `Mr. Jalapeño` (no nombre legal reconocible).
- se conservan nombres que parecen **persona real** con 2+ tokens razonables (ej. `Destiny Monique Arredondo`, `Ko Hyojoo`).

## 4.1) `vertical` desde `biography` (Instagram) + `businessCategoryName`

Cuando el Excel no trae `vertical`, se puede inferir de `biography`:
- líneas con separadores `|`, `+` o `/` → temas en minúsculas, formato `a, b and c` (o `a and b` si son dos).
- si la bio es larga o ambigua, extraer palabras clave (ej. travel, fitness, lifestyle, fashion, beauty, luxury, ugc, wellness, outdoors).
- si no hay señal clara, usar `businessCategoryName` con las mismas reglas que `format_vertical_custom`, **eliminando** la palabra `None` y dejando todo en **minúsculas**.
- si aun asi queda vacio, usar `digital creator` como valor por defecto operativo.

## 4.2) Emails y links desde Instagram `biography` / `externalUrls` (nuevo)

Cuando el Excel no trae email, se puede extraer desde el texto de `biography` con regex.
Ejemplo:

```text
"biography": "🇰🇷🇨🇦🇺🇸 \n... \nbaeverlyheels@abouttalentagency.com"
```

Email detectado: `baeverlyheels@abouttalentagency.com`

Adicionalmente, desde `externalUrls` se pueden capturar links a:
- TikTok (`tiktok_url` y `tiktok_handle` desde `https://www.tiktok.com/@...`)
- Facebook (`facebook_url`)
- YouTube (`youtube_channel`)

### Fallbacks importantes
- Si el nombre viene vacio, invalido o parece bio/marca, se usa fallback con username:
  - `full_name = @username`
  - `first_name = @username`
- Si parece nombre real:
  - `full_name` se deja en formato display limpio.
  - `first_name` se toma del primer token limpio.
