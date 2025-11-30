import os
from dataclasses import dataclass

# Yritetään ladata .env jos se löytyy, mutta ei vaadita
try:
    from dotenv import load_dotenv  # pip install python-dotenv (vapaaehtoinen)
    load_dotenv()
except Exception:
    pass

@dataclass(frozen=True)
class LLMConfig:
    # Intent (parser)
    intent_provider: str = os.environ.get("INTENT_PROVIDER", "groq")      # groq | gemini
    intent_model: str    = os.environ.get("INTENT_MODEL", "llama-3.1-8b-instant")

    # Narration (tarina)
    narration_provider: str = os.environ.get("NARRATION_PROVIDER", "groq") # groq | gemini
    narration_model: str    = os.environ.get(
        "NARRATION_MODEL",
        "llama-3.3-70b-versatile" if os.environ.get("NARRATION_PROVIDER","groq").lower()=="groq" else "gemini-1.5-flash"
    )

    # API-keyt (vain jos käytössä)
    groq_api_key: str   = os.environ.get("GROQ_API_KEY", "")
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")

CFG = LLMConfig()
q