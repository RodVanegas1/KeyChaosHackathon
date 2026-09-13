# Beany · Bancoagrícola — Voz

Proyecto Vite + React para la demo de voz de Beany.

## Requisitos
- Node.js 20.19+ o 22.12+
- npm
- Chrome o Edge para reconocimiento de voz
- Ollama local (si se usa el modo LLM local)

## Ejecutar
Abre PowerShell directamente en esta carpeta, donde está `package.json`:

```powershell
npm install
npm run dev
```

Luego abre la URL que muestre Vite, normalmente:

`http://localhost:5173`

## Importante
Esta versión deja `package.json` en la raíz del proyecto para que no haya que entrar a una subcarpeta después de descomprimir el ZIP.

Variables opcionales:
- `VITE_OLLAMA_URL`
- `VITE_OLLAMA_MODEL`
- `VITE_BACKEND_URL`
