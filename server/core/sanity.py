# server/core/sanity.py
from typing import Dict, Any
from core.types import Intent
from core.state import get_item

def in_inventory(state: Dict[str, Any], name: str, qty: int = 1) -> bool:
    for it in state["inventory"]:
        if it["name"].lower() == name.lower() and it["count"] >= qty:
            return True
    return False

def sanity_check(state: Dict[str, Any], intent: Intent):
    p = state["player"]

    if state.get("game_over"):
        return False, "The adventure has already ended."

    if p["hp"] <= 0:
        return False, "You are incapacitated and cannot act."

    if intent.action in ("TAKE_ITEM", "DROP_ITEM", "GIVE_ITEM") and intent.quantity <= 0:
        return False, "Invalid quantity."

    if intent.action == "USE_ITEM":
        if not intent.item:
            return False, "You must specify an item to use."
        if not in_inventory(state, intent.item, intent.quantity):
            return False, f"You don't have {intent.item}."
        canon, item_def = get_item(intent.item)
        if not item_def:
            return False, f"You can't use '{intent.item}' right now."
        if item_def.get("type") not in ("consumable", "utility"):
            return False, f"You can't really 'use' the {canon} directly."

    if intent.action in ("DROP_ITEM", "GIVE_ITEM") and intent.item:
        if not in_inventory(state, intent.item, intent.quantity):
            return False, f"You don't have enough {intent.item}."

    # BUY ei tee kovaa validointia täällä; shop / GM hoitaa.
    return True, ""
