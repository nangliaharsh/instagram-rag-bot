import os, hmac, hashlib
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException, Query

load_dotenv()
from rag import answer

app = FastAPI()
VERIFY_TOKEN = os.getenv("IG_VERIFY_TOKEN")
APP_SECRET = os.getenv("IG_APP_SECRET", "")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
GRAPH_URL = "https://graph.instagram.com/v21.0/me/messages"

seen_mids: set[str] = set()  # simple dedup; use Redis in production


def valid_signature(body: bytes, header: str | None) -> bool:
    if not header or not APP_SECRET:
        return False
    expected = "sha256=" + hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


async def send_reply(recipient_id: str, text: str):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            GRAPH_URL,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            json={"recipient": {"id": recipient_id}, "message": {"text": text}},
        )
        if r.status_code >= 400:
            print("SEND ERROR:", r.status_code, r.text)
        else:
            print("REPLY SENT to", recipient_id)


async def handle_message(sender_id: str, text: str):
    try:
        reply = answer(text)
        await send_reply(sender_id, reply)
    except Exception as e:
        print("HANDLER ERROR:", repr(e))


# Meta webhook verification
@app.get("/webhook")
async def verify(mode: str = Query(None, alias="hub.mode"),
                 token: str = Query(None, alias="hub.verify_token"),
                 challenge: str = Query(None, alias="hub.challenge")):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(403, "Verification failed")


# Incoming events
@app.post("/webhook")
async def webhook(request: Request, bg: BackgroundTasks):
    body = await request.body()
    if not valid_signature(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(403, "Bad signature")

    data = await request.json()
    print("WEBHOOK PAYLOAD:", data)

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            msg = event.get("message", {})
            if msg.get("is_echo") or not msg.get("text"):
                continue
            mid = msg.get("mid")
            if mid in seen_mids:
                continue
            seen_mids.add(mid)

            # Only react to story replies
            if "reply_to" in msg and "story" in msg["reply_to"]:
                bg.add_task(handle_message, event["sender"]["id"], msg["text"])
    return {"status": "ok"}


# Demo endpoint: test the RAG reply without Instagram
@app.post("/simulate")
async def simulate(payload: dict):
    return {"question": payload["text"], "reply": answer(payload["text"])}