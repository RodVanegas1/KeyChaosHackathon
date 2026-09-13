-- ============================================================
-- Mora Preventiva / Conversational Demo - MySQL
-- Version: V1
-- Motor: MySQL 8.x
-- Datos de demostración
-- ============================================================

USE railway;

-- ------------------------------------------------------------
-- 1. Usuarios
-- ------------------------------------------------------------
CREATE TABLE usuario (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    email VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_usuario_telefono UNIQUE (telefono),
    INDEX idx_usuario_nombre (nombre)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. Créditos
-- ------------------------------------------------------------
CREATE TABLE credito (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NOT NULL,
    monto_original DECIMAL(14,2) NOT NULL,
    saldo_pendiente DECIMAL(14,2) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado ENUM('ACTIVO', 'PAGADO', 'VENCIDO', 'CANCELADO')
        NOT NULL DEFAULT 'ACTIVO',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_credito_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario(id),

    CONSTRAINT chk_credito_montos
        CHECK (monto_original >= 0 AND saldo_pendiente >= 0),

    INDEX idx_credito_usuario (usuario_id),
    INDEX idx_credito_estado_vencimiento (estado, fecha_vencimiento)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 3. Pagos históricos
-- ------------------------------------------------------------
CREATE TABLE pago (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    credito_id BIGINT UNSIGNED NOT NULL,
    fecha_programada DATE NOT NULL,
    fecha_pago DATE NULL,
    monto_esperado DECIMAL(14,2) NOT NULL,
    monto_pagado DECIMAL(14,2) NULL,
    estado ENUM('PENDIENTE', 'PAGADO', 'TARDIO', 'PARCIAL', 'INCUMPLIDO')
        NOT NULL DEFAULT 'PENDIENTE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pago_credito
        FOREIGN KEY (credito_id) REFERENCES credito(id),

    CONSTRAINT chk_pago_montos
        CHECK (
            monto_esperado >= 0
            AND (monto_pagado IS NULL OR monto_pagado >= 0)
        ),

    INDEX idx_pago_credito (credito_id),
    INDEX idx_pago_credito_fecha (credito_id, fecha_programada),
    INDEX idx_pago_estado (estado)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 4. Evaluaciones de riesgo
--    Una evaluación representa el riesgo calculado en un momento.
-- ------------------------------------------------------------
CREATE TABLE evaluacion_riesgo (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    credito_id BIGINT UNSIGNED NOT NULL,

    score DECIMAL(5,2) NOT NULL,
    probabilidad_mora DECIMAL(5,4) NOT NULL,
    nivel_riesgo ENUM('BAJO', 'MEDIO', 'ALTO') NOT NULL,

    dias_restantes SMALLINT NULL,
    tasa_retraso DECIMAL(6,4) NULL,
    promedio_dias_retraso DECIMAL(8,2) NULL,
    pagos_tardios_recientes INT UNSIGNED NULL,

    tendencia ENUM('DISMINUYENDO', 'ESTABLE', 'AUMENTANDO') NULL,

    modelo_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    calculado_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_riesgo_credito
        FOREIGN KEY (credito_id) REFERENCES credito(id),

    CONSTRAINT chk_riesgo_score
        CHECK (score >= 0 AND score <= 100),

    CONSTRAINT chk_riesgo_probabilidad
        CHECK (probabilidad_mora >= 0 AND probabilidad_mora <= 1),

    INDEX idx_riesgo_credito_fecha (credito_id, calculado_at),
    INDEX idx_riesgo_nivel (nivel_riesgo)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 5. Conversaciones de WhatsApp
-- ------------------------------------------------------------
CREATE TABLE conversacion (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NOT NULL,
    credito_id BIGINT UNSIGNED NULL,

    canal ENUM('WHATSAPP') NOT NULL DEFAULT 'WHATSAPP',
    estado ENUM('INICIADA', 'EN_CURSO', 'COMPLETADA', 'CANCELADA', 'FALLIDA')
        NOT NULL DEFAULT 'INICIADA',

    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME NULL,

    CONSTRAINT fk_conversacion_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario(id),

    CONSTRAINT fk_conversacion_credito
        FOREIGN KEY (credito_id) REFERENCES credito(id),

    INDEX idx_conversacion_usuario (usuario_id),
    INDEX idx_conversacion_credito (credito_id),
    INDEX idx_conversacion_estado (estado)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 6. Mensajes
--    Se conserva el historial completo de la conversación.
-- ------------------------------------------------------------
CREATE TABLE mensaje (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversacion_id BIGINT UNSIGNED NOT NULL,

    remitente ENUM('USUARIO', 'ASISTENTE', 'SISTEMA') NOT NULL,
    tipo ENUM('TEXT', 'AUDIO', 'IMAGE') NOT NULL DEFAULT 'TEXT',

    contenido TEXT NOT NULL,
    external_message_id VARCHAR(255) NULL,
    sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mensaje_conversacion
        FOREIGN KEY (conversacion_id) REFERENCES conversacion(id),

    CONSTRAINT uq_mensaje_external_id UNIQUE (external_message_id),

    INDEX idx_mensaje_conversacion_fecha (conversacion_id, sent_at)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 7. Resumen estructurado de conversación
--    Resultado interpretado por el LLM y validado por backend.
-- ------------------------------------------------------------
CREATE TABLE resumen_conversacion (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversacion_id BIGINT UNSIGNED NOT NULL,

    resumen TEXT NOT NULL,

    intencion ENUM(
        'SIN_RESPUESTA',
        'NO_INTERESADO',
        'NO_PUEDE_PAGAR',
        'PUEDE_PAGAR',
        'COMPROMISO_PAGO',
        'OTRA'
    ) NOT NULL,

    compromiso_pago BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_compromiso DATE NULL,

    resultado ENUM(
        'SIN_COMPROMISO',
        'COMPROMISO_OBTENIDO',
        'REQUIERE_SEGUIMIENTO',
        'NO_CONTACTADO',
        'OTRO'
    ) NOT NULL,

    siguiente_accion VARCHAR(255) NULL,

    datos_llm JSON NULL,
    modelo_llm VARCHAR(100) NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_resumen_conversacion
        FOREIGN KEY (conversacion_id) REFERENCES conversacion(id),

    CONSTRAINT uq_resumen_conversacion UNIQUE (conversacion_id),

    INDEX idx_resumen_intencion (intencion),
    INDEX idx_resumen_resultado (resultado)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 8. Compromisos de pago
--    Registro operativo validado por el backend.
-- ------------------------------------------------------------
CREATE TABLE compromiso_pago (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    credito_id BIGINT UNSIGNED NOT NULL,
    usuario_id BIGINT UNSIGNED NOT NULL,
    conversacion_id BIGINT UNSIGNED NOT NULL,

    fecha_compromiso DATE NOT NULL,
    monto_comprometido DECIMAL(14,2) NULL,

    estado ENUM(
        'PENDIENTE',
        'CUMPLIDO',
        'INCUMPLIDO',
        'CANCELADO'
    ) NOT NULL DEFAULT 'PENDIENTE',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_compromiso_credito
        FOREIGN KEY (credito_id) REFERENCES credito(id),

    CONSTRAINT fk_compromiso_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario(id),

    CONSTRAINT fk_compromiso_conversacion
        FOREIGN KEY (conversacion_id) REFERENCES conversacion(id),

    CONSTRAINT chk_compromiso_monto
        CHECK (monto_comprometido IS NULL OR monto_comprometido >= 0),

    INDEX idx_compromiso_credito (credito_id),
    INDEX idx_compromiso_usuario (usuario_id),
    INDEX idx_compromiso_fecha_estado (fecha_compromiso, estado)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 9. Perfil de usuario (datos blandos / demográficos)
--    Complementa a `usuario` sin ensuciar la tabla transaccional.
-- ------------------------------------------------------------
CREATE TABLE perfil_usuario (
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
-- Fin del esquema V1
-- ============================================================
