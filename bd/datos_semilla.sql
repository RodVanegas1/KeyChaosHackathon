-- ============================================================
-- Mora Preventiva / Conversational Demo - MySQL
-- Datos semilla (seed data) para V1
-- Ejecutar DESPUÉS de mora_demo_v1.sql
-- ============================================================

USE mora_demo;

-- ------------------------------------------------------------
-- 1. Usuarios (5 perfiles distintos)
-- ------------------------------------------------------------
INSERT INTO usuario (id, nombre, telefono, email, created_at) VALUES
(1, 'Carlos Menjívar',   '+50370111222', 'carlos.menjivar@example.com',   '2025-11-02 09:15:00'),
(2, 'Ana Beatriz Flores','+50370222333', 'ana.flores@example.com',        '2025-10-20 14:32:00'),
(3, 'Jose Luis Ramírez', '+50370333444', 'joseluis.ramirez@example.com',  '2025-09-05 08:00:00'),
(4, 'María Elena Torres','+50370444555', 'maria.torres@example.com',      '2026-01-10 11:45:00'),
(5, 'Roberto Alfaro',    '+50370555666', NULL,                             '2025-12-18 16:20:00');

-- Perfiles:
-- 1. Carlos     -> riesgo ALTO, aumentando, ejemplo del documento (compromiso obtenido)
-- 2. Ana        -> riesgo MEDIO, estable, buen historial reciente
-- 3. Jose Luis  -> riesgo ALTO, historial de pagos tardíos recurrente, no responde
-- 4. María      -> riesgo BAJO, cliente puntual, sin necesidad de contacto
-- 5. Roberto    -> riesgo ALTO, disminuyendo, ya se comprometió y cumplió antes

-- ------------------------------------------------------------
-- 2. Créditos
-- ------------------------------------------------------------
INSERT INTO credito (id, usuario_id, monto_original, saldo_pendiente, fecha_inicio, fecha_vencimiento, estado, created_at) VALUES
(1, 1, 1000.00, 850.00, '2026-03-01', '2026-09-17', 'ACTIVO', '2026-03-01 10:00:00'),
(2, 2, 1500.00, 620.00, '2025-12-01', '2026-09-25', 'ACTIVO', '2025-12-01 09:30:00'),
(3, 3, 2000.00, 1780.00, '2026-01-15', '2026-09-14', 'ACTIVO', '2026-01-15 12:00:00'),
(4, 4, 900.00, 150.00, '2025-11-10', '2026-10-05', 'ACTIVO', '2025-11-10 08:20:00'),
(5, 5, 1200.00, 400.00, '2026-02-20', '2026-09-16', 'ACTIVO', '2026-02-20 15:10:00');

-- ------------------------------------------------------------
-- 3. Pagos históricos
-- ------------------------------------------------------------
-- Carlos (credito 1): un par de retrasos recientes
INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(1, '2026-06-17', '2026-06-17', 150.00, 150.00, 'PAGADO'),
(1, '2026-07-17', '2026-07-20', 150.00, 150.00, 'TARDIO'),
(1, '2026-08-17', '2026-08-22', 150.00, 150.00, 'TARDIO');

-- Ana (credito 2): historial mayormente puntual, un solo atraso leve
INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(2, '2026-06-25', '2026-06-25', 220.00, 220.00, 'PAGADO'),
(2, '2026-07-25', '2026-07-26', 220.00, 220.00, 'TARDIO'),
(2, '2026-08-25', '2026-08-25', 220.00, 220.00, 'PAGADO');

-- Jose Luis (credito 3): patrón crónico de atrasos e incumplimientos
INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(3, '2026-06-14', '2026-06-25', 250.00, 250.00, 'TARDIO'),
(3, '2026-07-14', '2026-07-30', 250.00, 200.00, 'PARCIAL'),
(3, '2026-08-14', NULL,          250.00, NULL,   'INCUMPLIDO');

-- María (credito 4): cliente puntual, sin atrasos
INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(4, '2026-07-05', '2026-07-05', 125.00, 125.00, 'PAGADO'),
(4, '2026-08-05', '2026-08-05', 125.00, 125.00, 'PAGADO'),
(4, '2026-09-05', '2026-09-05', 125.00, 125.00, 'PAGADO');

-- Roberto (credito 5): tuvo un atraso, pero mejoró tras compromiso anterior
INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(5, '2026-06-16', '2026-06-28', 200.00, 200.00, 'TARDIO'),
(5, '2026-07-16', '2026-07-16', 200.00, 200.00, 'PAGADO'),
(5, '2026-08-16', '2026-08-16', 200.00, 200.00, 'PAGADO');

