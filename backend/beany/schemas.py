from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class StartSessionRequest(BaseModel):
    telefono: str = Field(min_length=3, max_length=30)


class StartSessionResponse(BaseModel):
    session_id: str
    cliente_encontrado: bool
    estado: str
    nombre: Optional[str] = None
    usuario_id: Optional[int] = None
    conversacion_id: Optional[int] = None


class MessageRequest(BaseModel):
    session_id: str
    mensaje: str = Field(min_length=1)


class MessageResponse(BaseModel):
    session_id: str
    estado: str
    respuesta: str
    identidad_confirmada: bool
    contexto: Dict[str, Any] = {}


class FinishSessionRequest(BaseModel):
    session_id: str


class FinishSessionResponse(BaseModel):
    session_id: str
    estado: str
    conversacion_id: Optional[int] = None
