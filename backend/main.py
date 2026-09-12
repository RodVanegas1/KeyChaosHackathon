from datetime import date, datetime
from decimal import Decimal
import json
import os
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import Error
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Bancoagrícola - Prevención de Mora API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [
    origin.strip()
    for origin in allowed_origins_raw.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE CONFIG
# Railway:
# MYSQLHOST
# MYSQLPORT
# MYSQLUSER
# MYSQLPASSWORD
# MYSQLDATABASE
#
# Local:
# se pueden definir esas mismas variables en .env
# ============================================================

DB_CONFIG = {
    "host": os.getenv("MYSQLHOST", "localhost"),
    "port": int(os.getenv("MYSQLPORT", "3306")),
    "user": os.getenv("MYSQLUSER", "root"),
    "password": os.getenv("MYSQLPASSWORD", ""),
    "database": os.getenv("MYSQLDATABASE", "mora_demo"),
    "autocommit": False,
    "connection_timeout": 10,
}


def get_db_connection():
    """
    Crea una conexión nueva a MySQL.
    En Railway toma automáticamente las variables MYSQL*.
    """
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as exc:
        print(f"Error conectando a MySQL: {exc}")
        return None


# ============================================================
# HELPERS
# ============================================================

def serialize_value(value: Any) -> Any:
    """Convierte tipos de MySQL/Python a JSON serializable."""
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return value


def serialize_row(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None

    return {
        key: serialize_value(value)
        for key, value in row.items()
    }


def get_or_404_connection():
    conn = get_db_connection()

    if not conn:
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar a la base de datos."
        )

    return conn


# ============================================================
# MODELOS DE ENTRADA
# ============================================================

class MensajeWhatsApp(BaseModel):
    telefono: str = Field(min_length=3, max_length=30)
    mensaje: str = Field(min_length=1)
    external_message_id: Optional[str] = Field(
        default=None,
        max_length=255
    )


class MensajeConversacion(BaseModel):
    conversacion_id: int
    remitente: str
    contenido: str
    tipo: str = "TEXT"
    external_message_id: Optional[str] = None


class ResumenConversacion(BaseModel):
    conversacion_id: int
    resumen: str
    intencion: str
    compromiso_pago: bool = False
    fecha_compromiso: Optional[date] = None
    resultado: str
    siguiente_accion: Optional[str] = None
    datos_llm: Optional[Dict[str, Any]] = None
    modelo_llm: Optional[str] = None


class CompromisoPago(BaseModel):
    credito_id: int
    usuario_id: int
    conversacion_id: int
    fecha_compromiso: date
    monto_comprometido: Optional[float] = None


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Bancoagrícola - Prevención de Mora API",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    conn = get_db_connection()

    if not conn:
        raise HTTPException(
            status_code=503,
            detail="API activa, pero MySQL no está disponible."
        )

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        return {
            "status": "ok",
            "database": "connected"
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard/metrics")
def get_dashboard_metrics():
    conn = get_or_404_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Riesgo alto: tomamos la evaluación más reciente por crédito.
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM evaluacion_riesgo er
            INNER JOIN (
                SELECT credito_id, MAX(calculado_at) AS latest_at
                FROM evaluacion_riesgo
                GROUP BY credito_id
            ) latest
                ON latest.credito_id = er.credito_id
                AND latest.latest_at = er.calculado_at
            WHERE er.nivel_riesgo = 'ALTO'
            """
        )
        riesgo_alto = cursor.fetchone()["total"] or 0

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM conversacion
            WHERE estado = 'EN_CURSO'
            """
        )
        conversaciones_activas = cursor.fetchone()["total"] or 0

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM compromiso_pago
            WHERE estado IN ('PENDIENTE', 'CUMPLIDO')
            """
        )
        compromisos_obtenidos = cursor.fetchone()["total"] or 0

        cursor.execute(
            """
            SELECT COALESCE(SUM(monto_comprometido), 0) AS monto
            FROM compromiso_pago
            WHERE estado = 'CUMPLIDO'
            """
        )
        monto_recuperado = cursor.fetchone()["monto"] or 0

        return {
            "riesgo_alto": int(riesgo_alto),
            "conversaciones_activas": int(conversaciones_activas),
            "compromisos_obtenidos": int(compromisos_obtenidos),
            "monto_recuperado": float(monto_recuperado),
        }

    finally:
        cursor.close()
        conn.close()


@app.get("/api/dashboard/gestiones")
def get_gestiones_recientes(limit: int = 10):
    limit = max(1, min(limit, 50))

    conn = get_or_404_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = f"""
            SELECT
                u.id AS usuario_id,
                u.nombre,
                u.telefono,
                c.id AS credito_id,
                c.saldo_pendiente AS saldo,
                er.score AS riesgo,
                er.nivel_riesgo,
                er.tendencia,
                er.calculado_at,
                conv.id AS conversacion_id,
                conv.estado AS conversacion_estado
            FROM usuario u
            INNER JOIN credito c
                ON c.usuario_id = u.id
            LEFT JOIN (
                SELECT er1.*
                FROM evaluacion_riesgo er1
                INNER JOIN (
                    SELECT credito_id, MAX(calculado_at) AS latest_at
                    FROM evaluacion_riesgo
                    GROUP BY credito_id
                ) latest
                    ON latest.credito_id = er1.credito_id
                    AND latest.latest_at = er1.calculado_at
            ) er
                ON er.credito_id = c.id
            LEFT JOIN (
                SELECT conv1.*
                FROM conversacion conv1
                INNER JOIN (
                    SELECT usuario_id, credito_id, MAX(id) AS latest_id
                    FROM conversacion
                    GROUP BY usuario_id, credito_id
                ) latest_conv
                    ON latest_conv.latest_id = conv1.id
            ) conv
                ON conv.usuario_id = u.id
                AND conv.credito_id = c.id
            WHERE c.estado IN ('ACTIVO', 'VENCIDO')
            ORDER BY
                CASE er.nivel_riesgo
                    WHEN 'ALTO' THEN 1
                    WHEN 'MEDIO' THEN 2
                    WHEN 'BAJO' THEN 3
                    ELSE 4
                END,
                er.score DESC
            LIMIT {limit}
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        result = []

        for row in rows:
            item = serialize_row(row)

            item["estado"] = (
                item.get("conversacion_estado")
                or "REQUIERE_CONTACTO"
            )

            result.append(item)

        return result

    finally:
        cursor.close()
        conn.close()


# ============================================================
# BUSCAR CONTEXTO DE CLIENTE
# ============================================================

@app.get("/api/clientes/por-telefono/{telefono}")
def get_customer_context(telefono: str):
    """
    Devuelve el contexto operativo necesario para que n8n/IA
    pueda responder de forma personalizada.
    """

    conn = get_or_404_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # USUARIO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                nombre,
                telefono,
                email,
                created_at
            FROM usuario
            WHERE telefono = %s
            LIMIT 1
            """,
            (telefono,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado."
            )

        # ----------------------------------------------------
        # CREDITO ACTIVO / VENCIDO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                usuario_id,
                monto_original,
                saldo_pendiente,
                fecha_inicio,
                fecha_vencimiento,
                estado,
                created_at
            FROM credito
            WHERE usuario_id = %s
              AND estado IN ('ACTIVO', 'VENCIDO')
            ORDER BY fecha_vencimiento ASC
            LIMIT 1
            """,
            (usuario["id"],)
        )

        credito = cursor.fetchone()

        if not credito:
            raise HTTPException(
                status_code=404,
                detail="No existe un crédito activo o vencido."
            )

        # ----------------------------------------------------
        # PAGO PENDIENTE / TARDIO MÁS RELEVANTE
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                fecha_programada,
                fecha_pago,
                monto_esperado,
                monto_pagado,
                estado
            FROM pago
            WHERE credito_id = %s
              AND estado IN ('PENDIENTE', 'TARDIO', 'INCUMPLIDO', 'PARCIAL')
            ORDER BY fecha_programada ASC
            LIMIT 1
            """,
            (credito["id"],)
        )

        pago = cursor.fetchone()

        # ----------------------------------------------------
        # RIESGO MÁS RECIENTE
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                score,
                probabilidad_mora,
                nivel_riesgo,
                dias_restantes,
                tasa_retraso,
                promedio_dias_retraso,
                pagos_tardios_recientes,
                tendencia,
                modelo_version,
                calculado_at
            FROM evaluacion_riesgo
            WHERE credito_id = %s
            ORDER BY calculado_at DESC
            LIMIT 1
            """,
            (credito["id"],)
        )

        riesgo = cursor.fetchone()

        # ----------------------------------------------------
        # CONVERSACIÓN EN CURSO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                usuario_id,
                credito_id,
                canal,
                estado,
                started_at,
                ended_at
            FROM conversacion
            WHERE usuario_id = %s
              AND (credito_id = %s OR credito_id IS NULL)
              AND estado IN ('INICIADA', 'EN_CURSO')
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                usuario["id"],
                credito["id"]
            )
        )

        conversacion = cursor.fetchone()

        # ----------------------------------------------------
        # MÉTRICAS DE MORA
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COUNT(*) AS pagos_tardios,
                COALESCE(AVG(
                    CASE
                        WHEN fecha_pago IS NOT NULL
                             AND fecha_pago > fecha_programada
                        THEN DATEDIFF(fecha_pago, fecha_programada)
                    END
                ), 0) AS promedio_dias_retraso
            FROM pago
            WHERE credito_id = %s
            """,
            (credito["id"],)
        )

        historial_pago = cursor.fetchone()

        # ----------------------------------------------------
        # CÁLCULO DE DÍAS
        # ----------------------------------------------------

        hoy = date.today()

        fecha_referencia = None

        if pago and pago.get("fecha_programada"):
            fecha_referencia = pago["fecha_programada"]
        else:
            fecha_referencia = credito["fecha_vencimiento"]

        dias_mora = 0
        dias_restantes = None

        if fecha_referencia:
            delta = (hoy - fecha_referencia).days

            if delta > 0:
                dias_mora = delta
                dias_restantes = 0
            else:
                dias_mora = 0
                dias_restantes = abs(delta)

        # ----------------------------------------------------
        # RESPUESTA
        # ----------------------------------------------------

        return {
            "usuario": serialize_row(usuario),

            "credito": {
                **serialize_row(credito),
                "dias_mora": dias_mora,
                "dias_restantes": dias_restantes,
            },

            "pago_relevante": serialize_row(pago),

            "riesgo": serialize_row(riesgo),

            "historial": {
                "pagos_tardios": int(
                    historial_pago["pagos_tardios"] or 0
                ),
                "promedio_dias_retraso": float(
                    historial_pago["promedio_dias_retraso"] or 0
                ),
            },

            "conversacion": serialize_row(conversacion),

            # Todavía no inventamos incentivos porque no existen
            # en el esquema actual.
            "beneficio": {
                "disponible": False
            },
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================
# WHATSAPP -> BACKEND
# ============================================================

@app.post("/api/webhook/whatsapp")
def recibir_mensaje(data: MensajeWhatsApp):
    """
    Entrada preparada para n8n/WhatsApp.

    Responsabilidades:
    - localizar usuario;
    - localizar crédito;
    - crear/recuperar conversación;
    - guardar mensaje del usuario;
    - devolver contexto operativo a n8n.

    La IA NO se ejecuta aquí.
    """

    conn = get_or_404_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # 1. USUARIO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id, nombre, telefono, email
            FROM usuario
            WHERE telefono = %s
            LIMIT 1
            """,
            (data.telefono,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado."
            )

        # ----------------------------------------------------
        # 2. CREDITO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                usuario_id,
                monto_original,
                saldo_pendiente,
                fecha_inicio,
                fecha_vencimiento,
                estado
            FROM credito
            WHERE usuario_id = %s
              AND estado IN ('ACTIVO', 'VENCIDO')
            ORDER BY fecha_vencimiento ASC
            LIMIT 1
            """,
            (usuario["id"],)
        )

        credito = cursor.fetchone()

        if not credito:
            raise HTTPException(
                status_code=404,
                detail="No hay un crédito activo o vencido para el usuario."
            )

        # ----------------------------------------------------
        # 3. CONVERSACIÓN
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                estado
            FROM conversacion
            WHERE usuario_id = %s
              AND credito_id = %s
              AND estado IN ('INICIADA', 'EN_CURSO')
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                usuario["id"],
                credito["id"]
            )
        )

        conversacion = cursor.fetchone()

        if not conversacion:
            cursor.execute(
                """
                INSERT INTO conversacion
                    (usuario_id, credito_id, canal, estado)
                VALUES
                    (%s, %s, 'WHATSAPP', 'EN_CURSO')
                """,
                (
                    usuario["id"],
                    credito["id"]
                )
            )

            conversacion_id = cursor.lastrowid

        else:
            conversacion_id = conversacion["id"]

        # ----------------------------------------------------
        # 4. GUARDAR MENSAJE
        # ----------------------------------------------------

        if data.external_message_id:
            cursor.execute(
                """
                SELECT id
                FROM mensaje
                WHERE external_message_id = %s
                LIMIT 1
                """,
                (data.external_message_id,)
            )

            duplicate = cursor.fetchone()

            if not duplicate:
                cursor.execute(
                    """
                    INSERT INTO mensaje
                        (
                            conversacion_id,
                            remitente,
                            tipo,
                            contenido,
                            external_message_id
                        )
                    VALUES
                        (%s, 'USUARIO', 'TEXT', %s, %s)
                    """,
                    (
                        conversacion_id,
                        data.mensaje,
                        data.external_message_id
                    )
                )

        else:
            cursor.execute(
                """
                INSERT INTO mensaje
                    (
                        conversacion_id,
                        remitente,
                        tipo,
                        contenido
                    )
                VALUES
                    (%s, 'USUARIO', 'TEXT', %s)
                """,
                (
                    conversacion_id,
                    data.mensaje
                )
            )

        # ----------------------------------------------------
        # 5. COMMIT
        # ----------------------------------------------------

        conn.commit()

        return {
            "status": "success",
            "conversacion_id": conversacion_id,
            "usuario": serialize_row(usuario),
            "credito": serialize_row(credito),
            "mensaje": {
                "contenido": data.mensaje,
                "remitente": "USUARIO",
                "tipo": "TEXT",
            },
        }

    except HTTPException:
        conn.rollback()
        raise

    except Error as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error procesando mensaje: {exc}"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# HISTORIAL DE CONVERSACIÓN
# ============================================================

@app.get("/api/conversaciones/{conversacion_id}/mensajes")
def get_conversation_messages(conversacion_id: int):
    conn = get_or_404_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                conversacion_id,
                remitente,
                tipo,
                contenido,
                external_message_id,
                sent_at
            FROM mensaje
            WHERE conversacion_id = %s
            ORDER BY sent_at ASC, id ASC
            """,
            (conversacion_id,)
        )

        rows = cursor.fetchall()

        return [
            serialize_row(row)
            for row in rows
        ]

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GUARDAR MENSAJE DEL ASISTENTE
# ============================================================

