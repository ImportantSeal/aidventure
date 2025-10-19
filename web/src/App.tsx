import { useRef } from "react";
import ChatHistory from "./components/ChatHistory";
import TurnPanel from "./components/TurnPanel";
import InventoryPanel from "./components/InventoryPanel";
import ChoiceButtons from "./components/ChoiceButtons";
import { useGame } from "./hooks/useGame";
import "./styles.css";

export default function App() {
  const { history, currentGM, choices, loading, send, currentPlayer, hp, maxHp, inventory } = useGame();
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="container">
      <h1 style={{ margin: "6px 0 14px" }}>AIdventure</h1>

      {/* Main layout: game content (left) and inventory (right)*/}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 24 }}>
        {/* game content */}
        <div style={{ flex: 4, display: "flex", flexDirection: "column", width: "90%" }}>
          {/* History */}
          <ChatHistory items={history} />

          {/* Current turn */}
          <TurnPanel narration={currentGM} playerInput={currentPlayer} />

          {/* Input & choices */}
          <div>
            <div className="row">
              <input
                ref={inputRef}
                className="input"
                placeholder="Type a command (e.g., “sneak into the camp”)"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    const v = inputRef.current?.value?.trim() || "";
                    if (v) {
                      send(v);
                      inputRef.current!.value = "";
                    }
                  }
                }}
              />
              <button
                className="button"
                onClick={() => {
                  const v = inputRef.current?.value?.trim() || "";
                  if (v) {
                    send(v);
                    inputRef.current!.value = "";
                  }
                }}
                disabled={loading}
              >
                {loading ? "…" : "Send"}
              </button>
            </div>

            <ChoiceButtons choices={choices} onChoose={(c) => send(c)} disabled={loading} />

            <p className="hint">
              Tip: try commands like <i>“inspect the camp”</i>, <i>“sneak closer”</i>, or <i>“grab the keg and run”</i>.
            </p>
          </div>
        </div>

        {/* Inventory/Stats */}
        <div style={{ flex: 1, width: "20%" }}>
          <InventoryPanel hp={hp} maxHp={maxHp} inventory={inventory} />
        </div>
      </div>
    </div>
  );
}
