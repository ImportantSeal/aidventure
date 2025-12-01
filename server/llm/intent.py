# server/llm/intent.py
import json
from typing import Dict, Any

from core.types import Intent
from core.state import ITEMS_DB
from llm.provider import get_provider
from llm.prompts import INTENT_SYSTEM, intent_user
from config import CFG

_ALLOWED_ACTIONS = {
    "LOOK", "MOVE", "TALK", "ATTACK", "USE_ITEM",
    "TAKE_ITEM", "DROP_ITEM", "GIVE_ITEM", "RUN", "WAIT",
    "BUY", "OTHER",
}

_ACTION_SYNONYMS = {
    "INSPECT": "LOOK",
    "SEARCH": "LOOK",
    "CHECK": "LOOK",
    "EXAMINE": "LOOK",
    "SPEAK": "TALK",
    "CHAT": "TALK",
    "CONVERSE": "TALK",
    "FLEE": "RUN",
    "ESCAPE": "RUN",
    "DEFEND": "OTHER",
    "BLOCK": "OTHER",
    "TRADE": "BUY",
}

def _normalize_intent_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}

    # action
    act_raw = str(raw.get("action") or "").upper()
    act = _ACTION_SYNONYMS.get(act_raw, act_raw)
    if act not in _ALLOWED_ACTIONS:
        act = "LOOK"

    # quantity
    q = raw.get("quantity", 1)
    try:
        q = int(q)
    except Exception:
        q = 1
    if q <= 0:
        q = 1

    def _opt_str(v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None

    target = _opt_str(raw.get("target"))
    item = _opt_str(raw.get("item"))
    direction = _opt_str(raw.get("direction"))
    free_text = _opt_str(raw.get("free_text"))

    # jos malli väittää että USE_ITEM mutta ei ole itemiä,
    # tulkitaan se yleiseksi toiminnaksi (OTHER) eikä inventory-itemin käytöksi
    if act == "USE_ITEM" and not item:
        act = "OTHER"

    return {
        "action": act,
        "quantity": q,
        "target": target,
        "item": item,
        "direction": direction,
        "free_text": free_text,
    }

def parse_intent(state, player_text: str) -> Intent:
    prov = get_provider(CFG.intent_provider)

    # erittäin tiivis state intent-mallille
    state_for_llm = {
        "location": state.get("world", {}).get("location"),
        "quest": state.get("quest"),
        "inventory_items": [it["name"] for it in state.get("inventory", [])],
        "items_db": list(ITEMS_DB.keys()),
    }

    user = intent_user(player_text, json.dumps(state_for_llm, ensure_ascii=False))
    raw = prov.chat_json(CFG.intent_model, INTENT_SYSTEM, user, temperature=0.1)
    data = _normalize_intent_dict(raw)
    return Intent.model_validate(data)
