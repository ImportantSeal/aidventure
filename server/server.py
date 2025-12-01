import os
import json
import random
import re
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.types import TurnIn, TurnOut, Intent
from core.state import (
    new_state,
    apply_health_change,
    apply_item_effect,
    get_item,
    ITEMS_DB,
)
from core.sanity import sanity_check
from llm.intent import parse_intent
from llm.narration import make_narration

# ----------------- FastAPI & session management -----------------

SESSIONS: Dict[str, Dict[str, Any]] = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health endpoint – näyttää käytössä olevat providerit ja mallit."""
    return {
        "intent_provider": os.getenv("INTENT_PROVIDER", "unknown"),
        "intent_model": os.getenv("INTENT_MODEL", "unknown"),
        "narration_provider": os.getenv("NARRATION_PROVIDER", "unknown"),
        "narration_model": os.getenv("NARRATION_MODEL", "unknown"),
    }


def ensure_session(session_id: str) -> Dict[str, Any]:
    """Luo uuden pelitilan jos sessiota ei ole, muuten palauttaa olemassa olevan."""
    if session_id not in SESSIONS:
        SESSIONS[session_id] = new_state()
    return SESSIONS[session_id]


# ----------------- Item-nimien normalisointi -----------------

ALIASES = {
    # raha
    "gold coins": "Gold Coin",
    "gold coin": "Gold Coin",
    "coins": "Gold Coin",
    "coin": "Gold Coin",

    # kirjoitusvirheitä / paikkoja
    "supplies": "supplies",
    "blacsmith": "blacksmith",
    "black smith": "blacksmith",

    # ruoka
    "bread": "Loaf of Bread",
    "loaf": "Loaf of Bread",

    # aseiden yleisnimityksiä
    "better sword": "Iron Sword",
    "sword": "Iron Sword",
}

_WORD_S = re.compile(r"s$", re.IGNORECASE)


def normalize_item_name(name: str) -> str | None:
    """
    Yrittää löytää items.json:sta järkevän item-nimen.

    - käyttää alias-sanoja (coin/sword/bread)
    - tarkistaa suorat osumat ja yksikkö/monikko
    - kevyt fuzzy-match (alku, sisältää, tms.)
    """
    if not name:
        return None
    raw = name.strip()
    raw_lower = raw.lower()

    # aliasit ensin (paitsi supplies, jota shop-logiikka käsittelee erikseen)
    alias = ALIASES.get(raw_lower)
    if alias and alias != "supplies":
        return alias

    # suora osuma
    key, _ = get_item(raw)
    if key:
        return key

    # monikko → yksikkö
    if _WORD_S.search(raw):
        singular = _WORD_S.sub("", raw)
        key2, _ = get_item(singular)
        if key2:
            return key2

    # alkuosumalla yksi match
    starts = [k for k in ITEMS_DB.keys() if k.lower().startswith(raw_lower)]
    if len(starts) == 1:
        return starts[0]

    # item-nimi sisältyy tähän merkkijonoon: 'buy dagger' -> 'Dagger'
    key_in_raw = [k for k in ITEMS_DB.keys() if k.lower() in raw_lower]
    if len(key_in_raw) == 1:
        return key_in_raw[0]

    # tämä merkkijono sisältyy item-nimeen: 'map' -> 'Old Map'
    contains = [k for k in ITEMS_DB.keys() if raw_lower in k.lower()]
    if len(contains) == 1:
        return contains[0]

    return None


def extract_item_from_text(text: str, catalog: Dict[str, int]) -> str | None:
    """
    Yrittää kaivaa ostettavan itemin nimen vapaamuotoisesta tekstistä
    tietystä katalogista (markkinan tai sepän tuotteista).
    """
    if not text:
        return None
    lower = text.lower()

    # alias-substringit – esim. 'bread' tekstissä -> Loaf of Bread
    for alias_key, alias_val in ALIASES.items():
        if alias_val == "supplies":
            continue
        if alias_key in lower:
            return alias_val

    # katalogin item-nimet tekstissä: 'buy dagger' -> 'Dagger'
    hits = [name for name in catalog.keys() if name.lower() in lower]
    if len(hits) == 1:
        return hits[0]

    return None


# ----------------- liikkumislogiikka -----------------


def maybe_move(state: Dict[str, Any], intent: Intent, raw_text: str = "") -> str:
    """
    Päivittää pelaajan lokaatiota, jos intentti selvästi kertoo liikkumisesta.
    Tunnetut paikat: Village, Blacksmith, Market, Tavern, Cave.

    Kaikki muu liikkumisimprovisaatio (esim. 'go to witch hut') kannattaa antaa
    ensisijaisesti GM:n hoidettavaksi – täällä ei tehdä generisiä uusia paikkoja,
    jotta maailma pysyy hallittavana.
    """
    t = (intent.target or intent.direction or intent.free_text or raw_text or "").lower()

    # yleinen "poistuminen" → takaisin kyläaukiolle
    if "leave" in t or "go back" in t or "step outside" in t:
        loc = state["world"]["location"]
        if loc in ("Blacksmith", "Tavern", "Market", "Cave"):
            state["world"]["location"] = "Village"
            return "You step back out into the village square."

    # varsinaiset MOVE-komennot
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

        # muu liikkuminen (esim. 'go to ruins') annetaan GM:n tulkittavaksi.
        # Serveri ei muuta locationia, mutta GM voi kuvailla ympäristöä
        # nykyisen locationin sisällä.
    return ""


# ----------------- raha & inventory-utilityt -----------------


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


# ----------------- yksinkertainen kauppalogiikka -----------------


def try_shop_purchase(state: Dict[str, Any], intent: Intent, raw_text: str) -> str | None:
    """
    Yksinkertainen sääntöpohjainen kauppa:

      - Market / Village: Loaf of Bread (2c), Torch (1c), Rope (2c),
                          Bandage (2c), Healing Herbs (3c)
      - Blacksmith: Iron Sword (10c), Shield (8c), Dagger (4c)

    Tämän on tarkoitus kattaa *perustapaukset*.
    Kaikki monimutkaisempi kaupankäynti (tinkiminen, erikoisesineet,
    random NPC-kauppiaat uusissa paikoissa) annetaan GM:n hoidettavaksi.
    """
    loc = state["world"]["location"]
    text = (intent.free_text or raw_text or "").lower()

    # vain tietyt paikat saavat automaattisen shop-käsittelyn
    if loc not in ("Blacksmith", "Market", "Village"):
        return None

    market_catalog = {
        "Loaf of Bread": 2,
        "Torch": 1,
        "Rope": 2,
        "Bandage": 2,
        "Healing Herbs": 3,
    }
    blacksmith_catalog = {
        "Iron Sword": 10,
        "Shield": 8,
        "Dagger": 4,
    }

    def filter_existing(catalog: Dict[str, int]) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for name, price in catalog.items():
            k, _ = get_item(name)
            if k:
                out[name] = price
        return out

    market_catalog = filter_existing(market_catalog)
    blacksmith_catalog = filter_existing(blacksmith_catalog)
    catalog = market_catalog if loc in ("Market", "Village") else blacksmith_catalog

    # --- hinnan/kaupan kysely ilman ostamista ---
    hint_words = [
        "price",
        "cost",
        "buy",
        "sell",
        "weapon",
        "sword",
        "axe",
        "shield",
        "dagger",
        "torch",
        "rope",
        "bread",
        "food",
        "rations",
    ]
    if intent.action != "BUY" and any(w in text for w in hint_words):
        if loc == "Blacksmith":
            offers = [f"{name} for {price} coins" for name, price in blacksmith_catalog.items()]
            return (
                "The blacksmith shows you his wares: " + ", ".join(offers) + "."
                if offers
                else "The blacksmith shrugs; his racks are bare today."
            )
        else:
            offers = [f"{name} for {price} coins" for name, price in market_catalog.items()]
            return (
                "Stalls around you offer " + ", ".join(offers) + "."
                if offers
                else "The market is quiet and offers little right now."
            )

    # jos intent ei ole BUY, ei tehdä mitään – GM hoitaa muun kaupankäynnin
    if intent.action != "BUY":
        return None

    # tinkiminen ym. erikoistilanteet → GM:n vastuulle
    if "discount" in text or "cheaper" in text or "haggle" in text or "bargain" in text:
        if loc == "Blacksmith":
            return (
                "The blacksmith chuckles. 'A generous offer, but steel doesn't come cheap. "
                "No discounts today, I'm afraid.'"
            )
        else:
            return (
                "The vendor shakes their head. 'Business is hard enough as it is. "
                "No special discounts today.'"
            )

    # ruoka sepältä → ohjaus markkinalle
    if "food" in text and loc == "Blacksmith":
        return (
            "The blacksmith wipes his hands and grunts: 'I sell steel, not stew. "
            "For food, try the market in the village square.'"
        )

    # --- varsinainen ostaminen: vain selkeät tapaukset ---
    asked_item: str | None = None

    # 1) intent.item jos se tuntuu järkevältä
    if intent.item:
        norm_item = normalize_item_name(intent.item)
        if norm_item and norm_item in catalog:
            asked_item = norm_item

    # 2) yritetään kaivaa item tekstistä (buy dagger, buy bread...)
    if not asked_item:
        extracted = extract_item_from_text(raw_text or intent.free_text or "", catalog)
        if extracted:
            asked_item = extracted

    lower = text
    wanted: list[tuple[str, int]] = []

    # 3) "supplies" / "rations" / "food" marketissa → halvimmat pari juttua
    if not asked_item:
        if loc in ("Market", "Village") and (
            "supplies" in lower or "rations" in lower or "food" in lower
        ):
            if not catalog:
                return "There aren't any suitable supplies available to buy here."
            wanted = sorted(catalog.items(), key=lambda x: x[1])[:2]
        else:
            # epäselvä ostotilanne → anna GM:n käsitellä, ei pakoteta virheviestiä
            return None
    else:
        if asked_item not in catalog:
            # päädytään mieluummin GM:n selitykseen kuin kovaan virheeseen
            return None
        wanted = [(asked_item, catalog[asked_item])]

    total = sum(price for _, price in wanted)
    if count_coins(state) < total:
        items_list = ", ".join(name for name, _ in wanted)
        return f"You don't have enough coins to buy {items_list}. Total cost is {total}."

    if not remove_coins(state, total):
        return "Purchase failed: not enough Gold Coins."

    for name, _ in wanted:
        add_item(state, name, 1)

    items_list = ", ".join(name for name, _ in wanted)
    return f"You buy {items_list} for {total} Gold Coin(s)."

# ------------------------------------------------------
# Include memory in LLM state and record the turn
def handle_turn(state, intent, dice, session_id: str, background_tasks: BackgroundTasks | None = None, player_text: str = ""):
    state_for_llm = build_llm_state(state, session_id)
    intent_dict = intent.model_dump() if hasattr(intent, "model_dump") else intent
    gm_result = make_narration(state_for_llm, intent_dict, dice)

    # Record player + gm pair for short memory
    add_game_turn(player_text or "", gm_result.narration, session_id)

# ----------------- pää-endpoint / peliturni -----------------


@app.post("/api/turn", response_model=TurnOut)
def turn(payload: TurnIn):
    state = ensure_session(payload.session_id)
    dice = {"d20": random.randint(1, 20)}

    # 1) parse player intent (LLM #1)
    intent = parse_intent(state, payload.text)

    # 2) sanity check ennen mitään muutoksia
    ok, reason = sanity_check(state, intent)
    if not ok:
        narration = f"{reason} Try something else."
        choices = ["LOOK around", "Go to cave", "Check inventory"]
        state["turn"] += 1
        state["log"].append({"player": payload.text, "gm": narration})
        return TurnOut(
            narration=narration,
            choices=choices,
            end_game=False,
            state=state,
        )

    # 3) liikkuminen + mahdollinen sääntöpohjainen kauppa
    move_text = maybe_move(state, intent, payload.text)

    shop_text = try_shop_purchase(state, intent, payload.text)
    if shop_text:
        # Jos kauppa hoitui täysin sääntölogiikalla, ei kutsuta GM:ää erikseen.
        narration = (move_text + " " if move_text else "") + shop_text
        narration = narration.strip()

        state["turn"] += 1
        state["log"].append({"player": payload.text, "gm": narration})

        # Tarjoa fiksut nappivalinnat tunnetuissa paikoissa
        if state["world"]["location"] == "Blacksmith":
            base_choices = ["Buy Dagger", "Buy Iron Sword", "Buy Shield"]
        elif state["world"]["location"] in ("Market", "Village"):
            base_choices = ["Buy Torch", "Buy Rope", "Buy Loaf of Bread"]
        else:
            base_choices = []

        def exists(name: str) -> bool:
            k, _ = get_item(name)
            return k is not None

        choices = [c for c in base_choices if exists(c.split("Buy ", 1)[1])]
        if not choices:
            choices = ["LOOK around", "Go to cave", "Return to tavern"]

        return TurnOut(
            narration=narration,
            choices=choices,
            end_game=False,
            state=state,
        )

    # 4) Narraatio (LLM #2)
    gm = handle_turn(state, intent, dice, payload.session_id, background_tasks, player_text=payload.text)

    # 5) hp ja inventoryn muutokset turvallisesti
    apply_health_change(state, int(gm.health_change))

    narration = (move_text + " " if move_text else "") + gm.narration
    narration = narration.strip()

    inventory_change = gm.inventory_change or []
    current_inv = {it["name"].lower(): it for it in state["inventory"]}

    for ch in inventory_change:
        action = ch.action
        item_name = normalize_item_name(ch.item)
        try:
            count = max(1, int(ch.count))
        except Exception:
            count = 1

        # tuntemattomat itemit ohitetaan hiljaa – ei rikota immersiota
        if not item_name:
            continue

        key, item_def = get_item(item_name)
        if not key:
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

    # 6) turn counter + logi
    state["turn"] += 1
    state["log"].append({"player": payload.text, "gm": narration})

    # 7) pelin päättyminen
    if gm.end_game:
        state["game_over"] = True

    return TurnOut(
        narration=narration,
        choices=gm.choices or ["LOOK around", "Go to cave", "Return to tavern"],
        end_game=gm.end_game,
        state=state,
    )
