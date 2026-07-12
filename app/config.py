from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database — override with an env var for tests/deploys, defaults to the committed SQLite DB
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'app', 'db', 'property_sales.db')}",
)

# LLM provider — "ollama" (default, local) or "openai" (any OpenAI-compatible hosted endpoint)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

# Rate limiting for /agents/chat
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
