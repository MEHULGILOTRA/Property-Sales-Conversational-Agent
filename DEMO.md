# 🏠 Live Demo — Property Sales Conversational Agent

Everything below is a **real transcript** captured from the running application
(FastAPI + LangGraph + SQLite). The LLM was offline during capture, so these replies
come from the agent's deterministic fallbacks — with Ollama or a hosted LLM connected,
the summaries become richer, but every flow works either way.

---

## 1. Start the app

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/** — the built-in chat UI loads, checks `/health`, and
shows LLM connectivity in the header.

---

## 2. Property search (natural language → SQL)

> **You:** I want a 3 bhk in Dubai under 800000

> **Agent:**
> Here are the top matches for your search:
> - Downtown Dubai Residences (Dubai) — $320,458, 3 BHK
> - Business Bay (Dubai) — $327,002, 3 BHK
> - Burj Binghatti Jacob & Co Residences (Dubai) — $385,621, 3 BHK
>
> Would you like to book a site visit for any of these?

One message carried three constraints — **BHK count**, **city**, and **budget** — and
all three were extracted and applied as SQL filters. Budgets also work as shorthand
(`600k`, `1.2 million`), and saying *"actually my budget is 600k"* later re-runs the
search with the corrected value.

## 3. Booking two projects in one message

> **You:** Book Downtown Dubai Residences and Business Bay

> **Agent:** Great choice — **Downtown Dubai Residences, Business Bay**! Please share
> your email address so I can register your site visit.

The agent never books without contact details. Reply with just an email:

> **You:** demo.buyer@example.com

> **Agent:**
> ✅ Booking Request Received for:
> - **Downtown Dubai Residences** (Confirmation ID: 5)
> - **Business Bay** (Confirmation ID: 6)
>
> 👤 **Your Broker:** Mehul Gilotra
> 📞 **Contact:** +11-111-1111
> Site visit scheduled.

Behind the scenes this created **one lead** (keyed by email, deduplicated on repeat
bookings) and **two visit-booking rows** in SQLite.

## 4. Cancelling by name

> **You:** Cancel my visit to Business Bay

> **Agent:** 🗑️ Your site visit for **Business Bay** has been cancelled. If you'd like
> to reschedule, just ask me to book a new visit.

The agent matched the project among *your* bookings (looked up by email), deleted the
right row, and kept the Downtown Dubai Residences booking intact. With several bookings
and no name given, it lists them and asks which one; with no email on file, it asks for
the email first.

## 5. The same conversation over the raw API

The UI is just a client — everything works with three curls sharing a `conversation_id`
(this is what proves cross-request memory):

```bash
curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "message": "I want a 3 bhk in Dubai under 800000"}'
# → {"reply": "Here are the top matches for your search:\n- Downtown Dubai Residences ...", ...}

curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "message": "book Downtown Dubai Residences"}'
# → {"reply": "Great choice — **Downtown Dubai Residences**! Please share your email address ..."}

curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "message": "buyer@example.com"}'
# → {"reply": "✅ Booking Request Received for:\n- **Downtown Dubai Residences** (Confirmation ID: ...)"}
```

Turn 2 knows the shortlist from turn 1 and turn 3 completes the booking — the
`conversation_id` maps to a LangGraph checkpointer thread.

## 6. Observability

```bash
curl http://127.0.0.1:8000/health
# → {"status": "degraded", "db": "ok", "llm": "unreachable", "llm_provider": "ollama"}
```

Every response carries an `X-Request-ID` header, every log line carries that same ID,
and each graph node logs a `metric node=... duration_ms=...` line:

```
2026-07-12 17:21:02 | INFO | 385cf01357c2 | app.main | main.py:27 | GET / took 132ms
2026-07-12 16:49:44 | INFO | - | app.agent.graph | metric node=sql_search duration_ms=23
```

## 7. Prove it yourself

```bash
pip install -r requirements-dev.txt
pytest -q          # 43 tests — routing, search filters, booking, cancellation, rate limiting
```

The whole suite runs with the LLM mocked, so it needs nothing but Python.

---

*More detail: [architecture diagram](docs/architecture.svg) ·
[how the conversation-memory bug was found and fixed](docs/technical-writeup.md)*
