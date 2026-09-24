# Instagram Story-Reply Bot (RAG)

An AI auto-reply system for Instagram. When someone replies to a story, the bot retrieves the relevant answer from a knowledge base using a RAG pipeline and sends the reply back automatically in the DM.

## How it works

```
Story reply on Instagram
        |
        v
Meta webhook (POST /webhook)   -> signature verified, duplicates ignored
        |
        v
FastAPI backend                -> filters for story replies only
        |
        v
RAG pipeline
   1. Embed the question (all-MiniLM-L6-v2)
   2. Retrieve top 4 chunks from ChromaDB
   3. Generate a short answer with Groq / GPT-OSS 120B (via Groq)
        |
        v
Instagram Send API             -> reply delivered to the user's DM
```

## Tech stack

- **Backend:** FastAPI, Uvicorn, httpx
- **RAG:** LangChain, ChromaDB, sentence-transformers embeddings
- **LLM:** Groq (GPT-OSS 120B (via Groq))
- **Integration:** Meta Instagram Messaging API (webhooks + Send API)

## Project structure

```
instagram-rag-bot/
├── kb/                # knowledge base (.txt / .md files)
├── chroma_db/         # vector store, created by ingest.py
├── ingest.py          # loads kb/, chunks, embeds, stores in Chroma
├── rag.py             # retriever + LLM chain, answer()
├── main.py            # FastAPI app: /webhook and /simulate
├── requirements.txt
├── .env               # secrets (not committed)
└── README.md
```

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```
GROQ_API_KEY=your_groq_key
IG_ACCESS_TOKEN=your_instagram_access_token
IG_APP_SECRET=your_app_secret
IG_VERIFY_TOKEN=any_string_you_choose
```

Add your FAQs or docs to `kb/`, then build the index and start the server:

```powershell
python ingest.py
uvicorn main:app --reload --port 8000
```

To rebuild the index after editing the knowledge base, delete `chroma_db` first, then run `python ingest.py` again.

## Try it without Instagram

Open `http://localhost:8000/docs` and use `POST /simulate`:

```json
{"text": "What are your working hours?"}
```

Or from PowerShell:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/simulate -Method Post -ContentType "application/json" -Body '{"text": "Do you offer refunds?"}'
```

## Connecting to Instagram

1. Create an app at developers.facebook.com and add the **Instagram** product.
2. Connect a professional (Business or Creator) Instagram account.
3. Expose your local server: `ngrok http 8000`.
4. Set the webhook callback URL to `https://<your-ngrok-url>/webhook` with your verify token, and subscribe to the `messages` field.
5. Post a story from the connected account and reply to it from a tester account.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/webhook` | Meta webhook verification |
| POST | `/webhook` | Receives Instagram events, triggers the RAG reply |
| POST | `/simulate` | Tests the RAG answer without Instagram |

## Notes and limitations

- In development mode, only accounts with a role on the Meta app (admin, developer, tester) can trigger the bot. Public use requires Meta App Review for `instagram_business_manage_messages`.
- Meta's 24-hour messaging window applies: the bot can reply within 24 hours of the user's message.
- Answers come only from the knowledge base. If nothing relevant is found, the bot says a team member will follow up.
- Message deduplication is in-memory. Use Redis or a database for production.

## Possible next steps

- Conversation memory for multi-turn chats
- Admin page to upload and manage KB files
- Human handoff when confidence is low
- Analytics on common questions

## Author

Harsh Nanglia - [GitHub](https://github.com/nangliaharsh)
