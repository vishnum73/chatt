from __future__ import annotations

import os
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "140"))

SYSTEM_PROMPT = """
You are EduBot, a friendly education chatbot for teachers and students.
You help with programming, mathematics, formulas, science, lesson planning,
quizzes, study notes, examples, and step-by-step explanations.
Reply like a normal helpful chatbot: clear, direct, and concise.
Keep normal replies under 8 short lines unless the user asks for detail.
For programming, give one correct working code example and 2-3 bullet explanations.
For formulas, show the formula, define variables briefly, then give one small example.
For homework-like questions, teach the method instead of only giving the final answer.
If the user asks for a short answer, keep it short.
""".strip()

HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TeachMate Ollama Chatbot</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --ink: #162033;
      --muted: #637083;
      --line: #dfe5ef;
      --accent: #2364aa;
      --accent-dark: #174a80;
      --soft: #eaf2fb;
      --teacher: #fff7e6;
      --shadow: 0 18px 50px rgba(28, 39, 58, 0.12);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        linear-gradient(135deg, rgba(35, 100, 170, 0.10), rgba(20, 133, 116, 0.08)),
        var(--bg);
      color: var(--ink);
    }

    .app {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr auto;
      max-width: 1120px;
      margin: 0 auto;
      padding: 22px;
      gap: 16px;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 14px 0;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .mark {
      width: 44px;
      height: 44px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      color: white;
      font-weight: 800;
      background: linear-gradient(135deg, #2364aa, #168573);
      box-shadow: var(--shadow);
      flex: 0 0 auto;
    }

    h1 {
      margin: 0;
      font-size: 1.35rem;
      line-height: 1.15;
    }

    .subtitle {
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 0.94rem;
    }

    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.78);
      color: var(--muted);
      font-size: 0.9rem;
      white-space: nowrap;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 99px;
      background: #999;
    }

    .dot.ready {
      background: #14855f;
    }

    .dot.error {
      background: #c2410c;
    }

    main {
      display: grid;
      grid-template-columns: 290px minmax(0, 1fr);
      gap: 16px;
      min-height: 0;
    }

    aside,
    .chat-shell {
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    aside {
      padding: 16px;
      align-self: start;
    }

    .side-title {
      margin: 0 0 10px;
      font-size: 0.86rem;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 800;
    }

    .quick-list {
      display: grid;
      gap: 8px;
      margin-bottom: 18px;
    }

    .quick {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--ink);
      padding: 10px 11px;
      text-align: left;
      cursor: pointer;
      font: inherit;
      line-height: 1.25;
    }

    .quick:hover,
    .quick:focus-visible {
      border-color: var(--accent);
      outline: none;
      background: var(--soft);
    }

    label {
      display: block;
      margin-bottom: 7px;
      font-size: 0.86rem;
      font-weight: 700;
      color: var(--muted);
    }

    select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: white;
      padding: 10px;
      font: inherit;
      color: var(--ink);
      margin-bottom: 14px;
    }

    .note {
      margin: 0;
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.45;
    }

    .chat-shell {
      display: grid;
      grid-template-rows: 1fr auto;
      min-height: 620px;
      overflow: hidden;
    }

    .messages {
      min-height: 0;
      overflow-y: auto;
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .message {
      max-width: 82%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      line-height: 1.48;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .bot {
      align-self: flex-start;
      background: var(--panel);
    }

    .user {
      align-self: flex-end;
      color: #0b2540;
      background: var(--teacher);
      border-color: #efd392;
    }

    .composer {
      border-top: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.95);
      padding: 14px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
    }

    textarea {
      width: 100%;
      min-height: 54px;
      max-height: 170px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px 14px;
      color: var(--ink);
      font: inherit;
      line-height: 1.35;
    }

    textarea:focus {
      border-color: var(--accent);
      outline: 3px solid rgba(35, 100, 170, 0.16);
    }

    .send {
      min-width: 104px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: white;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
      padding: 0 18px;
    }

    .send:hover {
      background: var(--accent-dark);
    }

    .send:disabled {
      cursor: wait;
      opacity: 0.66;
    }

    footer {
      color: var(--muted);
      font-size: 0.86rem;
      text-align: center;
    }

    @media (max-width: 820px) {
      .app {
        padding: 14px;
      }

      header,
      main {
        display: block;
      }

      header {
        margin-bottom: 12px;
      }

      .status {
        margin-top: 12px;
      }

      aside {
        margin-bottom: 12px;
      }

      .chat-shell {
        min-height: 560px;
      }

      .message {
        max-width: 94%;
      }

      .composer {
        grid-template-columns: 1fr;
      }

      .send {
        min-height: 48px;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="brand">
        <div class="mark" aria-hidden="true">T</div>
        <div>
          <h1>TeachMate Ollama Chatbot</h1>
          <p class="subtitle">A classroom-ready assistant for teachers, tutors, and course teams.</p>
        </div>
      </div>
      <div class="status" title="Backend and Ollama connection status">
        <span id="statusDot" class="dot"></span>
        <span id="statusText">Checking Ollama...</span>
      </div>
    </header>

    <main>
      <aside aria-label="Teacher tools">
        <p class="side-title">Start with</p>
        <div class="quick-list">
          <button class="quick" data-mode="programming" data-prompt="Explain Python for loops with one small code example.">Programming</button>
          <button class="quick" data-mode="formula" data-prompt="Explain the area of a circle formula and solve an example with radius 7 cm.">Formula</button>
          <button class="quick" data-mode="general" data-prompt="Explain Newton's second law in simple language with one example.">Concept</button>
          <button class="quick" data-mode="teacher" data-prompt="Create a 30 minute lesson plan about photosynthesis for grade 7.">Lesson plan</button>
        </div>

        <label for="mode">Education mode</label>
        <select id="mode">
          <option value="general">General education</option>
          <option value="programming">Programming helper</option>
          <option value="formula">Formula solver</option>
          <option value="teacher">Teacher support</option>
          <option value="tutor">Student tutor</option>
          <option value="course">Course content helper</option>
        </select>

        <p class="note">
          This page talks to your local Ollama server. For Coursera or another LMS, embed this page URL in an iframe or connect the /chat API from your platform.
        </p>
      </aside>

      <section class="chat-shell" aria-label="Chatbot">
        <div id="messages" class="messages">
          <div class="message bot">Hello. I can help create lesson plans, quizzes, rubrics, explanations, discussion prompts, and feedback comments. What are you teaching today?</div>
        </div>

        <form id="chatForm" class="composer">
          <textarea id="messageInput" name="message" placeholder="Ask for a lesson plan, quiz, rubric, concept explanation, or feedback idea..." required></textarea>
          <button id="sendButton" class="send" type="submit">Send</button>
        </form>
      </section>
    </main>

    <footer>
      Using Ollama model: <strong id="modelName">loading</strong>
    </footer>
  </div>

  <script>
    const messages = document.getElementById("messages");
    const form = document.getElementById("chatForm");
    const input = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const mode = document.getElementById("mode");
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");
    const modelName = document.getElementById("modelName");
    const history = [];

    function addMessage(role, text) {
      const bubble = document.createElement("div");
      bubble.className = `message ${role === "user" ? "user" : "bot"}`;
      bubble.textContent = text;
      messages.appendChild(bubble);
      messages.scrollTop = messages.scrollHeight;
      return bubble;
    }

    function setStatus(state, text) {
      statusDot.className = `dot ${state}`;
      statusText.textContent = text;
    }

    async function checkHealth() {
      try {
        const response = await fetch("/health");
        const data = await response.json();
        modelName.textContent = data.model;
        setStatus(data.ollama_ready ? "ready" : "error", data.ollama_ready ? "Ollama ready" : "Ollama not reachable");
      } catch (error) {
        setStatus("error", "Backend not reachable");
      }
    }

    async function sendMessage(text) {
      addMessage("user", text);
      const requestHistory = history.slice(-8);
      const thinking = addMessage("bot", "Thinking... this can take a few seconds when Ollama is loading.");
      sendButton.disabled = true;
      let timeout;
      let slowNotice;

      try {
        const controller = new AbortController();
        timeout = setTimeout(() => controller.abort(), 120000);
        slowNotice = setTimeout(() => {
          thinking.textContent = "Still working... local Ollama can be slow on the first answer.";
        }, 15000);
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            message: text,
            mode: mode.value,
            history: requestHistory
          })
        });
        clearTimeout(timeout);
        clearTimeout(slowNotice);

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Chat request failed");
        }

        thinking.textContent = data.reply;
        history.push({ role: "user", content: text });
        history.push({ role: "assistant", content: data.reply });
      } catch (error) {
        clearTimeout(timeout);
        clearTimeout(slowNotice);
        const message = error.name === "AbortError"
          ? "The model took too long to answer. Try a shorter question or use a smaller Ollama model."
          : error.message;
        thinking.textContent = `I could not get a reply yet. ${message}`;
      } finally {
        sendButton.disabled = false;
        input.focus();
      }
    }

    document.querySelectorAll(".quick").forEach((button) => {
      button.addEventListener("click", () => {
        input.value = button.dataset.prompt;
        if (button.dataset.mode) {
          mode.value = button.dataset.mode;
        }
        input.focus();
      });
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      await sendMessage(text);
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    checkHealth();
  </script>
</body>
</html>
"""


app = FastAPI(title="TeachMate Ollama Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    mode: Literal["general", "programming", "formula", "teacher", "tutor", "course"] = "general"
    history: list[Message] = Field(default_factory=list, max_length=12)


class ChatResponse(BaseModel):
    reply: str


def mode_instruction(mode: str) -> str:
    instructions = {
        "general": "Answer as a friendly education chatbot. Keep most answers concise and useful.",
        "programming": "Focus on programming help. Include correct code, explain errors, and use simple examples.",
        "formula": "Focus on formulas and calculations. Show the formula, substitute values, and explain each step.",
        "teacher": "Focus on practical teacher support and classroom-ready materials.",
        "tutor": "Guide students Socratically. Explain concepts and give hints before answers.",
        "course": "Help build online course content, module outlines, activities, and assessments.",
    }
    return instructions.get(mode, instructions["general"])


def format_instruction(mode: str) -> str:
    if mode == "programming":
        return (
            "Answer in under 90 words. Include one small working code block and 2 short bullets. "
            "Do not add extra warnings or unrelated sections."
        )
    if mode == "formula":
        return (
            "Answer in under 100 words. Show the formula, define variables briefly, "
            "then solve one small example."
        )
    return "Answer in under 120 words unless I ask for more detail. Finish with a complete sentence."


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    return HTML_PAGE


@app.get("/embed", response_class=HTMLResponse)
async def embed() -> str:
    return HTML_PAGE


@app.get("/health")
async def health() -> dict[str, str | bool]:
    ready = False
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            ready = response.status_code == 200
    except httpx.HTTPError:
        ready = False

    return {
        "app": "ok",
        "ollama_url": OLLAMA_URL,
        "model": OLLAMA_MODEL,
        "num_predict": OLLAMA_NUM_PREDICT,
        "ollama_ready": ready,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    user_content = f"{request.message}\n\nResponse rules: {format_instruction(request.mode)}"
    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{mode_instruction(request.mode)}"},
        *[message.model_dump() for message in request.history[-10:]],
        {"role": "user", "content": user_content},
    ]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": OLLAMA_NUM_PREDICT,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            reply = data.get("message", {}).get("content", "").strip()
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama is not reachable at {OLLAMA_URL}. Start Ollama and try again.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned {exc.response.status_code}: {exc.response.text}",
        ) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                f"Ollama did not reply within {OLLAMA_TIMEOUT:.0f} seconds. "
                "The first reply can be slow while a model loads; try again or use a smaller model."
            ),
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Error talking to Ollama: {exc}") from exc

    if not reply:
        raise HTTPException(status_code=502, detail="Ollama returned an empty reply.")

    return ChatResponse(reply=reply)
