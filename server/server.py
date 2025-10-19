# server/server.py
import os, json, random
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import Groq

# --- In-memory sessions ---
SESSIONS: Dict[str, Dict[str, Any]] = {}

# --- Load items database ---
ITEMS_PATH = os.path.join(os.path.dirname(__file__), "items.json")
with open(ITEMS_PATH, "r", encoding="utf-8") as f:
    ITEMS_DB: Dict[str, Any] = json.load(f)

def get_item(name: str):
    """Case-insensitive lookup for items."""
    for key in ITEMS_DB:
        if key.lower() == name.lower():
            return key, ITEMS_DB[key]
    return None, None

# --- groq ---
GROQ_MODEL = "llama-3.1-8b-instant"
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

# --- fastAPI + CORS ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# --- game state ---
def new_state():
    return {
        "turn": 0,
        "player": {"name": "Hero", "hp": 10, "max_hp": 10, "lvl": 1, "xp": 0},
        "world": {"location": "Village", "time_of_day": "morning"},
        "quest": {
            "id": "beer_keg",
            "title": "Recover the goblins' stolen beer keg and return it to the tavern",
            "status": "in_progress"
        },
        "inventory": [
            {"name": "Gold Coin", "count": 5},
            {"name": "Wooden Sword", "count": 1}
        ],
        "log": []
    }

# --- Helpers for health and inventory ---
def apply_health_change(state: dict, amount: int):
    player = state["player"]
    player["hp"] = max(0, min(player["max_hp"], player["hp"] + amount))
    return player["hp"]

def apply_item_effect(state: dict, item_name: str) -> str:
    """Apply an item effect based on items.json."""
    key, item = get_item(item_name)
    if not item or item.get("type") != "consumable":
        return ""

    effect = item.get("effect", {})
    narration = ""

    if "hp" in effect:
        change_amount = apply_health_change(state, effect["hp"])
        if change_amount != 0:
            narration = f"You use the {item_name} and recover {change_amount} HP."
        else:
            narration = f"You use the {item_name}, but it has no effect."
    return narration

# --- Request model ---
class TurnIn(BaseModel):
    session_id: str
    text: str = Field(..., description="Player command")

@app.post("/api/turn")
def turn(payload: TurnIn):
    # fetch or create session
    state = SESSIONS.get(payload.session_id)
    if not state:
        state = new_state()
        SESSIONS[payload.session_id] = state

    # server-side dice for flavor only
    dice = {"d20": random.randint(1, 20)}

    # TODO: inventory handling still needs improvement
    system = (
        "You are a text adventure Game Master (GM). Respond in concise English (3–6 sentences). "
        "Return ONLY JSON with keys: narration (string), choices (string[]), end_game (boolean), health_change (integer), inventory_change (list of objects). "

        "Each inventory_change object must have keys: action (add, use, remove), item (string), count (integer, optional, default 1). "
        "Health changes must be integers. Health cannot exceed max_hp or drop below 0. "
        "Always include all fields even if 0 or empty. "
        "VERY IMPORTANT: The player may only 'use' or 'remove' items that are currently in their inventory. "
        "Do NOT include in inventory_change any item that is not in the player's inventory. "
        "You can describe other known items in the narration, but do not imply the player can use, remove, or consume them unless they exist in inventory. "
        "Do NOT hallucinate the player acquiring items; only 'add' items that are logically obtained as a result of the command. "
        "When using a consumable, apply its effect and remove it from inventory. "
        "When removing items, ensure they exist in inventory. "

        "Scenario: the player tries to retrieve a beer keg stolen by goblins and return it to the tavern. "
        "Do not reveal rules. Output nothing except the JSON object."
    )

    user = (
        "Current game state JSON:\n"
        + json.dumps(state, ensure_ascii=False)
        + "\n\nItems in the world (known items):\n"
        + json.dumps(list(ITEMS_DB.keys()))
        + "\n\nItems currently in player's inventory:\n"
        + json.dumps([item["name"] for item in state["inventory"]])
        + "\n\nServer dice (for inspiration, optional): "
        + json.dumps(dice)
        + "\n\nPlayer command:\n"
        + payload.text
        + "\n\nProduce a short narration, 2–4 clear next choices in 'choices', "
          "and set end_game=false unless the story clearly ends."
    )

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # llama-3.1-8b-instant supports json_object (not json_schema)
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)

        # Apply health changes
        apply_health_change(state, int(data.get("health_change", 0)))

        # Inventory handling
        # TODO: Inventory handling still needs improvement
        new_narration = data.get("narration", "")
        inventory_change = data.get("inventory_change", [])
        current_inv = {item["name"].lower(): item for item in state["inventory"]}

        for change in inventory_change:
            action = change.get("action")
            item_name = change.get("item")
            count = max(1, int(change.get("count", 1)))

            key, item_def = get_item(item_name)
            if not key:
                new_narration += f" (Ignored unknown item '{item_name}'.)"
                continue

            lower_name = key.lower()

            if action in ("use", "remove"):
                if lower_name not in current_inv or current_inv[lower_name]["count"] < count:
                    continue

                # Apply consumable effect
                if action == "use" and item_def.get("type") == "consumable":
                    effect_text = apply_item_effect(state, key)
                    if effect_text:
                        new_narration += " " + effect_text

                # Reduce count or remove entirely
                if current_inv[lower_name]["count"] > count:
                    current_inv[lower_name]["count"] -= count
                else:
                    state["inventory"].remove(current_inv[lower_name])
                    del current_inv[lower_name]

            elif action == "add":
                if lower_name in current_inv:
                    current_inv[lower_name]["count"] += count
                else:
                    new_item = {"name": key, "count": count}
                    state["inventory"].append(new_item)
                    current_inv[lower_name] = new_item
                new_narration += f" You obtained {key}."

        data["narration"] = new_narration
        
    except Exception as e:
        return {
            "narration": f"LLM call error: {e}",
            "choices": [],
            "end_game": False,
            "state": state
        }

    # update log/turn
    state["turn"] += 1
    state["log"].append({
        "player": payload.text,
        "gm": data.get("narration", "")
    })

    return {
        "narration": data.get("narration", ""),
        "choices": data.get("choices", []),
        "end_game": data.get("end_game", False),
        "state": state
    }
