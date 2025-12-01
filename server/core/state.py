import json, os
from typing import Dict, Any, Tuple
from core.memory import get_memory_manager
# HUOM: poistin tästä rivin:
# from llm.narration import update_memory_summary

# load items database once
ITEMS_PATH = os.path.join(os.path.dirname(__file__), "..", "items.json")
with open(ITEMS_PATH, "r", encoding="utf-8") as f:
    ITEMS_DB = json.load(f)


def new_state() -> Dict[str, Any]:
    # create a fresh game state for a new session
    return {
        "turn": 0,
        "player": {"name": "Hero", "hp": 10, "max_hp": 10, "lvl": 1, "xp": 0},
        "world": {"location": "Village", "time_of_day": "morning"},
        "quest": {
            "id": "beer_keg",
            "title": "Recover the goblins' stolen beer keg and return it to the tavern",
            "status": "in_progress",
        },
        "inventory": [
            {"name": "Gold Coin", "count": 5},
            {"name": "Wooden Sword", "count": 1},
        ],
        "log": [],          # <-- TÄMÄ
        "game_over": False, # (valinnainen, mutta järkevä)
    }




def get_item(name: str) -> Tuple[str, Any]:
    # case-insensitive item lookup; returns (canonical_name, item_def) or (None, None)
    for key in ITEMS_DB:
        if key.lower() == name.lower():
            return key, ITEMS_DB[key]
    return None, None


def apply_health_change(state: Dict[str, Any], amount: int) -> int:
    # clamp hp between 0 and max_hp and return new hp
    p = state["player"]
    new_hp = max(0, min(p["max_hp"], p["hp"] + int(amount)))
    p["hp"] = new_hp
    return new_hp


def apply_item_effect(state: Dict[str, Any], item_name: str) -> str:
    # apply a consumable's effect and return a short narration string
    key, item = get_item(item_name)
    if not item or item.get("type") != "consumable":
        return ""
    effect = item.get("effect", {})
    if "hp" in effect:
        before = state["player"]["hp"]
        apply_health_change(state, effect["hp"])
        gained = state["player"]["hp"] - before
        return (
            f"You use the {key} and recover {gained} HP."
            if gained != 0
            else f"You use the {key}, but it has no effect."
        )
    return ""


# MEMORY HELPER FUNCTIONS


def add_game_turn(turn_text: str, session_id: str):
    mm = get_memory_manager(session_id)
    mm.add_turn_text(turn_text)


def update_long_summary(session_id: str):
    # Tuodaan tämä vasta kun funktio kutsutaan, ei moduulin latausvaiheessa.
    from llm.narration import update_memory_summary

    mm = get_memory_manager(session_id)
    mm.update_long_summary(update_memory_summary)


def get_memory_context(session_id: str):
    mm = get_memory_manager(session_id)
    return {
        "short_term": mm.get_short_texts(),
        "long_term": mm.get_long_summary(),
    }


def build_llm_state(state: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    s = dict(state)
    mm = get_memory_manager(session_id)
    s["memory_long_summary"] = mm.get_long_summary()
    s["memory_short_turns"] = mm.get_short_texts()
    return s
