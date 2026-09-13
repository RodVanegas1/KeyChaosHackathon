# KeyChaosHackathon — Beany · Bancoagrícola

Prototipo desarrollado para un hackathon de **Bancoagrícola**: un sistema de **cobranza preventiva** que combina un backend en FastAPI + MySQL, un LLM (Ollama) para redactar respuestas naturales, un asistente de voz llamado **Beany**, un mock de app bancaria (PWA en React) y una capa de automatización con **n8n** pensada para WhatsApp.

> Este repositorio contiene **varios prototipos en distintos niveles de madurez** (backend "oficial", un backend legado más completo, y un frontend de voz que hoy corre de forma independiente). Este README documenta qué hace cada carpeta, cómo se ejecuta y qué está realmente conectado con qué — ver la sección [Estado real de la integración](#estado-real-de-la-integración-importante) antes de asumir que todo habla entre sí.

---

## Índice

1. [Estructura del repositorio](#estructura-del-repositorio)
2. [Arquitectura general](#arquitectura-general)
3. [Backend (`backend/`)](#backend-backend)
4. [Beany — asistente de voz (`beany/`)](#beany--asistente-de-voz-beany)
5. [Frontend PWA (`frontend/`)](#frontend-pwa-frontend)
6. [Base de datos (`bd/`)](#base-de-datos-bd)
7. [n8n (`n8n/`)](#n8n-n8n)
8. [Voz por Whisper local (`hackathon/voice/`)](#voz-por-whisper-local-hackathonvoice)
9. [Estado real de la integración (importante)](#estado-real-de-la-integración-importante)
10. [Seguridad — acción requerida](#seguridad--acción-requerida)
11. [Cómo levantar todo en local](#cómo-levantar-todo-en-local)
12. [Pendientes / roadmap](#pendientes--roadmap)
13. [Créditos](#créditos)

---

## Estructura del repositorio

```text
KeyChaosHackathon-main/
├── backend/                  # API FastAPI + MySQL (versión "oficial" y versión legada)
│   ├── main.py                  # App actual: monta el router de Beany (/api/beany/*)
│   ├── main_legacy.py           # Versión anterior, más completa: dashboard, WhatsApp, compromisos
│   ├── requirements.txt
│   ├── database/
│   │   └── connection.py        # Conexión a MySQL (Railway) — credenciales hardcodeadas ⚠️
│   ├── beany/                   # Lógica de sesión, estados y LLM de Beany
│   │   ├── router.py            # Endpoints /start, /message, /finish
│   │   ├── service.py           # Máquina de estados + extracción de intención/fecha/monto
│   │   ├── session.py           # Modelo de sesión en memoria (BeanySession)
│   │   ├── repository.py        # Acceso a datos (usuario, credito, conversacion, mensaje...)
│   │   ├── llm.py                # Llamada a Ollama (prompt del sistema de Beany)
│   │   ├── schemas.py            # Modelos Pydantic de request/response
│   │   └── beany_sesion.sql      # Tabla de persistencia de sesión
│   └── dashboard/                # Paquete vacío, reservado para métricas del dashboard
│
├── beany/                     # Frontend de voz de Beany (React + Vite), standalone
│   ├── src/
│   │   ├── main.jsx              # STT (Web Speech API) + TTS + llamada directa a Ollama
│   │   └── prompt.js             # MASTER_PROMPT: reglas de tono/negocio para Beany
│   ├── package.json
│   ├── README.md
│   └── *.zip                     # Snapshots/versiones anteriores de esta app (histórico)
│
├── frontend/                  # Mock de app móvil de Bancoagrícola (React + Vite + Docker + PWA)
│   ├── src/main.jsx              # Vista de usuario (home bancario) + vista de analista (dashboard)
│   ├── Dockerfile / docker-compose.yml / nginx.conf
│   └── public/                   # Manifest PWA, service worker, íconos
│
├── bd/                         # Esquema y datos de la base de datos
│   ├── mora_demo_v1.sql          # DDL: usuario, credito, pago, evaluacion_riesgo, conversacion...
│   ├── datos_semilla_v2.sql      # 6 usuarios arquetipo con historial de pago realista
│   └── modelo_negocio_mora_demo_v1.md  # Documento de diseño del modelo de negocio
│
├── n8n/                         # Orquestación (pensada para el canal WhatsApp)
│   ├── docker-compose.yml
│   ├── workflows/cobranza-demo.json
│   └── README.md / START-HERE.txt
│
├── hackathon/voice/whisper-local/
│   └── docker-compose.yml       # Servicio whisper.cpp para STT local (alternativa al navegador)
│
└── .gitignore
```

---

## Arquitectura general

El principio de diseño que atraviesa todo el proyecto (documentado en `bd/modelo_negocio_mora_demo_v1.md` y replicado en el prompt de Beany) es:

> **El backend decide; el LLM redacta.**

- El **backend** es responsable de identidad, estado de la conversación, reglas de negocio (p. ej. la ventana de 30 días para un compromiso de pago) y de la persistencia en MySQL.
- El **LLM (Ollama, `llama3.2:3b`)** solo interpreta lenguaje natural y redacta la respuesta hablada; no tiene autoridad para modificar saldos, fechas oficiales, ni confirmar compromisos por sí mismo.

```text
Cliente ⇄ Voz/WhatsApp ⇄ Backend (FastAPI) ⇄ MySQL (Railway)
                                 │
                                 ▼
                              Ollama (LLM)
```

---

## Backend (`backend/`)

Hay **dos versiones** del backend en la misma carpeta:

### `main.py` — versión actual, montada en producción del prototipo

App mínima (`Bancoagrícola - Beany Backend v2.2.0`) que solo expone:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Health check simple |
| GET | `/health` | Verifica conexión a MySQL |
| POST | `/api/beany/start` | Crea sesión, busca cliente por teléfono |
| POST | `/api/beany/message` | Procesa un turno de conversación |
| POST | `/api/beany/finish` | Cierra la sesión y la conversación |

La lógica vive en el paquete `backend/beany/`:

- **`service.py`** — máquina de estados (`INICIO → VERIFICANDO_IDENTIDAD → EXPLORANDO_SITUACION → BUSCANDO_FECHA → CONFIRMANDO_SIGUIENTE_PASO → FINALIZADA`), reconocimiento de frases de confirmación/negación de identidad, y extracción por reglas simples (regex) de intención, motivo, fecha y monto mencionados.
- **`session.py`** — `BeanySession`: dataclass con `session_id`, `usuario_id`, `estado`, `identidad_confirmada`, `historial` y el `contexto` estructurado (`intencion`, `motivo`, `fecha_propuesta`, `monto_mencionado`, `obstaculo`, `necesita_asesor`).
- **`repository.py`** — funciones de acceso a datos: buscar cliente por teléfono, crédito activo, crear/recuperar conversación, guardar mensajes, y guardar/cargar el estado de Beany (tabla `beany_sesion`, definida en `beany_sesion.sql`).
- **`llm.py`** — llama a Ollama (`OLLAMA_URL`, por defecto `http://127.0.0.1:11434/api/chat`; `OLLAMA_MODEL`, por defecto `llama3.2:3b`) con un `SYSTEM_PROMPT` que resume las reglas de negocio (no inventar saldos/fechas/beneficios, una sola pregunta por turno, no re-verificar identidad ya confirmada, etc.).

> **Nota:** el router actual **no expone** un endpoint `/api/beany/identify` (identificación por nombre) — solo `/start` (por teléfono), `/message` y `/finish`.

**Variables de entorno relevantes:**

```bash
ALLOWED_ORIGINS=*          # orígenes permitidos por CORS (coma-separados)
OLLAMA_URL=http://127.0.0.1:11434/api/chat
OLLAMA_MODEL=llama3.2:3b
```

**Ejecutar:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### `main_legacy.py` — versión anterior, más completa

Una API más grande (`Bancoagrícola - Prevención de Mora API v1.0.0`) pensada para el canal **WhatsApp** (no voz) y para un **dashboard de analista**. Incluye, además del health check:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/dashboard/metrics` | KPIs: riesgo alto, conversaciones activas, compromisos, monto recuperado |
| GET | `/api/dashboard/gestiones` | Listado de clientes ordenado por nivel/score de riesgo |
| GET | `/api/clientes/por-telefono/{telefono}` | Contexto completo del cliente (usuario, crédito, pago relevante, riesgo, historial) |
| POST | `/api/webhook/whatsapp` | Punto de entrada de un mensaje de WhatsApp (vía n8n): localiza/crea conversación y guarda el mensaje. **No ejecuta el LLM aquí.** |
| GET | `/api/conversaciones/{id}/mensajes` | Historial de una conversación |
| POST | `/api/conversaciones/mensaje` | Guarda un mensaje (usuario/asistente/sistema), con soporte de deduplicación por `external_message_id` |
| POST | `/api/conversaciones/{id}/completar` | Cierra una conversación |
| POST | `/api/conversaciones/resumen` | Guarda el resumen estructurado que produce el LLM (intención, compromiso, resultado) |
| POST | `/api/compromisos` | Registra un compromiso de pago, **validando en backend**: crédito activo, conversación válida, regla de 30 días, monto ≤ saldo pendiente |

Este archivo no está montado por `main.py`; queda como referencia/legado de un diseño más completo orientado a WhatsApp + dashboard, del cual `main.py`/`beany/` heredan las reglas de negocio (30 días, no inventar información, etc.).

### `database/connection.py`

Función `get_db_connection()` que abre una conexión a un MySQL alojado en **Railway**. Ver advertencia en [Seguridad](#seguridad--acción-requerida): las credenciales están **hardcodeadas en el archivo**, en lugar de leerse de variables de entorno como sí hace `main_legacy.py` (`MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`).

---

## Beany — asistente de voz (`beany/`)

App independiente en React + Vite (`beany-bancoagricola-voz`) que corre **en el navegador** y hace lo siguiente:

1. Usa la **Web Speech API** del navegador (`SpeechRecognition`) para transcribir voz a texto (funciona en Chrome/Edge; requiere permiso de micrófono).
2. Elige al azar uno de 6 clientes válidos (`VALID_NAMES`, los mismos arquetipos de `bd/datos_semilla_v2.sql`) y abre la llamada con un saludo de verificación de identidad.
3. Interpreta la respuesta del cliente con reglas simples (regex) para confirmar/negar identidad, detectar intención de pago, fecha, monto y motivo.
4. Llama **directamente a Ollama** (`fetch` a `VITE_OLLAMA_URL`/`api/chat`, modelo `VITE_OLLAMA_MODEL`) usando el `MASTER_PROMPT` de `src/prompt.js` — un prompt muy detallado sobre tono, ritmo conversacional, no repetir preguntas, reglas de fecha (máx. 30 días), privacidad de datos, cierre de llamada, etc.
5. Reproduce la respuesta con `speechSynthesis` (TTS del navegador), intentando elegir una voz femenina en español.
6. Muestra en pantalla un panel de "Datos para analistas" con lo que se pudo inferir de la conversación (identidad verificada, intención, motivo, fecha, monto, resultado).

**Variables de entorno (`.env` en esta carpeta):**

```bash
VITE_OLLAMA_URL=http://127.0.0.1:11434
VITE_OLLAMA_MODEL=llama3.2:3b
VITE_BACKEND_URL=            # declarada pero no usada actualmente (ver sección de integración)
```

**Ejecutar:**

```bash
cd beany
npm install
npm run dev     # abre normalmente en http://localhost:5173
```

Requiere Node 20.19+/22.12+, y Chrome o Edge para el reconocimiento de voz. Si se quiere usar Ollama local, debe estar corriendo con el modelo `llama3.2:3b` descargado (`ollama pull llama3.2:3b`).

> La carpeta incluye además varios `.zip` (`bancoagricola-beany-voz-natural-final*.zip`, `bancoagricola-beany-contexto*.zip`) que son snapshots de versiones anteriores de esta misma app, y un `main.jsx.bak` de respaldo. Son histórico de iteración, no se ejecutan.

---

## Frontend PWA (`frontend/`)

Mock de la app móvil de Bancoagrícola (React + Vite + Docker), con dos vistas dentro de `App()`:

- **`UserView`** — pantalla de inicio de cliente: header con accesos (Coach Financiero, mensajería, QR), tarjeta de "Mis tarjetas", accesos rápidos, promociones, y widgets de gamificación (racha de pagos, meta adicional con anillo de progreso). Es **solo visual**: los botones son placeholders para el equipo de backend, sin datos personales, de cuenta o de transacciones reales.
- **`AdminView`** — dashboard de analista con un gráfico de pastel (distribución de cartera por riesgo alto/medio/bajo), buscador de clientes y una lista con los 6 arquetipos (datos **mock**, hardcodeados en el componente, no vienen de la API) con score de riesgo, saldo, días en mora y un botón "Iniciar Intervención IA".
- Alterna entre ambas vistas y modo claro/oscuro desde `App()`.

Incluye manifest y service worker mínimos para funcionar como PWA instalable (el `sw.js` no precachea el app shell, a propósito, para evitar pantallas en blanco por caché durante el hackathon).

**Ejecutar con Docker:**

```bash
cd frontend
docker compose up --build
# abre http://localhost:8080
```

**Ejecutar en local (sin Docker):**

```bash
cd frontend
npm install
npm run dev
```

---

## Base de datos (`bd/`)

- **`mora_demo_v1.sql`** — esquema completo en MySQL 8 (base `railway`): `usuario`, `credito`, `pago`, `evaluacion_riesgo`, `conversacion`, `mensaje`, `resumen_conversacion`, `compromiso_pago`, `perfil_usuario`. Incluye los `ENUM` de estados (crédito: `ACTIVO/PAGADO/VENCIDO/CANCELADO`; conversación: `INICIADA/EN_CURSO/COMPLETADA/CANCELADA/FALLIDA`; compromiso: `PENDIENTE/CUMPLIDO/INCUMPLIDO/CANCELADO`, etc.) y sus llaves foráneas/índices.
- **`datos_semilla_v2.sql`** — inserta los **6 usuarios arquetipo** usados en toda la demo (voz, frontend, dashboard), con perfil demográfico, crédito e historial de pagos coherente con su arquetipo:

  | Usuario | Arquetipo | Ocupación | Ingreso |
  |---|---|---|---|
  | Ana Beatriz Hernández | La Cumplidora Anticipada | Contadora | Fijo |
  | Douglas Alexander Portillo | El Fantasma | Mecánico automotriz independiente | Informal |
  | Marta Elena Cortez | El Filo de la Navaja | Dueña de pupusería | Informal |
  | Jorge Iván Meléndez | El Reincidente Rescatable | Vendedor por comisión | Variable |
  | Katherine Sofía Aguilar | La Negociadora Parcial | Agente de call center | Fijo |
  | Óscar Renato Villalta | El Imprevisto | Técnico de mantenimiento industrial | Fijo |

- **`modelo_negocio_mora_demo_v1.md`** — documento de diseño del modelo de negocio: separación LLM/backend, ciclo de vida de la evaluación de riesgo, regla de contacto preventivo, ciclo de vida del compromiso de pago, y alcance explícito de la V1 (qué sí y qué no cubre esta demo).

Para levantar la base localmente (o replicarla), ejecutar en orden: `mora_demo_v1.sql` → `datos_semilla_v2.sql` → `backend/beany/beany_sesion.sql`.

---

## n8n (`n8n/`)

Infraestructura local de **n8n** para orquestar el canal de WhatsApp (todavía no conectado a Twilio/Meta en este repo).

- `docker-compose.yml` levanta n8n en `http://localhost:5678`, con timezone `America/El_Salvador`.
- `workflows/cobranza-demo.json` es un workflow de prueba: un webhook (`POST /webhook/cobranza-demo`) que recibe `{customer_id, message}`, lo normaliza con un nodo de código y responde con un JSON de eco — todavía **no** conecta WhatsApp, IA ni Whisper.
- `.env.example` deja preparadas (comentadas) las variables `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` y `OPENAI_API_KEY` para cuando se conecten esas integraciones.

**Ejecutar:**

```bash
cd n8n
docker compose up -d
# abre http://localhost:5678, crea tu usuario local
# importa workflows/cobranza-demo.json desde n8n (Import from File)
```

Roadmap documentado en `n8n/README.md`: entrada de WhatsApp → memoria/contexto del cliente → agente de conversación empática → analyzer a JSON → registro para dashboard → seguimientos preventivos → voz con Whisper local.

---

## Voz por Whisper local (`hackathon/voice/`)

`whisper-local/docker-compose.yml` levanta un servicio **whisper.cpp** (`ghcr.io/ggml-org/whisper.cpp`) como servidor STT en `http://localhost:8081`, usando el modelo `ggml-base.bin` (se descarga en el volumen `whisper_models`). Es una alternativa a la Web Speech API del navegador para reconocimiento de voz local/offline; no está todavía conectado a `beany/` ni al backend en el código actual.

```bash
cd hackathon/voice/whisper-local
docker compose up -d
```

---

## Estado real de la integración (importante)

Para evitar confusiones al retomar el proyecto, así está conectado (o no) cada componente **en el código tal como está en este repo**:

| Componente | ¿Conectado a…? | Estado |
|---|---|---|
| `backend/main.py` (+ `beany/`) | MySQL (Railway), Ollama | ✅ Conectado y funcional (vía HTTP: `/api/beany/start`, `/message`, `/finish`) |
| `beany/` (frontend de voz) | Ollama | ✅ Llama directo a Ollama desde el navegador |
| `beany/` (frontend de voz) | `backend/main.py` | ⚠️ **No conectado en este build**: `VITE_BACKEND_URL` está declarada en `main.jsx` pero no se usa en ninguna llamada `fetch`. La identidad, la selección de cliente y el contexto se manejan **en el propio frontend** (array `VALID_NAMES` + regex), no vía `/api/beany/*`. |
| `frontend/` (PWA) | Backend / API | ⚠️ No conectado: `AdminView` usa datos mock hardcodeados (`mockData`) en lugar de `/api/dashboard/*`. |
| `n8n/` | WhatsApp / Twilio | ⚠️ No conectado: el workflow demo solo hace eco, sin llamar a `main_legacy.py` ni a ningún LLM. |
| `hackathon/voice/whisper-local` | `beany/` o backend | ⚠️ No conectado: servicio disponible pero no referenciado desde el código. |
| `backend/main_legacy.py` | MySQL | ✅ Funcional de forma independiente, pero **no está montado** por `main.py` (no se ejecuta salvo que se lance explícitamente). |

En resumen: el flujo de voz **end-to-end que sí funciona hoy** es *navegador → Web Speech API → Ollama → speechSynthesis*, sin pasar por FastAPI/MySQL. El backend con máquina de estados, persistencia e integración por teléfono (`backend/beany/`) es funcional por su cuenta (probado vía `/api/beany/*`), pero está pendiente **unir ambas piezas** para que el frontend de voz consuma esos endpoints en lugar de decidir identidad y contexto por su cuenta en el cliente.

---

## Seguridad — acción requerida

`backend/database/connection.py` tiene **hardcodeados en texto plano** el host, usuario, contraseña y nombre de la base de datos de MySQL en Railway, directamente en el código versionado. Esto es distinto del patrón usado en `main_legacy.py`, que sí lee estos valores desde variables de entorno (`MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`).

**Recomendado antes de seguir usando este repo:**

1. **Rotar la contraseña de esa base de datos en Railway de inmediato** (quedó expuesta en el historial de git).
2. Reemplazar `database/connection.py` para que lea de variables de entorno igual que `main_legacy.py`, y mover los valores reales a un `.env` **no versionado**.
3. Añadir `.env` al `.gitignore` (actualmente el `.gitignore` de la raíz solo ignora `frontend/node_modules/`).

Adicionalmente, la carpeta `beany/node_modules/` (~46 MB) está commiteada en el repositorio — conviene añadir `beany/node_modules/` y `**/__pycache__/` al `.gitignore` y limpiarlos del historial si el tamaño del repo es un problema.

---

## Cómo levantar todo en local

Orden sugerido para una demo completa:

```bash
# 1. Base de datos (MySQL 8 accesible, local o Railway)
mysql < bd/mora_demo_v1.sql
mysql < bd/datos_semilla_v2.sql
mysql < backend/beany/beany_sesion.sql

# 2. Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Ollama (en otra terminal)
ollama pull llama3.2:3b
ollama serve

# 4. Frontend de voz de Beany
cd beany
npm install
npm run dev          # http://localhost:5173

# 5. (Opcional) Mock de app bancaria
cd frontend
docker compose up --build   # http://localhost:8080

# 6. (Opcional) n8n
cd n8n
docker compose up -d         # http://localhost:5678
```

---

## Pendientes / roadmap

- [ ] Conectar `beany/` (frontend de voz) directamente a `/api/beany/start` y `/api/beany/message`, retirando la lógica de identidad/contexto que hoy vive en el cliente.
- [ ] Añadir el endpoint `/api/beany/identify` al router actual (existe en la documentación del proyecto pero no en `backend/beany/router.py`).
- [ ] Mover las credenciales de MySQL a variables de entorno (ver [Seguridad](#seguridad--acción-requerida)).
- [ ] Conectar `frontend/` (`AdminView`) a `/api/dashboard/metrics` y `/api/dashboard/gestiones` en lugar de datos mock.
- [ ] Conectar el workflow de n8n con WhatsApp/Twilio y con `main_legacy.py` (o su lógica migrada a `main.py`).
- [ ] Integrar `hackathon/voice/whisper-local` como alternativa de STT a la Web Speech API del navegador.
- [ ] Corregir el problema de codificación UTF-8 observado en respuestas mostradas por PowerShell durante pruebas.
- [ ] Endurecer la persistencia de sesión de Beany bajo reinicios y concurrencia.
- [ ] Reemplazar la extracción de intención/fecha/monto por regex (`service.py`, `main.jsx`) por componentes más robustos.

---

## Créditos

Prototipo desarrollado por el equipo para el hackathon de Bancoagrícola. Durante el desarrollo se usaron **Google Gemini** y **OpenAI ChatGPT** como herramientas de apoyo para generación/depuración de código y redacción de documentación; son independientes de **Ollama**, que es el LLM que Beany usa en producción para redactar sus respuestas.
