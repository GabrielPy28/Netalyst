-- Criterio: validación de emails (patrones + Hunter). Debe ser el ÚLTIMO criterio del programa (orden más alto).
-- Sustituye :program_id por el UUID de tu programa en programs.
--
-- Requiere en .env: HUNTER_API_KEY (y opcionalmente HUNTER_MAX_CALLS_PER_RUN, HUNTER_MIN_SCORE, HUNTER_REQUEST_DELAY_SECONDS).

-- insert into criteria (program_id, nombre, objetivo, orden)
-- values (
--   ':program_id'::uuid,
--   'Email y verificación Hunter',
--   'Marcar patrones institucionales/comerciales; verificar emails limpios con Hunter.io (score ≥ 88, status valid o accept_all).',
--   99
-- );

-- insert into criterion_steps (criterion_id, paso_num, nombre, definicion, funcion_a_ejecutar)
-- select id, 1,
--   'Patrones en email',
--   'Marca email_pattern_flag sin eliminar filas.',
--   'screen_email_patterns'
-- from criteria where program_id = ':program_id'::uuid and nombre = 'Email y verificación Hunter';

-- insert into criterion_steps (criterion_id, paso_num, nombre, definicion, funcion_a_ejecutar)
-- select id, 2,
--   'Hunter Email Verifier',
--   'Una petición por email válido; columnas hunter_* y email_hunter_passed.',
--   'hunter_verify_emails'
-- from criteria where program_id = ':program_id'::uuid and nombre = 'Email y verificación Hunter';
