import json
from typing import Any, Dict, List, Optional
from database.connection import get_db_connection


def _conn():
    conn = get_db_connection()
    if not conn:
        raise RuntimeError('No se pudo conectar a MySQL')
    return conn


def find_customer_by_phone(telefono: str) -> Optional[Dict[str, Any]]:
    conn = _conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute('SELECT id,nombre,telefono,email FROM usuario WHERE telefono=%s LIMIT 1',(telefono,))
        return cur.fetchone()
    finally: cur.close(); conn.close()


def find_active_credito(usuario_id: int) -> Optional[Dict[str, Any]]:
    conn = _conn(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,usuario_id,monto_original,saldo_pendiente,fecha_inicio,fecha_vencimiento,estado FROM credito WHERE usuario_id=%s AND estado IN ('ACTIVO','VENCIDO') ORDER BY fecha_vencimiento ASC LIMIT 1",(usuario_id,))
        return cur.fetchone()
    finally: cur.close(); conn.close()


def create_or_get_conversation(usuario_id:int, credito_id:Optional[int], canal:str='VOZ')->int:
    conn=_conn(); cur=conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM conversacion WHERE usuario_id=%s AND (credito_id=%s OR (%s IS NULL AND credito_id IS NULL)) AND estado IN ('INICIADA','EN_CURSO') ORDER BY id DESC LIMIT 1",(usuario_id,credito_id,credito_id))
        row=cur.fetchone()
        if row: return int(row['id'])
        cur2=conn.cursor()
        cur2.execute("INSERT INTO conversacion (usuario_id,credito_id,canal,estado) VALUES (%s,%s,%s,'EN_CURSO')",(usuario_id,credito_id,canal))
        cid=int(cur2.lastrowid); cur2.close(); conn.commit(); return cid
    except Exception:
        conn.rollback(); raise
    finally: cur.close(); conn.close()


def load_conversation_history(conversacion_id:int, limit:int=20)->List[Dict[str,str]]:
    conn=_conn(); cur=conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT remitente,contenido FROM mensaje WHERE conversacion_id=%s ORDER BY sent_at ASC,id ASC LIMIT %s",(conversacion_id,limit))
        out=[]
        for r in cur.fetchall(): out.append({'role':'assistant' if r['remitente']=='ASISTENTE' else 'user','content':r['contenido']})
        return out
    finally: cur.close(); conn.close()


def save_message(conversacion_id:int, remitente:str, contenido:str, tipo:str='TEXT')->int:
    conn=_conn(); cur=conn.cursor()
    try:
        cur.execute('INSERT INTO mensaje (conversacion_id,remitente,tipo,contenido) VALUES (%s,%s,%s,%s)',(conversacion_id,remitente,tipo,contenido))
        mid=int(cur.lastrowid); conn.commit(); return mid
    except Exception:
        conn.rollback(); raise
    finally: cur.close(); conn.close()


def save_beany_state(session_id:str, usuario_id:Optional[int], conversacion_id:Optional[int], estado:str, identidad_confirmada:bool, contexto:Dict[str,Any])->None:
    conn=_conn(); cur=conn.cursor()
    try:
        cur.execute('''INSERT INTO beany_sesion (session_id,usuario_id,conversacion_id,estado,identidad_confirmada,contexto_json) VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE usuario_id=VALUES(usuario_id),conversacion_id=VALUES(conversacion_id),estado=VALUES(estado),identidad_confirmada=VALUES(identidad_confirmada),contexto_json=VALUES(contexto_json),updated_at=CURRENT_TIMESTAMP''',(session_id,usuario_id,conversacion_id,estado,1 if identidad_confirmada else 0,json.dumps(contexto,ensure_ascii=False)))
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: cur.close(); conn.close()


def load_beany_state(session_id:str)->Optional[Dict[str,Any]]:
    conn=_conn(); cur=conn.cursor(dictionary=True)
    try:
        cur.execute('SELECT session_id,usuario_id,conversacion_id,estado,identidad_confirmada,contexto_json FROM beany_sesion WHERE session_id=%s LIMIT 1',(session_id,))
        row=cur.fetchone()
        if not row: return None
        row['contexto']=json.loads(row.pop('contexto_json') or '{}')
        row['identidad_confirmada']=bool(row['identidad_confirmada'])
        return row
    finally: cur.close(); conn.close()


def close_conversation(conversacion_id:int)->None:
    conn=_conn(); cur=conn.cursor()
    try:
        cur.execute("UPDATE conversacion SET estado='COMPLETADA',ended_at=CURRENT_TIMESTAMP WHERE id=%s",(conversacion_id,)); conn.commit()
    except Exception: conn.rollback(); raise
    finally: cur.close(); conn.close()
