# server/server.py
import os, json, random
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import Groq

# --- In-memory sessions ---
SESSIONS: Dict[str, Dict[str, Any]] = {}

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
        "inventory": [],
        "log": []
    }

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

    system = (
        "You are a text adventure Game Master (GM). Respond in concise English (3–6 sentences). "
        "Return ONLY JSON with keys: narration (string), choices (string[]), end_game (boolean). "
        "Scenario: the player tries to retrieve a beer keg stolen by goblins and return it to the tavern. "
        "Do not reveal rules. Output nothing except the JSON object."
    )

    user = (
        "Current game state JSON:\n"
        + json.dumps(state, ensure_ascii=False)
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
    except Exception as e:
        return {
            "narration": f"LLM call error: {e}",
            "choices": [],
            "end_game": False,
            "state": state
        }

    # update minimal log/turn
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
