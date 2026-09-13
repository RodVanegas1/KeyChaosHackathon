-- ============================================================
-- Mora Preventiva / Conversational Demo - MySQL
-- Datos semilla: 6 arquetipos de usuario
-- Fecha de referencia para "hoy": 2026-09-12
-- Requiere: mora_demo_v1.sql ya ejecutado (esquema base)
-- ============================================================

USE mora_demo;

-- ------------------------------------------------------------
-- 0. Tabla nueva: perfil_usuario
--    Datos blandos/demográficos, 1:1 con usuario.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perfil_usuario (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NOT NULL,

    edad SMALLINT UNSIGNED NULL,
    sexo ENUM('M', 'F', 'OTRO') NULL,
    ocupacion VARCHAR(150) NULL,

    tipo_ingreso ENUM('FIJO', 'VARIABLE', 'INFORMAL') NOT NULL,
    rango_salario_estimado ENUM(
        'BAJO',
        'MEDIO_BAJO',
        'MEDIO',
        'MEDIO_ALTO',
        'ALTO'
    ) NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_perfil_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario(id),

    CONSTRAINT uq_perfil_usuario UNIQUE (usuario_id),

    INDEX idx_perfil_tipo_ingreso (tipo_ingreso)
) ENGINE=InnoDB;

-- ============================================================
-- 1. Ana Beatriz Hernández — La Cumplidora Anticipada
-- ============================================================
INSERT INTO usuario (nombre, telefono, email) VALUES
('Ana Beatriz Hernández', '+50370112233', 'ana.hernandez@example.com');
SET @user_ana = LAST_INSERT_ID();

INSERT INTO perfil_usuario (usuario_id, edad, sexo, ocupacion, tipo_ingreso, rango_salario_estimado) VALUES
(@user_ana, 34, 'F', 'Contadora', 'FIJO', 'MEDIO');

INSERT INTO credito (usuario_id, monto_original, saldo_pendiente, fecha_inicio, fecha_vencimiento, estado) VALUES
(@user_ana, 1200.00, 200.00, '2026-03-15', '2026-09-20', 'ACTIVO');
SET @credito_ana = LAST_INSERT_ID();

INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(@credito_ana, '2026-04-15', '2026-04-11', 200.00, 200.00, 'PAGADO'),
(@credito_ana, '2026-05-15', '2026-05-12', 200.00, 200.00, 'PAGADO'),
(@credito_ana, '2026-06-15', '2026-06-10', 200.00, 200.00, 'PAGADO'),
(@credito_ana, '2026-07-15', '2026-07-11', 200.00, 200.00, 'PAGADO'),
(@credito_ana, '2026-08-15', '2026-08-13', 200.00, 200.00, 'PAGADO'),
(@credito_ana, '2026-09-20', NULL,          200.00, NULL,   'PENDIENTE');

