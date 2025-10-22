import os, json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from config import CFG

class LLMProvider(ABC):
    @abstractmethod
    def chat_json(self, model: str, system: str, user: str, temperature: float = 0.3) -> Dict[str, Any]:
        ...

# --- groq (llama) ---
class GroqProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        # use groq api client; read key from config by default
        from groq import Groq
        self.client = Groq(api_key=api_key or CFG.groq_api_key)

    def chat_json(self, model: str, system: str, user: str, temperature: float = 0.3) -> Dict[str, Any]:
        # request json-only output from the model
        resp = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(resp.choices[0].message.content)

# --- gemini (optional) ---
class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        # lazy import and key check; fail clearly if not available
        try:
            import google.generativeai as genai
        except Exception as e:
            raise ImportError("google-generativeai not installed") from e

        key = api_key or CFG.gemini_api_key
        if not key:
            raise RuntimeError("GEMINI_API_KEY missing")
        genai.configure(api_key=key)
        self.genai = genai

    def chat_json(self, model: str, system: str, user: str, temperature: float = 0.3) -> Dict[str, Any]:
        # build a single prompt and ask for minified json only
        prompt = f"{system}\n\nUSER:\n{user}\n\nReturn ONLY valid minified JSON."
        m = self.genai.GenerativeModel(model)
        resp = m.generate_content(prompt, generation_config={"temperature": temperature})
        text = resp.text.strip()
        # strip code fences if present
        if text.startswith("```"):
            text = text.strip("`")
            text = text.split("\n", 1)[-1]
        return json.loads(text)

def get_provider(kind: str) -> LLMProvider:
    # choose provider; fallback to groq if gemini is not available
    k = (kind or "groq").lower()
    if k == "gemini":
        try:
            return GeminiProvider()
        except Exception:
            return GroqProvider()
    return GroqProvider()
