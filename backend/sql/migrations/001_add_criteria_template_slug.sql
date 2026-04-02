-- Ejecutar una vez en bases ya creadas antes de template_slug.
alter table criteria add column if not exists template_slug text;
