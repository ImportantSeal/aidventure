# server/llm/provider.py
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from config import CFG


class LLMProvider(ABC):
    @abstractmethod
    def chat_json(
        self,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Return a Python dict parsed from the model's JSON response.
        """
        ...


# --- Groq (llama) provider -------------------------------------------------


class GroqProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        from groq import Groq  # asennettu pipillä: pip install groq
        self.client = Groq(api_key=api_key or CFG.groq_api_key)

    def chat_json(
        self,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Kutsuu Groq-chat API:a ja pyytää JSON-only vastauksen.
        max_tokens rajaa vastauksen pituutta -> nopeampi ja vähemmän tokeneita.
        """
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=256,  # riittää hyvin intentille ja GM-jsonille
        )
        return json.loads(resp.choices[0].message.content)


# --- Gemini (valinnainen, fallbackaa Groq:iin jos ei toimi) -----------------


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        try:
            import google.generativeai as genai
        except Exception as e:
            raise ImportError("google-generativeai not installed") from e

        key = api_key or CFG.gemini_api_key
        if not key:
            raise RuntimeError("GEMINI_API_KEY missing")
        genai.configure(api_key=key)
        self.genai = genai

    def chat_json(
        self,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Rakentaa yhden promptin ja pyytää minified JSONin.
        """
        prompt = f"{system}\n\nUSER:\n{user}\n\nReturn ONLY valid minified JSON."
        m = self.genai.GenerativeModel(model)
        resp = m.generate_content(
            prompt,
            generation_config={"temperature": temperature},
        )
        text = resp.text.strip()
        # stripataan mahdolliset ```json -aidat
        if text.startswith("```"):
            text = text.strip("`")
            text = text.split("\n", 1)[-1]
        return json.loads(text)


# --- providerin valinta -----------------------------------------------------


def get_provider(kind: Optional[str]) -> LLMProvider:
    """
    Valitsee providerin CFG:n (tai annetun stringin) perusteella.

    kind: "groq" | "gemini" | None
    """
    k = (kind or "groq").lower()
    if k == "gemini":
        try:
            return GeminiProvider()
        except Exception:
            # jos gemini ei ole saatavilla, fallback Groqiin
            return GroqProvider()
    # default: groq
    return GroqProvider()
