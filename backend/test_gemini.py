"""
test_gemini.py
Live smoke-test for the primary LLM connection.

Skips automatically when:
  - GEMINI_API_KEY is not set, or
  - The API returns a 429 rate-limit / quota error.

Run manually:
    pytest test_gemini.py -v -s
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv(".env")


# Skip the whole module if no key is configured
if not os.getenv("GEMINI_API_KEY"):
    pytest.skip("GEMINI_API_KEY not set — skipping live LLM test", allow_module_level=True)


def test_gemini_basic_response():
    """Sends a simple prompt to the primary LLM and checks for a non-empty reply."""
    try:
        from app.core.llm import primary_llm
        response = primary_llm.invoke("Hello, who are you?")
        assert response and response.content, "LLM returned an empty response"
        print(f"\nLLM reply: {response.content[:200]}")
    except Exception as exc:
        err = str(exc)
        if "429" in err or "ResourceExhausted" in err or "quota" in err.lower():
            pytest.skip(f"Gemini API rate-limit / quota exceeded — skipping: {err[:120]}")
        raise
