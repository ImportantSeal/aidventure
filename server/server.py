# server/server.py

import os
import json, random, re
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.types import TurnIn, TurnOut, Intent
from core.state import new_state, apply_health_change, apply_item_effect, get_item
from core.sanity import sanity_check
from llm.intent import parse_intent
from llm.narration import make_narration

SESSIONS: Dict[str, Dict[str, Any]] = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ---- Health check (näytä aktiiviset mallit/providereit) ----
@app.get("/health")
def health_check():
    return {
        "intent_provider": os.getenv("INTENT_PROVIDER", "unknown"),
        "intent_model": os.getenv("INTENT_MODEL", "unknown"),
        "narration_provider": os.getenv("NARRATION_PROVIDER", "unknown"),
        "narration_model": os.getenv("NARRATION_MODEL", "unknown"),
    }

def ensure_session(session_id: str):
    if session_id not in SESSIONS:
        SESSIONS[session_id] = new_state()
    return SESSIONS[session_id]

# --------- NIMIEN NORMALISOINTI / ALIAKSET ----------

ALIASES = {
    "gold coins": "Gold Coin",
    "gold coin": "Gold Coin",
    "coins": "Gold Coin",
    "coin": "Gold Coin",

    "supplies": "supplies",   # käsitellään erikseen
    "blacksmith": "blacksmith",
    "black smith": "blacksmith",

    "bread": "Loaf of Bread",
    "loaf": "Loaf of Bread",

    "better sword": "Iron Sword",
    "sword": "Iron Sword"     # ostokontekstissa tulkitaan paremmaksi miekaksi
}
_WORD_S = re.compile(r"s$", re.IGNORECASE)

def normalize_item_name(name: str) -> str | None:
    if not name:
        return None
    raw = name.strip()
    alias = ALIASES.get(raw.lower())
    if alias and alias != "supplies":
        return alias
    key, _ = get_item(raw)
    if key:
        return key
    if _WORD_S.search(raw):
        singular = _WORD_S.sub("", raw)
        key2, _ = get_item(singular)
        if key2:
            return key2
    return None

# --------- SIJOITUS/KAUPPA – KEVYT PELILOGIIKKA ----------

def maybe_move(state: Dict[str, Any], intent: Intent) -> str:
    """Päivitä sijainti, jos intent pyytää selkeää siirtymää."""
    t = (intent.target or intent.direction or intent.free_text or "").lower()
    if intent.action == "MOVE":
        if "blacksmith" in t or "smith" in t:
            state["world"]["location"] = "Blacksmith"
            return "You head to the blacksmith's forge."
        if "market" in t:
            state["world"]["location"] = "Market"
            return "You head to the small village market."
        if "tavern" in t:
            state["world"]["location"] = "Tavern"
            return "You return to the tavern."
        if "cave" in t or "north" in t:
            state["world"]["location"] = "Cave"
            return "You make your way toward the goblin cave."
        if "village" in t:
            state["world"]["location"] = "Village"
            return "You are back in the village square."
    return ""

def count_coins(state: Dict[str, Any]) -> int:
    for it in state["inventory"]:
        if it["name"].lower() == "gold coin":
            return it["count"]
    return 0

def add_item(state: Dict[str, Any], name: str, qty: int) -> None:
    for it in state["inventory"]:
        if it["name"].lower() == name.lower():
            it["count"] += qty
            return
    state["inventory"].append({"name": name, "count": qty})

def remove_coins(state: Dict[str, Any], qty: int) -> bool:
    for it in state["inventory"]:
        if it["name"].lower() == "gold coin":
            if it["count"] >= qty:
                it["count"] -= qty
                if it["count"] == 0:
                    state["inventory"].remove(it)
                return True
            return False
    return False

