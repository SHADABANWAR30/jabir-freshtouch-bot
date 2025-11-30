# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

from bot import (
    load_model,
    detect_language,
    handle_small_talk_and_meta,
    faq_answer,
    generate_reply,
)

app = FastAPI()

# ✅ Domains allowed to call this API
origins = [
    "https://fabrico.ae",
    "https://www.fabrico.ae",
    "https://fabrico.vercel.app",  # if you use this preview domain
    "http://localhost:5173",       # Vite dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once on startup
tokenizer, model = load_model()

# 🔹 Per-session histories (simple in-memory dict)
# key: session_id, value: history_text string
histories: Dict[str, str] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # 👈 new: optional session id from frontend


class ChatResponse(BaseModel):
    reply: str


@app.post("/jabir/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    global histories

    user_text = (req.message or "").strip()
    if not user_text:
        return ChatResponse(
            reply="Please type a question about laundry, prices, pickup or offers 😊"
        )

    # 🔹 Use session_id if provided, otherwise fall back to a shared "default"
    session_id = req.session_id or "default"

    history_text = histories.get(session_id, "")

    lang = detect_language(user_text)

    # 0) Small talk: hi, thanks, compliments, who are you, etc.
    small = handle_small_talk_and_meta(user_text, lang)
    if small is not None:
        history_text = (history_text + f"\nUser: {user_text}\nJabir: {small}").strip()
        histories[session_id] = history_text
        return ChatResponse(reply=small)

    # 1) FAQ / business logic: prices, pickup, offers, WhatsApp, etc.
    faq = faq_answer(user_text, lang)
    if faq is not None:
        history_text = (history_text + f"\nUser: {user_text}\nJabir: {faq}").strip()
        histories[session_id] = history_text
        return ChatResponse(reply=faq)

    # 2) Model reply
    history_text, bot_reply = generate_reply(
        tokenizer, model, history_text, user_text, lang
    )
    histories[session_id] = history_text

    return ChatResponse(reply=bot_reply)
