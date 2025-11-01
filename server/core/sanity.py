from typing import Dict, Any, Tuple
from core.types import Intent

def _to_int(val, default: int = 1) -> int:
    try:
        v = int(val)
        return v
    except Exception:
        return default

def in_inventory(state: Dict[str, Any], name: str, qty: int = 1) -> bool:
    # coerce and clamp qty
    q = _to_int(qty, 1)
    if q < 1:
        q = 1
    # check if the player has at least qty of the item
    for it in state["inventory"]:
        if it["name"].lower() == name.lower() and it["count"] >= q:
            return True
    return False

def sanity_check(state: Dict[str, Any], intent: Intent) -> Tuple[bool, str]:
    # basic guards to prevent impossible or cheating actions
    p = state["player"]
    if p["hp"] <= 0:
        return False, "You are incapacitated and cannot act."

    action = (intent.action or "").upper()
    item = (intent.item or "").strip()
    raw_qty = intent.quantity
    qty = _to_int(raw_qty, 1)

    if action == "USE_ITEM":
        if not item:
            return False, "You must specify an item to use."
        if not in_inventory(state, item, qty):
            return False, f"You don't have {item}."

    if action in ("TAKE_ITEM", "DROP_ITEM", "GIVE_ITEM"):
        if _to_int(raw_qty, 0) <= 0:
            return False, "Invalid quantity."

    # allow buy; the shop logic does the actual checks
    return True, ""
