from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BeanySession:
    session_id: str
    telefono: str
    usuario_id: Optional[int] = None
    nombre: Optional[str] = None
    credito_id: Optional[int] = None
    conversacion_id: Optional[int] = None

    estado: str = "INICIO"
    identidad_confirmada: bool = False
    finalizada: bool = False

    historial: List[Dict[str, str]] = field(default_factory=list)

    contexto: Dict[str, Any] = field(default_factory=lambda: {
        "intencion": None,
        "motivo": None,
        "fecha_propuesta": None,
        "monto_mencionado": None,
        "obstaculo": None,
        "necesita_asesor": False,
    })

    def public_context(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "estado": self.estado,
            "cliente": {
                "usuario_id": self.usuario_id,
                "nombre": self.nombre,
            },
            "identidad_confirmada": self.identidad_confirmada,
            "contexto": self.contexto,
        }
