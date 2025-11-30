from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bot import answer

app = FastAPI()

origins = [
    "https://fabrico.ae",
    "https://www.fabrico.ae",
    "https://fabrico.vercel.app",  # your Vercel domain if any
    "http://localhost:5173",       # local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # accepted but not used


class ChatResponse(BaseModel):
    reply: str


@app.post("/jabir/chat", response_model=ChatResponse)
def jabir_chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        return ChatResponse(
            reply="Please type a question about laundry, prices, pickup or offers 😊"
        )

    reply = answer(user_text)
    return ChatResponse(reply=reply)
