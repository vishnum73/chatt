from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import ollama

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


class ChatRequest(BaseModel):
    prompt: str


@app.post("/chat")
def chat(request: ChatRequest):
    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "user",
                "content": request.prompt,
            }
        ],
    )

    answer = response["message"]["content"]

    return {
        "response": answer
    }
#uvicorn main:app --reload