def try_shop_purchase(state: Dict[str, Any], intent: Intent) -> str | None:
    """
    Kevyt, sääntöpohjainen kauppa:
      - Market/Village: Loaf of Bread (2c), Torch (1c), Rope (2c), Bandage (2c), Healing Herbs (3c) jos items.jsonissa on
      - Blacksmith: Iron Sword (10c), Shield (8c), Dagger (4c)
      - 'supplies': pikapakkaus (Market/Village: kaksi halvinta saatavilla)
    Lisäksi: jos intent EI ole BUY mutta teksti viittaa hintoihin/tarjontaan,
    palautetaan informatiivinen vastaus ilman maksua/inventaarion muutoksia.
    """
    loc = state["world"]["location"]
    text = (intent.free_text or "").lower()

    # väärä paikka → ei käsitellä kauppaa (LLM hoitaa muun narraation)
    if loc not in ("Blacksmith", "Market", "Village"):
        return None

    # --- pelkkä hintakysely / tarjonnan tiedustelu (ei ostoa) ---
    hint_words = ["price", "cost", "buy", "sell", "weapon", "sword", "axe", "shield", "dagger", "torch", "rope", "bread"]
    if intent.action != "BUY" and any(w in text for w in hint_words):
        if loc == "Blacksmith":
            # listaa vain mitä oikeasti on items.jsonissa
            offers = []
            for name, price in {"Iron Sword": 10, "Shield": 8, "Dagger": 4}.items():
                k, _ = get_item(name)
                if k:
                    offers.append(f"{name} for {price} coins")
            if offers:
                return "The blacksmith shows you his wares: " + ", ".join(offers) + "."
            return "The blacksmith shrugs; his racks are bare today."
        else:
            offers = []
            for name, price in {"Loaf of Bread": 2, "Torch": 1, "Rope": 2, "Bandage": 2, "Healing Herbs": 3}.items():
                k, _ = get_item(name)
                if k:
                    offers.append(f"{name} for {price} coins")
            if offers:
                return "Stalls around you offer " + ", ".join(offers) + "."
            return "The market is quiet and offers little right now."

    # --- varsinainen ostaminen ---
    if intent.action != "BUY":
        return None

    # valikoimat
    market_catalog = {"Loaf of Bread": 2, "Torch": 1, "Rope": 2, "Bandage": 2, "Healing Herbs": 3}
    blacksmith_catalog = {"Iron Sword": 10, "Shield": 8, "Dagger": 4}

    def filter_existing(catalog: Dict[str, int]) -> Dict[str, int]:
        out = {}
        for name, price in catalog.items():
            k, _ = get_item(name)
            if k:
                out[name] = price
        return out

    market_catalog = filter_existing(market_catalog)
    blacksmith_catalog = filter_existing(blacksmith_catalog)
    catalog = market_catalog if loc in ("Market", "Village") else blacksmith_catalog

    asked_raw = (intent.item or intent.free_text or "").strip()
    asked = asked_raw.lower()

    wanted: list[tuple[str, int]] = []
    if not asked or asked == "supplies":
        # kaksi halvinta saatavilla olevaa tuotetta
        if not catalog:
            return "There aren't any suitable supplies available to buy here."
        wanted = sorted(catalog.items(), key=lambda x: x[1])[:2]
    else:
        norm = normalize_item_name(asked_raw) or ALIASES.get(asked)
        if not norm:
            return "That item isn't available here."
        if norm not in catalog:
            return "That item isn't sold at this location."
        wanted = [(norm, catalog[norm])]

    total = sum(price for _, price in wanted)
    if count_coins(state) < total:
        # ystävällinen vastaus ilman “tönäisyä”
        items_list = ", ".join(name for name, _ in wanted)
        return f"You don't have enough coins to buy {items_list}. Total cost is {total}."

    if not remove_coins(state, total):
        return "Purchase failed: not enough Gold Coins."

    for name, _ in wanted:
        add_item(state, name, 1)

    items_list = ", ".join(name for name, _ in wanted)
    return f"You buy {items_list} for {total} Gold Coin(s)."

# ------------------------------------------------------

@app.post("/api/turn", response_model=TurnOut)
def turn(payload: TurnIn):
    state = ensure_session(payload.session_id)
    dice = {"d20": random.randint(1, 20)}

    # 1) Intent-parsi (LLM #1)
    intent = parse_intent(state, payload.text)

    # 2) Sanity-check ennen mitään (estetään huijaus/mahdottomat)
    ok, reason = sanity_check(state, intent)
    if not ok:
        narration = f"{reason} Try something else."
        choices = ["LOOK around", "Go to cave", "Check inventory"]
        state["turn"] += 1
        state["log"].append({"player": payload.text, "gm": narration})
        return TurnOut(narration=narration, choices=choices, end_game=False, state=state)

    # 3) Paikallinen logiikka: liikkuminen & kauppa ennen narraatiota
    move_text = maybe_move(state, intent)

    shop_text = try_shop_purchase(state, intent)
    if shop_text:
        # jos shop_text on pelkkä informatiivinen vastaus, anna muutama järkevä valinta
        narration = (move_text + " " if move_text else "") + shop_text
        state["turn"] += 1
        state["log"].append({"player": payload.text, "gm": narration})
        choices = ["Buy Dagger", "Buy Iron Sword", "Buy Shield"] if state["world"]["location"] == "Blacksmith" else ["Buy Torch", "Buy Rope", "Buy Loaf of Bread"]
        # suodata valinnat, jotka oikeasti ovat olemassa items.jsonissa
        def exists(name: str) -> bool:
            k, _ = get_item(name)
            return k is not None
        choices = [c for c in choices if exists(c.split("Buy ",1)[1])]
        if not choices:
            choices = ["LOOK around", "Go to cave", "Return to tavern"]
        return TurnOut(
            narration=narration.strip(),
            choices=choices,
            end_game=False,
            state=state
        )

    # 4) Narraatio (LLM #2)
    gm = make_narration(state, intent.model_dump(), dice)

    # 5) Sovelletaan muutokset turvallisesti
    apply_health_change(state, int(gm.health_change))
    narration = (move_text + " " if move_text else "") + gm.narration
    inventory_change = gm.inventory_change or []
    current_inv = {it["name"].lower(): it for it in state["inventory"]}

    for ch in inventory_change:
        action = ch.action                            # add | use | remove
        item_name = normalize_item_name(ch.item)
        count = max(1, int(ch.count))

        if not item_name:
            narration += f" (Ignored unknown item '{ch.item}'.)"
            continue

        key, item_def = get_item(item_name)
        if not key:
            narration += f" (Ignored unknown item '{ch.item}'.)"
            continue

        lname = key.lower()

        if action in ("use", "remove"):
            if lname not in current_inv or current_inv[lname]["count"] < count:
                continue
            if action == "use" and item_def.get("type") == "consumable":
                eff = apply_item_effect(state, key)
                if eff:
                    narration += " " + eff
            if current_inv[lname]["count"] > count:
                current_inv[lname]["count"] -= count
            else:
                state["inventory"].remove(current_inv[lname])
                del current_inv[lname]

        elif action == "add":
            if lname in current_inv:
                current_inv[lname]["count"] += count
            else:
                state["inventory"].append({"name": key, "count": count})
                current_inv[lname] = {"name": key, "count": count}
            narration += f" You obtained {key}."

    # 6) Päivitä loki & turn
    state["turn"] += 1
    state["log"].append({"player": payload.text, "gm": narration})

    return TurnOut(
        narration=narration.strip(),
        choices=gm.choices or ["LOOK around", "Go to cave", "Return to tavern"],
        end_game=gm.end_game,
        state=state,
    )
