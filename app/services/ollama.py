import requests
import json

def local_llm_infer(prompt: str, model="llama3.2"):
    """
    Calls a local LLM endpoint for merging/refining itineraries.
    """
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        res.raise_for_status()
        data = res.json()
        return data.get("response", "").strip()
    except Exception as e:
        print(f"⚠️ LLM request failed: {e}")
        return "{}"

if __name__ == "__main__":
    prompt = "Hello agent"
    res = local_llm_infer(prompt)
    print(res)