from fastapi import APIRouter, HTTPException
from .schemas import (
    StartSessionRequest,
    StartSessionResponse,
    MessageRequest,
    MessageResponse,
    FinishSessionRequest,
    FinishSessionResponse,
)
from .service import BeanyService


router = APIRouter()
service = BeanyService()


@router.post("/start", response_model=StartSessionResponse)
def start_session(data: StartSessionRequest):
    session = service.start_session(data.telefono)

    return StartSessionResponse(
        session_id=session.session_id,
        cliente_encontrado=session.usuario_id is not None,
        estado=session.estado,
        nombre=session.nombre,
        usuario_id=session.usuario_id,
        conversacion_id=session.conversacion_id,
    )


@router.post("/message", response_model=MessageResponse)
def process_message(data: MessageRequest):
    try:
        session = service.process_message(data.session_id, data.mensaje)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return MessageResponse(
        session_id=session.session_id,
        estado=session.estado,
        respuesta=getattr(session, "last_response", ""),
        identidad_confirmada=session.identidad_confirmada,
        contexto=session.contexto,
    )


@router.post("/finish", response_model=FinishSessionResponse)
def finish_session(data: FinishSessionRequest):
    try:
        session = service.get_session(data.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    session.estado = "FINALIZADA"
    session.finalizada = True

    return FinishSessionResponse(
        session_id=session.session_id,
        estado=session.estado,
        conversacion_id=session.conversacion_id,
    )
