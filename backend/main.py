from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from typing import Optional

app = FastAPI(title="Bancoagrícola - Prevención de Mora API")

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mora_demo'
}

# --- MODELOS DE DATOS (Pydantic) ---
class MensajeWhatsApp(BaseModel):
    telefono: str
    mensaje: str

class CompromisoPago(BaseModel):
    credito_id: int
    usuario_id: int
    conversacion_id: int
    fecha_compromiso: str
    monto_comprometido: float

# --- CONEXIÓN BD ---
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Error conectando a MySQL: {e}")
        return None

# --- ENDPOINTS DEL DASHBOARD ---

@app.get("/api/dashboard/metrics")
def get_dashboard_metrics():
    conn = get_db_connection()
    if not conn:
        return {
            "riesgo_alto": 142,
            "conversaciones_activas": 28,
            "compromisos_obtenidos": 85,
            "monto_recuperado": 12500.50
        }
        
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM evaluacion_riesgo WHERE nivel_riesgo = 'ALTO'")
        riesgo_alto = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM conversacion WHERE estado = 'EN_CURSO'")
        conv_activas = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(monto_comprometido) as monto 
            FROM compromiso_pago 
            WHERE estado IN ('PENDIENTE', 'CUMPLIDO')
        """)
        compromisos_data = cursor.fetchone()
        
        return {
            "riesgo_alto": riesgo_alto,
            "conversaciones_activas": conv_activas,
            "compromisos_obtenidos": compromisos_data['total'] or 0,
            "monto_recuperado": float(compromisos_data['monto'] or 0)
        }
    finally:
        cursor.close()
        conn.close()

@app.get("/api/dashboard/gestiones")
def get_gestiones_recientes():
    """Obtiene los clientes con riesgo alto para mostrarlos en la lista del dashboard"""
    conn = get_db_connection()
    if not conn:
        # Fallback para que la UI no se rompa
        return [
            {"nombre": "Carlos M.", "riesgo": 84, "saldo": 850.00, "estado": "Compromiso 17/09"},
            {"nombre": "María G.", "riesgo": 71, "saldo": 320.00, "estado": "En conversación..."}
        ]
        
    cursor = conn.cursor(dictionary=True)
    try:
        # Hacemos un JOIN para traer el nombre del usuario, su riesgo y el saldo del crédito
        query = """
            SELECT u.nombre, er.score as riesgo, c.saldo_pendiente as saldo
            FROM evaluacion_riesgo er
            JOIN credito c ON er.credito_id = c.id
            JOIN usuario u ON c.usuario_id = u.id
            WHERE er.nivel_riesgo = 'ALTO'
            ORDER BY er.score DESC
            LIMIT 5
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        
        # Formatear la salida para el frontend
        gestiones = []
        for row in resultados:
            gestiones.append({
                "nombre": row['nombre'],
                "riesgo": float(row['riesgo']),
                "saldo": float(row['saldo']),
                "estado": "Requiere contacto" # Esto luego se puede cruzar con la tabla 'conversacion'
            })
        return gestiones
    finally:
        cursor.close()
        conn.close()

# --- ENDPOINTS DEL LLM / WHATSAPP ---

@app.post("/api/webhook/whatsapp")
def recibir_mensaje(data: MensajeWhatsApp):
    """Aquí entra el mensaje del cliente, llamas al LLM y guardas en BD"""
    
    # 1. Buscar al usuario por teléfono
    # 2. Guardar el mensaje en la tabla 'mensaje'
    # 3. Mandar el historial al LLM (ej. OpenAI)
    # 4. Devolver la respuesta del LLM
    
    respuesta_ia = f"Hola, soy el asistente de Bancoagrícola. He recibido tu mensaje: '{data.mensaje}'"
    
    # Simulación de respuesta exitosa para la demo
    return {
        "status": "success",
        "reply": respuesta_ia
    }

@app.post("/api/compromisos")
def registrar_compromiso(data: CompromisoPago):
    """El LLM llama a esto cuando el cliente acepta pagar"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a BD")
        
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO compromiso_pago (credito_id, usuario_id, conversacion_id, fecha_compromiso, monto_comprometido, estado)
            VALUES (%s, %s, %s, %s, %s, 'PENDIENTE')
        """
        cursor.execute(query, (data.credito_id, data.usuario_id, data.conversacion_id, data.fecha_compromiso, data.monto_comprometido))
        conn.commit()
        return {"status": "success", "mensaje": "Compromiso registrado correctamente"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()