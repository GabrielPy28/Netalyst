-- Ejemplo: Creator Fast Track + criterio first_name + pasos.
-- Ejecutar después de schema.sql. Si ya existen datos, ajusta o borra antes.

insert into programs (nombre, brand, descripcion, is_active)
values (
    'Creator Fast Track',
    'Meta',
    'Validación de creadores para programa Creator Fast Track de Meta.',
    true
);

insert into criteria (program_id, nombre, objetivo, orden)
select id, 'first_name limpio y nombre válido',
       'Validar y normalizar first_name a partir de full_name, email, username y bio.',
       1
from programs
where nombre = 'Creator Fast Track'
order by created_at desc
limit 1;

insert into criterion_steps (criterion_id, paso_num, nombre, definicion, funcion_a_ejecutar)
select c.id, s.paso_num, s.nombre, s.definicion, s.funcion
from criteria c
join programs p on p.id = c.program_id
cross join (values
    (1, 'Obtener columnas de trabajo',
     'Validar columnas full_name, first_name, email, username e instagram_bio.',
     'load_creator_columns'),
    (2, 'Extraer la mejor fuente de nombre',
     'Decidir la fuente más confiable antes de parsear.',
     'extract_best_name_source'),
    (3, 'Aplicar parser de nombres',
     'Normalizar y parsear para first_name.',
     'apply_name_parser'),
    (4, 'Procesar la lista completa',
     'Transformaciones finales sobre el DataFrame del criterio.',
     'process_full_dataframe')
) as s(paso_num, nombre, definicion, funcion)
where p.nombre = 'Creator Fast Track'
  and c.nombre = 'first_name limpio y nombre válido';
