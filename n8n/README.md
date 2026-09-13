# Bancoagrícola Hackathon — n8n local

Esta carpeta contiene únicamente la infraestructura local de n8n para el proyecto.

## Levantar n8n

Desde esta carpeta:

```bash
docker compose up -d
```

Abrir:

http://localhost:5678

Para ver logs:

```bash
docker compose logs -f n8n
```

Para detener:

```bash
docker compose down
```

Los datos de n8n se guardan en el volumen Docker `n8n_data`.

## Workflow demo

`workflows/cobranza-demo.json` es un workflow de prueba local para validar la entrada y salida del flujo antes de conectar WhatsApp, IA o Whisper.

Importarlo desde n8n con **Import from File**.

Endpoint del demo:

```text
POST http://localhost:5678/webhook/cobranza-demo
```

Body JSON de ejemplo:

```json
{
  "customer_id": "DEMO-001",
  "message": "No puedo pagar este viernes, podría hacerlo el lunes."
}
```

## Próximos módulos

1. Entrada de WhatsApp.
2. Memoria/contexto del cliente.
3. Agente de conversación empática.
4. Analyzer de conversación a JSON.
5. Registro para dashboard.
6. Seguimientos preventivos.
7. Voz con Whisper local.

No guardar credenciales reales dentro del repo.
