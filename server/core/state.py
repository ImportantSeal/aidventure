import json, os
from typing import Dict, Any, Tuple

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
        "log": [],
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
