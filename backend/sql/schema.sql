-- Netalyst: programas → criterios → pasos (PostgreSQL / Supabase)
-- Opcional: la API también crea estas tablas al arrancar (SQLAlchemy create_all)
-- si DATABASE_URL está definida. Usa este script si prefieres DDL explícito o triggers.

create extension if not exists "pgcrypto";

create table if not exists programs (
    id uuid primary key default gen_random_uuid(),
    nombre text not null,
    brand text,
    image_brand_url text,
    descripcion text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists criteria (
    id uuid primary key default gen_random_uuid(),
    program_id uuid not null references programs (id) on delete cascade,
    nombre text not null,
    objetivo text,
    template_slug text,
    orden int not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_criteria_program on criteria (program_id);

create table if not exists criterion_steps (
    id uuid primary key default gen_random_uuid(),
    criterion_id uuid not null references criteria (id) on delete cascade,
    paso_num int not null,
    nombre text not null,
    definicion text,
    funcion_a_ejecutar text not null,
    created_at timestamptz not null default now(),
    unique (criterion_id, paso_num)
);

create index if not exists idx_criterion_steps_criterion on criterion_steps (criterion_id);

comment on table programs is 'Programa u oportunidad (cabecera de validación)';
comment on table criteria is 'Criterio de limpieza / validación (1:N con programa)';
comment on table criterion_steps is 'Pasos ejecutables en orden (funcion_a_ejecutar = clave en registro Python)';
