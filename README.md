## Running AIdventure (minimal)

This project contains a FastAPI backend (in `server/`) and a Vite + React frontend (in `web/`).

Below are minimal, exact PowerShell commands for a development run on Windows (PowerShell). These steps assume you have Python 3.11+ and Node.js + npm installed.

1) Backend (Python)

Open PowerShell in the repository root and run:

```powershell
# create and activate a venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# install Python deps
pip install -r requirements.txt

# start the backend on port 8000
uvicorn server.server:app --reload --port 8000
```

Notes:
- If you will use the Groq or Gemini LLM providers, set the corresponding environment variables before running (in the same PowerShell session):

```powershell
$env:INTENT_PROVIDER = 'groq'           # or 'gemini'
$env:INTENT_MODEL = 'llama-3.1-8b-instant'
$env:NARRATION_PROVIDER = 'groq'
$env:NARRATION_MODEL = 'llama-3.1-8b-instant'
# API keys (optional / provider-specific)
$env:GROQ_API_KEY = 'your_groq_key_here'
$env:GEMINI_API_KEY = 'your_gemini_key_here'
```

- The server already enables CORS for development (allow_origins = ["*"]).
- The server keeps sessions in-memory (no DB). Stopping the process resets all sessions.

2) Frontend (web)

Open another PowerShell and run:

```powershell
cd web
npm install
npm run dev
```

Vite will start the dev server (usually at http://localhost:5173).

Development note about backend URL
- The frontend's client currently calls `/api/turn` (relative path). When running the frontend dev server on a different port (5173) you have two options:
  1. Edit `web/src/api/client.ts` and change the fetch URL to the full backend URL:
     replace `fetch("/api/turn", ...)` with `fetch("http://localhost:8000/api/turn", ...)`
  2. Or configure a Vite dev proxy in `web/vite.config.ts` to forward `/api` requests to `http://localhost:8000`.

Either approach works; the backend allows CORS for development.

3) Quick smoke test

- With the backend running at port 8000 and the frontend dev server running, open the frontend URL (http://localhost:5173).
- The UI will automatically send the initial "Start the adventure." turn when it mounts.

Optional: Build and serve the frontend from a static server
- If you'd like to serve frontend and backend from the same origin, build the web app and serve the built files from any static host. The backend doesn't serve static assets by default — you can use a static file server or add a small static route to the backend if desired.

Questions / next steps
- I can add a `vite` proxy example, a small script to serve the frontend from the backend, or a `requirements-dev.txt` with pinned versions. Tell me which you'd prefer and I'll add it.