-- ------------------------------------------------------------
-- 4. Evaluaciones de riesgo (evolución en el tiempo)
-- ------------------------------------------------------------
-- Carlos: riesgo escalando (coincide con el ejemplo del documento)
INSERT INTO evaluacion_riesgo
  (credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(1, 42.00, 0.4200, 'MEDIO', 8, 0.3333, 3.50, 2, 'AUMENTANDO', 'v1', '2026-09-08 07:00:00'),
(1, 57.00, 0.5700, 'MEDIO', 6, 0.3333, 3.50, 2, 'AUMENTANDO', 'v1', '2026-09-10 07:00:00'),
(1, 71.00, 0.7100, 'ALTO',  4, 0.6667, 4.00, 2, 'AUMENTANDO', 'v1', '2026-09-11 07:00:00'),
(1, 84.00, 0.8400, 'ALTO',  1, 0.6667, 4.00, 2, 'AUMENTANDO', 'v1', '2026-09-12 07:00:00');

-- Ana: riesgo medio, estable
INSERT INTO evaluacion_riesgo
  (credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(2, 38.00, 0.3800, 'MEDIO', 13, 0.3333, 1.00, 1, 'ESTABLE', 'v1', '2026-09-10 07:00:00'),
(2, 40.00, 0.4000, 'MEDIO', 12, 0.3333, 1.00, 1, 'ESTABLE', 'v1', '2026-09-12 07:00:00');

-- Jose Luis: riesgo alto, incumplimiento reciente
INSERT INTO evaluacion_riesgo
  (credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(3, 65.00, 0.6500, 'ALTO', 5, 0.6667, 12.00, 3, 'AUMENTANDO', 'v1', '2026-09-09 07:00:00'),
(3, 89.00, 0.8900, 'ALTO', 2, 1.0000, 15.00, 3, 'AUMENTANDO', 'v1', '2026-09-12 07:00:00');

-- María: riesgo bajo
INSERT INTO evaluacion_riesgo
  (credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(4, 8.00, 0.0800, 'BAJO', 23, 0.0000, 0.00, 0, 'ESTABLE', 'v1', '2026-09-12 07:00:00');

-- Roberto: riesgo alto pero disminuyendo
INSERT INTO evaluacion_riesgo
  (credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(5, 78.00, 0.7800, 'ALTO', 10, 0.3333, 12.00, 1, 'DISMINUYENDO', 'v1', '2026-09-05 07:00:00'),
(5, 66.00, 0.6600, 'ALTO', 4,  0.3333, 12.00, 1, 'DISMINUYENDO', 'v1', '2026-09-12 07:00:00');

-- ------------------------------------------------------------
-- 5. Conversaciones
-- ------------------------------------------------------------
-- Carlos: conversación completada con compromiso (ejemplo del documento)
INSERT INTO conversacion (id, usuario_id, credito_id, canal, estado, started_at, ended_at) VALUES
(1, 1, 1, 'WHATSAPP', 'COMPLETADA', '2026-09-12 09:00:00', '2026-09-12 09:04:00');

-- Ana: aún no se contacta (riesgo medio, no cruza el umbral todavía) -> sin conversación

-- Jose Luis: conversación fallida, el usuario no respondió
INSERT INTO conversacion (id, usuario_id, credito_id, canal, estado, started_at, ended_at) VALUES
(2, 3, 3, 'WHATSAPP', 'FALLIDA', '2026-09-12 10:00:00', '2026-09-12 10:00:00');

-- María: no aplica contacto (riesgo bajo) -> sin conversación

-- Roberto: conversación previa completada, compromiso ya cumplido
INSERT INTO conversacion (id, usuario_id, credito_id, canal, estado, started_at, ended_at) VALUES
(3, 5, 5, 'WHATSAPP', 'COMPLETADA', '2026-09-05 11:00:00', '2026-09-05 11:06:00');

-- ------------------------------------------------------------
-- 6. Mensajes
-- ------------------------------------------------------------
-- Conversación 1: Carlos (coincide con el ejemplo del documento)
INSERT INTO mensaje (conversacion_id, remitente, tipo, contenido, external_message_id, sent_at) VALUES
(1, 'SISTEMA',   'TEXT', 'Se inicia contacto preventivo por riesgo ALTO (score 84).', NULL, '2026-09-12 09:00:00'),
(1, 'ASISTENTE', 'TEXT', 'Hola Carlos. Te contactamos porque tu próximo pago se encuentra próximo a su fecha de vencimiento. ¿Podrías indicarnos cuándo estimas realizarlo?', 'wamid.CARLOS001', '2026-09-12 09:00:15'),
(1, 'USUARIO',   'TEXT', 'El jueves puedo hacerlo.', 'wamid.CARLOS002', '2026-09-12 09:02:40'),
(1, 'ASISTENTE', 'TEXT', 'Perfecto Carlos, quedamos entonces en que realizarás el pago el jueves 17/09. ¡Gracias por confirmarlo!', 'wamid.CARLOS003', '2026-09-12 09:03:10');

-- Conversación 2: Jose Luis (no responde)
INSERT INTO mensaje (conversacion_id, remitente, tipo, contenido, external_message_id, sent_at) VALUES
(2, 'SISTEMA',   'TEXT', 'Se inicia contacto preventivo por riesgo ALTO (score 89) e incumplimiento reciente.', NULL, '2026-09-12 10:00:00'),
(2, 'ASISTENTE', 'TEXT', 'Hola José Luis. Notamos que tu crédito tiene un pago pendiente próximo a vencer. ¿Podrías confirmarnos cuándo realizarás el pago?', 'wamid.JOSE001', '2026-09-12 10:00:20');

-- Conversación 3: Roberto (compromiso previo, ya cumplido)
INSERT INTO mensaje (conversacion_id, remitente, tipo, contenido, external_message_id, sent_at) VALUES
(3, 'SISTEMA',   'TEXT', 'Se inicia contacto preventivo por riesgo ALTO (score 78).', NULL, '2026-09-05 11:00:00'),
(3, 'ASISTENTE', 'TEXT', 'Hola Roberto. Tu pago está próximo a vencer. ¿Podrías indicarnos cuándo lo realizarás?', 'wamid.ROBERTO001', '2026-09-05 11:00:30'),
(3, 'USUARIO',   'TEXT', 'Sí, lo pago mañana mismo.', 'wamid.ROBERTO002', '2026-09-05 11:05:00'),
(3, 'ASISTENTE', 'TEXT', 'Excelente Roberto, quedamos en que pagarás mañana 06/09. ¡Gracias!', 'wamid.ROBERTO003', '2026-09-05 11:05:45');

-- ------------------------------------------------------------
-- 7. Resúmenes de conversación
-- ------------------------------------------------------------
INSERT INTO resumen_conversacion
  (conversacion_id, resumen, intencion, compromiso_pago, fecha_compromiso, resultado, siguiente_accion, datos_llm, modelo_llm) VALUES
(1,
 'El usuario indicó que realizará el pago el jueves 17/09.',
 'COMPROMISO_PAGO', TRUE, '2026-09-17', 'COMPROMISO_OBTENIDO', 'Dar seguimiento el 17/09 para confirmar cumplimiento.',
 JSON_OBJECT('intencion','COMPROMISO_PAGO','compromiso_pago',TRUE,'fecha_compromiso','2026-09-17','resumen','El usuario indicó que realizará el pago el jueves.','resultado','COMPROMISO_OBTENIDO'),
 'claude-sonnet-4-6'),
(2,
 'El usuario no respondió al mensaje inicial dentro de la ventana esperada.',
 'SIN_RESPUESTA', FALSE, NULL, 'NO_CONTACTADO', 'Reintentar contacto en 24 horas o escalar a agente humano.',
 JSON_OBJECT('intencion','SIN_RESPUESTA','compromiso_pago',FALSE,'resumen','El usuario no respondió al mensaje inicial.','resultado','NO_CONTACTADO'),
 'claude-sonnet-4-6'),
(3,
 'El usuario confirmó que realizaría el pago al día siguiente.',
 'COMPROMISO_PAGO', TRUE, '2026-09-06', 'COMPROMISO_OBTENIDO', 'Verificar pago el 06/09.',
 JSON_OBJECT('intencion','COMPROMISO_PAGO','compromiso_pago',TRUE,'fecha_compromiso','2026-09-06','resumen','El usuario confirmó que pagaría al día siguiente.','resultado','COMPROMISO_OBTENIDO'),
 'claude-sonnet-4-6');

-- ------------------------------------------------------------
-- 8. Compromisos de pago
-- ------------------------------------------------------------
-- Carlos: compromiso aún pendiente (vence el 17/09, fecha "actual" de la demo es 12/09)
INSERT INTO compromiso_pago (credito_id, usuario_id, conversacion_id, fecha_compromiso, monto_comprometido, estado) VALUES
(1, 1, 1, '2026-09-17', 150.00, 'PENDIENTE');

-- Roberto: compromiso anterior ya cumplido (demuestra el ciclo completo)
INSERT INTO compromiso_pago (credito_id, usuario_id, conversacion_id, fecha_compromiso, monto_comprometido, estado) VALUES
(5, 5, 3, '2026-09-06', 200.00, 'CUMPLIDO');

-- ============================================================
-- Fin de datos semilla V1
-- ============================================================