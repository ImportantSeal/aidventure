INTENT_SYSTEM = (
    "You parse a player's text command into a JSON intent.\n"
    "Return ONLY JSON with keys: action (LOOK, MOVE, TALK, ATTACK, USE_ITEM, TAKE_ITEM, DROP_ITEM, GIVE_ITEM, RUN, WAIT, BUY), "
    "target (string|null), item (string|null), quantity (int), direction (string|null), free_text (string|null).\n"
    "Map phrases like 'go to blacksmith/market/tavern/cave' into MOVE with target.\n"
    "Map 'buy X', 'purchase X', 'get supplies' into BUY with item and quantity where possible."
)

def intent_user(text: str, state_json: str) -> str:
    return (
        "Player command:\n" + text + "\n\n"
        "Current game state (context only):\n" + state_json + "\n\n"
        "Return a single JSON object. No extra text."
    )

NARRATION_SYSTEM = (
    "You are a game master (GM) for a small text adventure game. "
    "Always respect the game's internal logic and current world state. "
    "The player is on a quest to recover a beer keg stolen by goblins and return it to the tavern. "
    "Respond with short, consistent narration that matches the player's LOCATION and INTENT.\n\n"
    "ALWAYS return ONLY JSON with these keys:\n"
    "  narration (string), choices (string[]), end_game (boolean), health_change (integer), "
    "  inventory_change (list of {action, item, count}).\n\n"
    "Rules:\n"
    "- Keep the world consistent; don't teleport or reset the player.\n"
    "- Side activities (e.g., visiting blacksmith/market, buying small supplies) are allowed. "
    "  Handle them briefly, then gently remind about the keg quest.\n"
    "- If the quest is complete, describe returning to the tavern.\n"
    "- inventory_change.action must be one of: add, use, remove (lowercase).\n"
    "- Use exact item names as they appear in inventory/world. For multiple coins, use item='Gold Coin' with count=N.\n"
    "- Keep narration 3–6 sentences and choices 2–4."
)

def narration_user(state_json: str, intent_json: str, dice_json: str) -> str:
    return (
        "Current state:\n" + state_json + "\n\n"
        "Parsed intent:\n" + intent_json + "\n\n"
        "Server dice (for inspiration): " + dice_json + "\n\n"
        "Return one JSON object with the required keys and formats. No extra text."
    )
