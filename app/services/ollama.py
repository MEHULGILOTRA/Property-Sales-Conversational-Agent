import requests

from app.config import LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY, LLM_TIMEOUT
from app.core.logger import setup_logger

logger = setup_logger(__name__)


def local_llm_infer(prompt: str, model: str = None) -> str:
    """
    Calls the configured LLM endpoint. Supports a local Ollama server
    (LLM_PROVIDER=ollama) or any OpenAI-compatible hosted endpoint
    (LLM_PROVIDER=openai, e.g. Groq/Together/OpenRouter) via env vars.

    Returns "" on any failure so callers can fall back to deterministic replies.
    """
    model = model or LLM_MODEL
    try:
        if LLM_PROVIDER == "openai":
            headers = {"Content-Type": "application/json"}
            if LLM_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_API_KEY}"
            res = requests.post(
                f"{LLM_BASE_URL.rstrip('/')}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                headers=headers,
                timeout=LLM_TIMEOUT,
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"].strip()

        res = requests.post(
            f"{LLM_BASE_URL.rstrip('/')}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=LLM_TIMEOUT,
        )
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"LLM request failed: {e}")
        return ""


if __name__ == "__main__":
    print(local_llm_infer("Hello agent"))