INSERT INTO evaluacion_riesgo
(credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(@credito_ana, 12.00, 0.0800, 'BAJO', 15, 0.0000, 0.00, 0, 'ESTABLE', 'v1', '2026-09-05 09:00:00'),
(@credito_ana, 13.50, 0.0850, 'BAJO', 10, 0.0000, 0.00, 0, 'ESTABLE', 'v1', '2026-09-10 09:00:00'),
(@credito_ana, 15.00, 0.0900, 'BAJO', 8,  0.0000, 0.00, 0, 'ESTABLE', 'v1', '2026-09-12 09:00:00');


-- ============================================================
-- 2. Douglas Alexander Portillo — El Fantasma
-- ============================================================
INSERT INTO usuario (nombre, telefono, email) VALUES
('Douglas Alexander Portillo', '+50370223344', NULL);
SET @user_douglas = LAST_INSERT_ID();

INSERT INTO perfil_usuario (usuario_id, edad, sexo, ocupacion, tipo_ingreso, rango_salario_estimado) VALUES
(@user_douglas, 27, 'M', 'Mecánico automotriz independiente', 'INFORMAL', 'BAJO');

INSERT INTO credito (usuario_id, monto_original, saldo_pendiente, fecha_inicio, fecha_vencimiento, estado) VALUES
(@user_douglas, 600.00, 400.00, '2026-06-01', '2026-09-15', 'ACTIVO');
SET @credito_douglas = LAST_INSERT_ID();

INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(@credito_douglas, '2026-07-01', '2026-07-01', 200.00, 200.00, 'PAGADO'),
(@credito_douglas, '2026-08-01', NULL,         200.00, NULL,   'INCUMPLIDO'),
(@credito_douglas, '2026-09-15', NULL,         200.00, NULL,   'PENDIENTE');

INSERT INTO evaluacion_riesgo
(credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(@credito_douglas, 65.00, 0.5500, 'MEDIO', 14, 0.5000, 0.00, 1, 'AUMENTANDO', 'v1', '2026-09-01 09:00:00'),
(@credito_douglas, 78.00, 0.7200, 'ALTO',  7,  0.5000, 0.00, 1, 'AUMENTANDO', 'v1', '2026-09-08 09:00:00'),
(@credito_douglas, 88.00, 0.8500, 'ALTO',  3,  0.5000, 0.00, 1, 'AUMENTANDO', 'v1', '2026-09-12 09:00:00');


-- ============================================================
-- 3. Marta Elena Cortez — El Filo de la Navaja
-- ============================================================
INSERT INTO usuario (nombre, telefono, email) VALUES
('Marta Elena Cortez', '+50370334455', NULL);
SET @user_marta = LAST_INSERT_ID();

INSERT INTO perfil_usuario (usuario_id, edad, sexo, ocupacion, tipo_ingreso, rango_salario_estimado) VALUES
(@user_marta, 45, 'F', 'Dueña de pupusería', 'INFORMAL', 'MEDIO_BAJO');

INSERT INTO credito (usuario_id, monto_original, saldo_pendiente, fecha_inicio, fecha_vencimiento, estado) VALUES
(@user_marta, 1000.00, 200.00, '2026-04-01', '2026-09-17', 'ACTIVO');
SET @credito_marta = LAST_INSERT_ID();

INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(@credito_marta, '2026-05-01', '2026-05-01', 200.00, 200.00, 'PAGADO'),
(@credito_marta, '2026-06-01', '2026-06-01', 200.00, 200.00, 'PAGADO'),
(@credito_marta, '2026-07-01', '2026-07-01', 200.00, 200.00, 'PAGADO'),
(@credito_marta, '2026-08-01', '2026-08-01', 200.00, 200.00, 'PAGADO'),
(@credito_marta, '2026-09-17', NULL,         200.00, NULL,   'PENDIENTE');

-- Nota: tasa_retraso/promedio_dias_retraso quedan en 0 porque nunca
-- paga después de la fecha programada; el score medio refleja el
-- patrón de "pago justo al límite" que el motor de riesgo debe
-- capturar con una señal adicional (no solo con estos campos).
INSERT INTO evaluacion_riesgo
(credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(@credito_marta, 55.00, 0.4200, 'MEDIO', 12, 0.0000, 0.00, 0, 'ESTABLE', 'v1', '2026-09-05 09:00:00'),
(@credito_marta, 58.00, 0.4500, 'MEDIO', 7,  0.0000, 0.00, 0, 'ESTABLE', 'v1', '2026-09-10 09:00:00'),
(@credito_marta, 60.00, 0.4700, 'MEDIO', 5,  0.0000, 0.00, 0, 'ESTABLE', 'v1', '2026-09-12 09:00:00');


-- ============================================================
-- 4. Jorge Iván Meléndez — El Reincidente Rescatable
-- ============================================================
INSERT INTO usuario (nombre, telefono, email) VALUES
('Jorge Iván Meléndez', '+50370445566', NULL);
SET @user_jorge = LAST_INSERT_ID();

INSERT INTO perfil_usuario (usuario_id, edad, sexo, ocupacion, tipo_ingreso, rango_salario_estimado) VALUES
(@user_jorge, 39, 'M', 'Vendedor por comisión', 'VARIABLE', 'MEDIO');

INSERT INTO credito (usuario_id, monto_original, saldo_pendiente, fecha_inicio, fecha_vencimiento, estado) VALUES
(@user_jorge, 1750.00, 250.00, '2026-02-01', '2026-09-19', 'ACTIVO');
SET @credito_jorge = LAST_INSERT_ID();

INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(@credito_jorge, '2026-03-01', '2026-03-09', 250.00, 250.00, 'TARDIO'),
(@credito_jorge, '2026-04-01', '2026-04-06', 250.00, 250.00, 'TARDIO'),
(@credito_jorge, '2026-05-01', '2026-05-01', 250.00, 250.00, 'PAGADO'),
(@credito_jorge, '2026-06-01', '2026-06-11', 250.00, 250.00, 'TARDIO'),
(@credito_jorge, '2026-07-01', '2026-07-08', 250.00, 250.00, 'TARDIO'),
(@credito_jorge, '2026-08-01', '2026-08-09', 250.00, 250.00, 'TARDIO'),
(@credito_jorge, '2026-09-19', NULL,         250.00, NULL,   'PENDIENTE');

INSERT INTO evaluacion_riesgo
(credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(@credito_jorge, 68.00, 0.6000, 'ALTO', 18, 0.8333, 6.33, 5, 'AUMENTANDO', 'v1', '2026-09-01 09:00:00'),
(@credito_jorge, 72.00, 0.6500, 'ALTO', 11, 0.8333, 6.33, 5, 'AUMENTANDO', 'v1', '2026-09-08 09:00:00'),
(@credito_jorge, 75.00, 0.6900, 'ALTO', 7,  0.8333, 6.33, 5, 'AUMENTANDO', 'v1', '2026-09-12 09:00:00');


-- ============================================================
-- 5. Katherine Sofía Aguilar — La Negociadora Parcial
-- ============================================================
INSERT INTO usuario (nombre, telefono, email) VALUES
('Katherine Sofía Aguilar', '+50370556677', 'katherine.aguilar@example.com');
SET @user_katherine = LAST_INSERT_ID();

INSERT INTO perfil_usuario (usuario_id, edad, sexo, ocupacion, tipo_ingreso, rango_salario_estimado) VALUES
(@user_katherine, 23, 'F', 'Agente de call center', 'FIJO', 'BAJO');

INSERT INTO credito (usuario_id, monto_original, saldo_pendiente, fecha_inicio, fecha_vencimiento, estado) VALUES
(@user_katherine, 500.00, 400.00, '2026-07-01', '2026-09-16', 'ACTIVO');
SET @credito_katherine = LAST_INSERT_ID();

INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(@credito_katherine, '2026-08-01', '2026-08-03', 250.00, 100.00, 'PARCIAL'),
(@credito_katherine, '2026-09-16', NULL,         250.00, NULL,   'PENDIENTE');

INSERT INTO evaluacion_riesgo
(credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(@credito_katherine, 70.00, 0.6200, 'ALTO', 13, 1.0000, 2.00, 1, 'AUMENTANDO', 'v1', '2026-09-03 09:00:00'),
(@credito_katherine, 76.00, 0.7000, 'ALTO', 6,  1.0000, 2.00, 1, 'AUMENTANDO', 'v1', '2026-09-10 09:00:00'),
(@credito_katherine, 79.00, 0.7300, 'ALTO', 4,  1.0000, 2.00, 1, 'AUMENTANDO', 'v1', '2026-09-12 09:00:00');


-- ============================================================
-- 6. Óscar Renato Villalta — El Imprevisto
-- ============================================================
INSERT INTO usuario (nombre, telefono, email) VALUES
('Óscar Renato Villalta', '+50370667788', 'oscar.villalta@example.com');
SET @user_oscar = LAST_INSERT_ID();

INSERT INTO perfil_usuario (usuario_id, edad, sexo, ocupacion, tipo_ingreso, rango_salario_estimado) VALUES
(@user_oscar, 41, 'M', 'Técnico de mantenimiento industrial', 'FIJO', 'MEDIO_ALTO');

INSERT INTO credito (usuario_id, monto_original, saldo_pendiente, fecha_inicio, fecha_vencimiento, estado) VALUES
(@user_oscar, 2400.00, 400.00, '2025-01-15', '2026-09-18', 'ACTIVO');
SET @credito_oscar = LAST_INSERT_ID();

-- Nota: se omiten las cuotas 1-6 (todas PAGADO, puntuales) por brevedad;
-- solo se detallan las 4 más recientes antes de la cuota actual.
INSERT INTO pago (credito_id, fecha_programada, fecha_pago, monto_esperado, monto_pagado, estado) VALUES
(@credito_oscar, '2026-05-15', '2026-05-12', 200.00, 200.00, 'PAGADO'),
(@credito_oscar, '2026-06-15', '2026-06-11', 200.00, 200.00, 'PAGADO'),
(@credito_oscar, '2026-07-15', '2026-07-13', 200.00, 200.00, 'PAGADO'),
(@credito_oscar, '2026-08-15', '2026-08-12', 200.00, 200.00, 'PAGADO'),
(@credito_oscar, '2026-09-18', NULL,         200.00, NULL,   'PENDIENTE');

-- El salto de score entre el 05/09 y el 12/09 representa el evento
-- externo (choque vehicular) que aún no se refleja como atraso real
-- en `pago` -- tasa_retraso sigue en 0, pero el sistema debe elevar
-- el riesgo por proximidad de vencimiento sin pago registrado.
INSERT INTO evaluacion_riesgo
(credito_id, score, probabilidad_mora, nivel_riesgo, dias_restantes, tasa_retraso, promedio_dias_retraso, pagos_tardios_recientes, tendencia, modelo_version, calculado_at) VALUES
(@credito_oscar, 15.00, 0.1000, 'BAJO',  29, 0.0000, 0.00, 0, 'ESTABLE',    'v1', '2026-08-20 09:00:00'),
(@credito_oscar, 22.00, 0.1500, 'BAJO',  13, 0.0000, 0.00, 0, 'ESTABLE',    'v1', '2026-09-05 09:00:00'),
(@credito_oscar, 58.00, 0.5000, 'MEDIO', 6,  0.0000, 0.00, 0, 'AUMENTANDO', 'v1', '2026-09-12 09:00:00');

-- ============================================================
-- Fin de datos semilla
-- ============================================================
