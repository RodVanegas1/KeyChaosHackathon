CREATE TABLE IF NOT EXISTS beany_sesion (
 session_id CHAR(36) NOT NULL,
 usuario_id BIGINT NULL,
 conversacion_id BIGINT NULL,
 estado VARCHAR(50) NOT NULL,
 identidad_confirmada TINYINT(1) NOT NULL DEFAULT 0,
 contexto_json JSON NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 PRIMARY KEY(session_id),
 CONSTRAINT fk_beany_sesion_usuario FOREIGN KEY(usuario_id) REFERENCES usuario(id) ON DELETE SET NULL,
 CONSTRAINT fk_beany_sesion_conversacion FOREIGN KEY(conversacion_id) REFERENCES conversacion(id) ON DELETE SET NULL
);
