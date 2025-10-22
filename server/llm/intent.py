import json
from core.types import Intent
from llm.provider import get_provider
from llm.prompts import INTENT_SYSTEM, intent_user
from config import CFG

def parse_intent(state, player_text: str) -> Intent:
    # call the selected provider/model to parse a structured intent
    prov = get_provider(CFG.intent_provider)
    user = intent_user(player_text, json.dumps(state, ensure_ascii=False))
    data = prov.chat_json(CFG.intent_model, INTENT_SYSTEM, user, temperature=0.1)
    return Intent.model_validate(data)
