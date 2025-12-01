# server/core/types.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

ActionType = Literal[
    "LOOK", "MOVE", "TALK", "ATTACK", "USE_ITEM",
    "TAKE_ITEM", "DROP_ITEM", "GIVE_ITEM", "RUN", "WAIT",
    "BUY", "OTHER"
]

class Intent(BaseModel):
    action: ActionType
    target: Optional[str] = None
    item: Optional[str] = None
    quantity: int = 1
    direction: Optional[str] = None
    free_text: Optional[str] = None

class InventoryChange(BaseModel):
    action: Literal["add", "use", "remove"]
    item: str
    count: int = 1

class GMResult(BaseModel):
    narration: str
    choices: List[str] = Field(default_factory=list)
    end_game: bool = False
    health_change: int = 0
    inventory_change: List[InventoryChange] = Field(default_factory=list)

class TurnIn(BaseModel):
    session_id: str
    text: str

class TurnOut(BaseModel):
    narration: str
    choices: List[str]
    end_game: bool
    state: Dict[str, Any]
