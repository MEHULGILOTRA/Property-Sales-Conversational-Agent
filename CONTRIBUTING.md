# Contributing

Thanks for your interest in improving the Property Sales Conversational Agent!

## Setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements-dev.txt
```

## Before opening a PR

1. Run the linter: `ruff check .`
2. Run the tests: `pytest -q` (no Ollama needed — LLM calls are mocked)
3. Add tests for any new conversation flow or tool behavior.

## Guidelines

- Keep nodes small and single-purpose; conversation routing lives in `app/agent/router.py`.
- Anything that hits the DB goes through a tool (`app/tools/`) or service (`app/services/`).
- New config belongs in `app/config.py` + `.env.example`, not hardcoded values.
