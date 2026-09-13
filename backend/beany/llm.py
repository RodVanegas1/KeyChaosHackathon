import json
import os
import urllib.request
import urllib.error
from typing import Any, Dict


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


SYSTEM_PROMPT = """
Eres Beany, asistente virtual femenina de Bancoagrícola para cobranza preventiva.

Tu función es conversar de forma natural, breve, empática y directa con el cliente.
La lógica de negocio y el estado de la conversación los controla el backend; tú no debes inventarlos ni modificarlos.

REGLAS:
- Responde únicamente en español.
- Máximo dos oraciones cortas.
- No digas "¿en qué te puedo ayudar?".
- No repitas preguntas ya contestadas.
- No vuelvas a validar la identidad si el backend indica que está confirmada.
- No inventes saldos, fechas exactas, beneficios, descuentos, intereses, consecuencias ni confirmaciones de pago.
- Usa solamente la información autorizada que aparece en el contexto.
- Haz una sola pregunta cuando el estado actual lo requiera.
- Mantente en cobranza preventiva de Bancoagrícola.
- Si el cliente pide un asesor humano, acepta la solicitud de forma breve.
- Si el cliente se despide, responde con una despedida breve.
"""


def _compact(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def generate_response(session_context: Dict[str, Any], history: list[Dict[str, str]]) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "CONTEXTO ESTRUCTURADO DE LA LLAMADA:\n"
                + _compact(session_context)
            ),
        },
    ]

    # Keep enough recent turns for continuity without flooding a small local model.
    messages.extend(history[-10:])

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.35,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"No se pudo consultar Ollama: {exc}") from exc

    content = data.get("message", {}).get("content", "").strip()
    if not content:
        raise RuntimeError("Ollama devolvió una respuesta vacía.")

    return content
