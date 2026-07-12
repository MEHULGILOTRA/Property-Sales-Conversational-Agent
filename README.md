# Property Sales Conversational Agent

[![CI](https://github.com/MEHULGILOTRA/Property-Sales-Conversational-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/MEHULGILOTRA/Property-Sales-Conversational-Agent/actions/workflows/ci.yml)

A LangGraph-powered real-estate sales assistant. It understands budgets, cities, BHK and
feature preferences in natural language, searches a property database, shortlists the best
matches with an LLM, and walks the user through booking a site visit — capturing their
email and creating a lead along the way.

![Demo](docs/demo.gif)

**👉 [See it in action — full demo walkthrough](DEMO.md)**

## How it works

![Architecture](docs/architecture.svg)

```
greet (entry)
  └─ router ──► ask_budget ────────────────────────────► END
             ──► not_relevant ───────────────────────────► END
             ──► project_qa (LLM answers from shortlist) ► END
             ──► extract_budget ─► sql_search ─► select_top ─► summarize ─► present ─► END
             ──► book_project (choose project(s) → capture email → create lead + bookings) ─► END
             ──► cancel_booking (lookup by email → cancel by name) ─► END
```

**Booking flow — how memory carries a multi-turn booking:**

![Booking flow](docs/booking-flow.svg)

**Data model:**

![Data model](docs/data-model.svg)

- **Memory**: each `conversation_id` maps to a LangGraph checkpointer thread, so budget,
  city, shortlist and booking progress persist across turns.
- **LLM**: local [Ollama](https://ollama.com) by default; any OpenAI-compatible hosted
  endpoint via env vars. If the LLM is unreachable, deterministic fallbacks keep the
  conversation working.
- **Storage**: SQLite via async SQLAlchemy (`app/db/property_sales.db` ships pre-seeded
  for the demo).

## Quick start

```bash
git clone https://github.com/MEHULGILOTRA/Property-Sales-Conversational-Agent.git
cd Property-Sales-Conversational-Agent
python -m venv venv
# Windows: venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional — defaults work out of the box
```

**CLI chat:**

```bash
python main_cli.py
```

**Web UI + API server:**

```bash
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000/> for the built-in chat UI (no build step —
plain HTML/JS served by FastAPI).

```bash
# 1. Search
curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "message": "I want a 3 bhk in Dubai under 800000"}'

# 2. Book (same conversation_id — the agent remembers the shortlist)
curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "message": "Book Downtown Dubai Residences"}'

# 3. Provide email — lead + site-visit booking are created
curl -X POST http://127.0.0.1:8000/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "demo-1", "message": "buyer@example.com"}'
```

## Configuration

All settings are env vars (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` (local) or `openai` (any OpenAI-compatible endpoint) |
| `LLM_BASE_URL` | `http://localhost:11434` | LLM endpoint base URL |
| `LLM_MODEL` | `llama3.2` | Model name |
| `LLM_API_KEY` | — | Bearer token for hosted endpoints |
| `DATABASE_URL` | committed SQLite DB | Async SQLAlchemy URL |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | `20` / `60` | Per-IP rate limit on `/agents/chat` |

## Development

```bash
pip install -r requirements-dev.txt
ruff check .   # lint
pytest -q      # full suite — LLM is mocked, no Ollama needed
```

Re-seed the database from a CSV: `python -m app.db.seed path/to/data.csv`
(or set `SEED_CSV_PATH`).

## Deployment

A `render.yaml` blueprint is included for [Render](https://render.com) — point
`LLM_BASE_URL`/`LLM_API_KEY` at a hosted OpenAI-compatible provider and deploy.

## More

- [DEMO.md](DEMO.md) — full walkthrough with real transcripts
- [docs/technical-writeup.md](docs/technical-writeup.md) — how the conversation-memory
  bug was found and fixed
- [docs/architecture.svg](docs/architecture.svg) — architecture diagram
- [docs/booking-flow.svg](docs/booking-flow.svg) — booking sequence diagram
- [docs/data-model.svg](docs/data-model.svg) — database ERD

## License

[MIT](LICENSE)