@app.post("/api/conversaciones/mensaje")
def guardar_mensaje(data: MensajeConversacion):
    if data.remitente not in ("USUARIO", "ASISTENTE", "SISTEMA"):
        raise HTTPException(
            status_code=400,
            detail="Remitente inválido."
        )

    if data.tipo not in ("TEXT", "AUDIO", "IMAGE"):
        raise HTTPException(
            status_code=400,
            detail="Tipo de mensaje inválido."
        )

    conn = get_or_404_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar conversación
        cursor.execute(
            """
            SELECT id, estado
            FROM conversacion
            WHERE id = %s
            LIMIT 1
            """,
            (data.conversacion_id,)
        )

        conversacion = cursor.fetchone()

        if not conversacion:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada."
            )

        if data.external_message_id:
            cursor.execute(
                """
                SELECT id
                FROM mensaje
                WHERE external_message_id = %s
                LIMIT 1
                """,
                (data.external_message_id,)
            )

            existing = cursor.fetchone()

            if existing:
                return {
                    "status": "already_exists",
                    "mensaje_id": existing["id"],
                }

        cursor.execute(
            """
            INSERT INTO mensaje
                (
                    conversacion_id,
                    remitente,
                    tipo,
                    contenido,
                    external_message_id
                )
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (
                data.conversacion_id,
                data.remitente,
                data.tipo,
                data.contenido,
                data.external_message_id,
            )
        )

        mensaje_id = cursor.lastrowid

        conn.commit()

        return {
            "status": "success",
            "mensaje_id": mensaje_id,
        }

    except HTTPException:
        conn.rollback()
        raise

    except Error as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error guardando mensaje: {exc}"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# CIERRE DE CONVERSACIÓN
# ============================================================

@app.post("/api/conversaciones/{conversacion_id}/completar")
def completar_conversacion(conversacion_id: int):
    conn = get_or_404_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE conversacion
            SET
                estado = 'COMPLETADA',
                ended_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (conversacion_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Conversación no encontrada."
            )

        conn.commit()

        return {
            "status": "success",
            "conversacion_id": conversacion_id,
            "estado": "COMPLETADA",
        }

    except HTTPException:
        conn.rollback()
        raise

    except Error as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error completando conversación: {exc}"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# RESUMEN DE CONVERSACIÓN
# ============================================================

@app.post("/api/conversaciones/resumen")
def guardar_resumen(data: ResumenConversacion):
    conn = get_or_404_connection()
    cursor = conn.cursor()

    allowed_intenciones = {
        "SIN_RESPUESTA",
        "NO_INTERESADO",
        "NO_PUEDE_PAGAR",
        "PUEDE_PAGAR",
        "COMPROMISO_PAGO",
        "OTRA",
    }

    allowed_resultados = {
        "SIN_COMPROMISO",
        "COMPROMISO_OBTENIDO",
        "REQUIERE_SEGUIMIENTO",
        "NO_CONTACTADO",
        "OTRO",
    }

    if data.intencion not in allowed_intenciones:
        raise HTTPException(
            status_code=400,
            detail="Intención inválida."
        )

    if data.resultado not in allowed_resultados:
        raise HTTPException(
            status_code=400,
            detail="Resultado inválido."
        )

    try:
        datos_llm_json = (
            json.dumps(data.datos_llm, ensure_ascii=False)
            if data.datos_llm is not None
            else None
        )

        cursor.execute(
            """
            INSERT INTO resumen_conversacion
                (
                    conversacion_id,
                    resumen,
                    intencion,
                    compromiso_pago,
                    fecha_compromiso,
                    resultado,
                    siguiente_accion,
                    datos_llm,
                    modelo_llm
                )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                resumen = VALUES(resumen),
                intencion = VALUES(intencion),
                compromiso_pago = VALUES(compromiso_pago),
                fecha_compromiso = VALUES(fecha_compromiso),
                resultado = VALUES(resultado),
                siguiente_accion = VALUES(siguiente_accion),
                datos_llm = VALUES(datos_llm),
                modelo_llm = VALUES(modelo_llm)
            """,
            (
                data.conversacion_id,
                data.resumen,
                data.intencion,
                data.compromiso_pago,
                data.fecha_compromiso,
                data.resultado,
                data.siguiente_accion,
                datos_llm_json,
                data.modelo_llm,
            )
        )

        conn.commit()

        return {
            "status": "success",
            "conversacion_id": data.conversacion_id,
        }

    except Error as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error guardando resumen: {exc}"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# COMPROMISO DE PAGO
# ============================================================

@app.post("/api/compromisos")
def registrar_compromiso(data: CompromisoPago):
    conn = get_or_404_connection()
    cursor = conn.cursor()

    try:
        # ----------------------------------------------------
        # 1. VALIDAR CRÉDITO + USUARIO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                c.id,
                c.usuario_id,
                c.estado,
                c.saldo_pendiente
            FROM credito c
            WHERE c.id = %s
              AND c.usuario_id = %s
            LIMIT 1
            """,
            (
                data.credito_id,
                data.usuario_id
            )
        )

        credito = cursor.fetchone()

        if not credito:
            raise HTTPException(
                status_code=404,
                detail="Crédito no encontrado para el usuario."
            )

        if credito[2] not in ("ACTIVO", "VENCIDO"):
            raise HTTPException(
                status_code=400,
                detail="El crédito no está disponible para compromiso."
            )

        # ----------------------------------------------------
        # 2. VALIDAR CONVERSACIÓN
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM conversacion
            WHERE id = %s
              AND usuario_id = %s
              AND (credito_id = %s OR credito_id IS NULL)
            LIMIT 1
            """,
            (
                data.conversacion_id,
                data.usuario_id,
                data.credito_id
            )
        )

        conversacion = cursor.fetchone()

        if not conversacion:
            raise HTTPException(
                status_code=404,
                detail="Conversación no válida para este compromiso."
            )

        # ----------------------------------------------------
        # 3. REGLA DE 30 DÍAS
        #
        # Importante:
        # la fecha se valida aquí, no en el LLM.
        # ----------------------------------------------------

        hoy = date.today()
        max_fecha = hoy.fromordinal(hoy.toordinal() + 30)

        if data.fecha_compromiso > max_fecha:
            raise HTTPException(
                status_code=400,
                detail="La fecha de compromiso supera la ventana permitida de 30 días."
            )

        if data.fecha_compromiso < hoy:
            raise HTTPException(
                status_code=400,
                detail="La fecha de compromiso no puede estar en el pasado."
            )

        # ----------------------------------------------------
        # 4. VALIDAR MONTO
        # ----------------------------------------------------

        if data.monto_comprometido is not None:
            if data.monto_comprometido < 0:
                raise HTTPException(
                    status_code=400,
                    detail="El monto comprometido no puede ser negativo."
                )

            saldo_pendiente = float(credito[3] or 0)

            if data.monto_comprometido > saldo_pendiente:
                raise HTTPException(
                    status_code=400,
                    detail="El monto comprometido supera el saldo pendiente."
                )

        # ----------------------------------------------------
        # 5. REGISTRAR
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO compromiso_pago
                (
                    credito_id,
                    usuario_id,
                    conversacion_id,
                    fecha_compromiso,
                    monto_comprometido,
                    estado
                )
            VALUES
                (%s, %s, %s, %s, %s, 'PENDIENTE')
            """,
            (
                data.credito_id,
                data.usuario_id,
                data.conversacion_id,
                data.fecha_compromiso,
                data.monto_comprometido,
            )
        )

        compromiso_id = cursor.lastrowid

        conn.commit()

        return {
            "status": "success",
            "compromiso_id": compromiso_id,
            "estado": "PENDIENTE",
            "fecha_compromiso": data.fecha_compromiso.isoformat(),
        }

    except HTTPException:
        conn.rollback()
        raise

    except Error as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error registrando compromiso: {exc}"
        )

    finally:
        cursor.close()
        conn.close()
