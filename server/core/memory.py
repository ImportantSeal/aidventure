from typing import List, Dict, Any, Callable, Optional

def _trim_summary(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars]
    # try to end at last period within the cut
    dot = cut.rfind(".")
    if dot >= 50:  # avoid trimming to a very short fragment
        return cut[:dot + 1]
    return cut

class MemoryManager:
    def __init__(self, short_term_limit: int = 5, max_long_chars: int = 1200):
        self.short_term_limit = short_term_limit
        self.max_long_chars = max_long_chars
        # store pairs in short-term: {"player": str, "gm": str}
        self._short_texts: List[Dict[str, str]] = []
        self._pending_texts: List[str] = []   # new texts since last summary
        self._long_summary: str = ""          # running summary of all events

    def add_turn_text(self, player_text: str, gm_text: str) -> None:
        player_text = (player_text or "").strip()
        gm_text = (gm_text or "").strip()
        if not player_text and not gm_text:
            return
        self._short_texts.append({"player": player_text, "gm": gm_text})
        if len(self._short_texts) > self.short_term_limit:
            self._short_texts.pop(0)
        if gm_text:
            self._pending_texts.append(gm_text)

    def update_long_summary(self, summarize_func) -> None:
        if not self._pending_texts and self._long_summary:
            return
        new_summary = summarize_func(self._long_summary, self._pending_texts)
        if new_summary:
            self._long_summary = _trim_summary(new_summary.strip(), self.max_long_chars)
            self._pending_texts.clear()

    def get_short_texts(self) -> List[Dict[str, str]]:
        return list(self._short_texts)

    def get_long_summary(self) -> str:
        return self._long_summary

# Session-scoped registry
_MANAGERS: Dict[str, MemoryManager] = {}

def get_memory_manager(session_id: str) -> MemoryManager:
    mgr = _MANAGERS.get(session_id)
    if mgr is None:
        mgr = MemoryManager(short_term_limit=5, max_long_chars=1200)
        _MANAGERS[session_id] = mgr
    return mgr

def reset_memory(session_id: str) -> None:
    if session_id in _MANAGERS:
        del _MANAGERS[session_id]