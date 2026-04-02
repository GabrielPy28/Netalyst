# Automatisation Clean 
> Esta herrmeinta sera una plataforma de servicio dsponible para que el equipo pueda llevar a cabo la limpieza y validación de lso creadores en función de criterios pre-establecidos para cada Oportunidad o programa activo dentro de la empresa, 

## Stack Tecnologico:
> Dicha herramienta estara construido sobre las siguientes herramientas y lenguajes de programa:

- ### **Back-End**: 
    - #### **Python**:
        - ##### **FastApi**: 
        > utilizar APIRouter para arquitectura modular y codigo limpio para que cada servicio tenga su propia carpeta "independiente", python-dotenv para el manejo de variables de entorno, pandas para el manejo de dataframes, openpyxl para el manejo de archivos xlsx, pillow para el manejo de imagenes, python-nameparser para limpieza de nombres (paso critico y requerido en más de un oportunidad o programa) ver [clean_full_name.md](./clean_full_names.md), GLiClass + instaloader  para exclusión por categoria en función de los datos en la biography del creador + business_category_name (Otro paso critico y requerido en la validación en más de una oportunidad o porgrama, hay que escluir cuantas que no son creadores d econtenido individuales: Marcas (Hotwheels, Matel, Barby, Ilumination, Marvel, Universal, etc..), equipos de footboll, cuentas de estados (Arizona, Miami, New York, etc..), universidades, Church, School, University, Foundation, Association, Ministry, Department, Government, cuentas de comida rapida (McDonadls - New Jersey), cuentas de tiendas en line (en su biografia aparece shop, retails, buy, reserve, make a order, Store, Boutique, Deals, etc...), cuentas de famosos (Max Verstappen, Adan Sandler, Ryan Reinolds, etc...), cuentas de hoteles, resorts y restaurantes, cuentas de politicos,  FC, NFL, NBA, MLB, NHL, Athletics, Warriors, Eagles, Raiders, Patriots, Football, Soccer, Basketball + nombre de ciudad o equipo, Corp, Inc, LLC, Group (cuando aparece solo, sin nombre de persona)), JWT-Token para autorizacion, entre otras herramientas que se pueden ir agregando durante el desarrollo e integración continua...

- ### **Front-End**:
    - #### **Node**: 
        - ##### **React**:
        > react-icons para iconos, Tailwind Css para el framewrok de estilos, sweetalert2 para manejo de notificaciones y alertas, framer-motion para website builder, animaciones y estilos visuales, React Select para inputs de tipo listas y listas de opción multiple, shadcn@latest para animaciones y mejor presentación, tabla de colores (--purple: #6641ed; --blue: #79bcf7; --pink: #ff47ac; --dark: #0f172a; --white: #F8FAFC, green: #31C950, yellowe: #FFDF20; red. #E7180B)

- ### **Data Base**: 
    - #### **Supabase**: 
        - ##### **DataBase Url**: 
        > "postgresql+psycopg2://postgres.zosovsdepfdrbdvjhfyt:Jeremias11_29@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    - #### **Autorization**:
        - ##### **Supabase URL**: 
        > https://cmmmkmwjvhgtjoktneqa.supabase.co
        - ##### **Supabase Public API KAY**:
        > "sb_publishable_oGUqnPKqg_ZqUHtZNOQHkA_Enh6nK6z"
        - ##### **SUPABASE_SECRET_KEY**:
        > "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNtbW1rbXdqdmhndGpva3RuZXFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxNDMyNiwiZXhwIjoyMDc3NDkwMzI2fQ.IL1XuRlIgfjKVBcgqq2p7A3IVdTvn3bbXXJdszjFa2Y"
        > ve [auth.py](./auth.py)

- ### **Conteneriacion**
    - #### **Docker**: la estrategia principal es utilizar imágenes base "slim" o "alpine" y la técnica de Multistage Builds.
        - ##### **Levantar**:
            - **Back-End**
            - **Front-End**

```
email	first_name	last_name	full_name	picture	username	instagram_url	tiktok_url	youtube_channel_url	instagram_username	tiktok_username	youtube_channel	category	facebook_page	personalized_paragraph	max_followers	main_platform	status	instagram_followers	instagram_post_count	instagram_picture	instagram_bio	instagram_category	instagram_verified	tiktok_followers	tiktok_post_count	tiktok_picture	tiktok_bio	tiktok_category	tiktok_verified	youtube_followers	youtube_post_count	youtube_picture	youtube_bio	youtube_category	youtube_verified
```