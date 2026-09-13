import re, uuid
from typing import Dict
from .repository import find_customer_by_phone,find_active_credito,create_or_get_conversation,load_conversation_history,save_message,save_beany_state,load_beany_state,close_conversation
from .session import BeanySession
from .llm import generate_response

CONF=('si','sí','soy yo','soy el titular','soy la titular','correcto','correcta','afirmativo')
NEG=('no soy','equivocado','equivocada','no es')
OBJECTIVES={'VERIFICANDO_IDENTIDAD':'CONFIRMAR_IDENTIDAD','EXPLORANDO_SITUACION':'ENTENDER_SITUACION_DE_PAGO','BUSCANDO_FECHA':'PREGUNTAR_FECHA_PAGO','CONFIRMANDO_SIGUIENTE_PASO':'CONFIRMAR_FECHA_Y_SIGUIENTE_PASO','FINALIZADA':'CERRAR_CONVERSACION'}

def norm(t): return ' '.join(t.lower().strip().split())
def amount(t):
 m=re.search(r'(?:\$|usd\s*)?(\d+(?:[.,]\d{1,2})?)',t.lower()); return m.group(1).replace(',','.') if m else None
def intent(t):
 t=norm(t)
 if any(x in t for x in ('no puedo pagar','no puedo hacerlo','no tengo dinero','no me alcanza')): return 'NO_PUEDE_PAGAR'
 if any(x in t for x in ('puedo pagar','sí puedo pagar','si puedo pagar','voy a pagar')): return 'PUEDE_PAGAR'
 if any(x in t for x in ('asesor','persona','agente')): return 'REQUIERE_ASESOR'

def reason(t):
 t=norm(t)
 if any(x in t for x in ('me quede sin trabajo','me quedé sin trabajo','desemple','sin empleo','me despidieron')): return 'SITUACION_LABORAL'
 if any(x in t for x in ('enfer','salud','hospital')): return 'SALUD'
 if any(x in t for x in ('gasto','emergencia')): return 'GASTO_IMPREVISTO'

def date_ref(t):
 t=norm(t)
 for x in ('hoy','mañana','manana','lunes','martes','miércoles','miercoles','jueves','viernes','sábado','sabado','domingo'):
  if x in t: return x

class BeanyService:
 def __init__(self): self.sessions:Dict[str,BeanySession]={}
 def start_session(self,telefono):
  c=find_customer_by_phone(telefono); sid=str(uuid.uuid4()); s=BeanySession(session_id=sid,telefono=telefono)
  if not c: s.estado='FINALIZADA'; s.finalizada=True; self.sessions[sid]=s; return s
  s.usuario_id=c['id']; s.nombre=c['nombre']; cr=find_active_credito(c['id']); s.credito_id=cr['id'] if cr else None
  s.conversacion_id=create_or_get_conversation(s.usuario_id,s.credito_id,'VOZ'); s.historial=load_conversation_history(s.conversacion_id,20); s.estado='VERIFICANDO_IDENTIDAD'; self.sessions[sid]=s; self._persist(s); return s
 def get_session(self,sid):
  if sid in self.sessions:return self.sessions[sid]
  st=load_beany_state(sid)
  if not st: raise KeyError('Sesión no encontrada')
  s=BeanySession(session_id=sid,telefono='',usuario_id=st['usuario_id'],conversacion_id=st['conversacion_id'],estado=st['estado'],identidad_confirmada=st['identidad_confirmada'],contexto=st['contexto'])
  if s.conversacion_id:s.historial=load_conversation_history(s.conversacion_id,20)
  self.sessions[sid]=s; return s
 def _update_context(self,s,t):
  i=intent(t); r=reason(t); d=date_ref(t); a=amount(t)
  if i: s.contexto['intencion']=i; s.contexto['necesita_asesor']= i=='REQUIERE_ASESOR' or s.contexto['necesita_asesor']
  if r: s.contexto['motivo']=r; s.contexto['obstaculo']='SITUACION_PERSONAL'
  if d: s.contexto['fecha_propuesta']=d
  if a: s.contexto['monto_mencionado']=a
 def _update_state(self,s):
  if not s.identidad_confirmada: s.estado='VERIFICANDO_IDENTIDAD'; return
  if s.contexto['necesita_asesor']: s.estado='FINALIZADA'; s.finalizada=True; return
  if s.contexto.get('fecha_propuesta'): s.estado='CONFIRMANDO_SIGUIENTE_PASO'; return
  if s.contexto.get('intencion')=='NO_PUEDE_PAGAR': s.estado='BUSCANDO_FECHA'; return
  s.estado='EXPLORANDO_SITUACION'
 def _persist(self,s): save_beany_state(s.session_id,s.usuario_id,s.conversacion_id,s.estado,s.identidad_confirmada,s.contexto)
 def process_message(self,sid,msg):
  s=self.get_session(sid); t=norm(msg); s.historial.append({'role':'user','content':msg})
  if s.conversacion_id: save_message(s.conversacion_id,'USUARIO',msg)
  if s.estado=='VERIFICANDO_IDENTIDAD':
   if any(x in t for x in NEG): s.estado='FINALIZADA'; s.finalizada=True
   elif any(x in t for x in CONF): s.identidad_confirmada=True; s.estado='EXPLORANDO_SITUACION'
  else: self._update_context(s,msg); self._update_state(s)
  self._persist(s)
  response=generate_response({**s.public_context(),'objetivo_actual':OBJECTIVES.get(s.estado,'MANTENER_CONVERSACION')},s.historial)
  s.historial.append({'role':'assistant','content':response})
  if s.conversacion_id: save_message(s.conversacion_id,'ASISTENTE',response)
  self._persist(s); s.last_response=response; return s
 def finish_session(self,sid):
  s=self.get_session(sid); s.estado='FINALIZADA'; s.finalizada=True
  if s.conversacion_id: close_conversation(s.conversacion_id)
  self._persist(s); return s
