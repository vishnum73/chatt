# TeachMate Ollama Chatbot

A FastAPI webpage chatbot for teacher-friendly education support. It connects to a local Ollama model and can be embedded into an LMS page with an iframe.

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Install and start Ollama, then pull the model used by the app:

```powershell
ollama pull mistral
ollama serve
```

## Run The Webpage

```powershell
.\run.ps1
```

Or run Uvicorn directly:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8010
```

Open:

```text
http://127.0.0.1:8010/
```

Embed-friendly route:

```text
http://127.0.0.1:8010/embed
```

Example iframe:

```html
<iframe
  src="http://127.0.0.1:8010/embed"
  width="100%"
  height="760"
  style="border:0;"
  title="TeachMate Chatbot">
</iframe>
```

## Configure

Edit `.env`:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=300
```

For Coursera or another education system, host this FastAPI app on a server reachable by that platform, then use the hosted `/embed` URL in the iframe.
