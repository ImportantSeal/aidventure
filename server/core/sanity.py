from typing import Dict, Any
from core.types import Intent

def in_inventory(state: Dict[str, Any], name: str, qty: int = 1) -> bool:
    # check if the player has at least qty of the item
    for it in state["inventory"]:
        if it["name"].lower() == name.lower() and it["count"] >= qty:
            return True
    return False

def sanity_check(state: Dict[str, Any], intent: Intent):
    # basic guards to prevent impossible or cheating actions
    p = state["player"]
    if p["hp"] <= 0:
        return False, "You are incapacitated and cannot act."

    if intent.action == "USE_ITEM":
        if not intent.item:
            return False, "You must specify an item to use."
        if not in_inventory(state, intent.item, intent.quantity):
            return False, f"You don't have {intent.item}."

    if intent.action in ("TAKE_ITEM", "DROP_ITEM", "GIVE_ITEM") and intent.quantity <= 0:
        return False, "Invalid quantity."

    # allow buy; the shop logic does the actual checks
    return True, ""
