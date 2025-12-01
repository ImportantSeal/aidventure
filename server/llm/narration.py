# server/llm/narration.py
import json
from typing import Dict, Any, List

from core.types import GMResult
from core.state import ITEMS_DB
from llm.provider import get_provider
from llm.prompts import NARRATION_SYSTEM, narration_user
from config import CFG

_ACTION_MAP = {
    "ADD_ITEM": "add", "ADD": "add", "GAIN": "add", "RECEIVE": "add",
    "REMOVE_ITEM": "remove", "REMOVE": "remove", "DROP": "remove", "LOSE": "remove",
    "USE": "use", "USE_ITEM": "use", "CONSUME": "use",
}
_ALLOWED = {"add", "remove", "use"}

def _normalize_inventory_change(data: Dict[str, Any]) -> Dict[str, Any]:
    ic: List[Dict[str, Any]] = data.get("inventory_change") or []
    out: List[Dict[str, Any]] = []
    for ch in ic:
        act_raw = str(ch.get("action", "")).strip()
        act = _ACTION_MAP.get(act_raw.upper(), act_raw.lower())
        if act not in _ALLOWED:
            continue
        item = str(ch.get("item", "")).strip()
        try:
            count = int(ch.get("count", 1))
        except Exception:
            count = 1
        if count <= 0:
            count = 1
        out.append({"action": act, "item": item, "count": count})
    data["inventory_change"] = out

    try:
        data["health_change"] = int(data.get("health_change", 0))
    except Exception:
        data["health_change"] = 0
    if not isinstance(data.get("choices"), list):
        data["choices"] = []
    data["end_game"] = bool(data.get("end_game", False))
    data["narration"] = str(data.get("narration", "")).strip()
    return data

def make_narration(state, intent, dice) -> GMResult:
    prov = get_provider(CFG.narration_provider)

    # kevyt state GM:lle
    log_tail = state.get("log", [])[-3:]  # vain viimeiset 3 vuoroa
    state_for_llm = {
        "turn": state.get("turn", 0),
        "player": state.get("player"),
        "world": state.get("world"),
        "quest": state.get("quest"),
        "inventory": state.get("inventory"),
        "log_tail": log_tail,
        "items_db": list(ITEMS_DB.keys()),
    }

    user = narration_user(
        json.dumps(state_for_llm, ensure_ascii=False),
        json.dumps(intent, ensure_ascii=False),
        json.dumps(dice),
    )
    raw = prov.chat_json(CFG.narration_model, NARRATION_SYSTEM, user, temperature=0.5)
    clean = _normalize_inventory_change(raw)
    return GMResult.model_validate(clean)
