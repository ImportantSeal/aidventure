import { useRef } from "react";
import ChatHistory from "./components/ChatHistory";
import TurnPanel from "./components/TurnPanel";
import InventoryPanel from "./components/InventoryPanel";
import ChoiceButtons from "./components/ChoiceButtons";
import MapPanel from "./components/MapPanel";
import { useGame } from "./hooks/useGame";
import "./styles.css";

export default function App() {
  const { history, currentGM, choices, loading, send, currentPlayer, hp, maxHp, inventory, state } = useGame();
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="container">
      <h1 style={{ margin: "6px 0 14px" }}>AIdventure</h1>
      {/* Main layout: left sprite box, game content (center) and inventory/map (right) */}
        <div style={{ display: "flex", alignItems: "stretch", gap: 24 }}>
        {/* Left sprite box */}
          <div style={{ flexBasis: 220, flexShrink: 0, display: "flex", flexDirection: "column" }}>
            <div
              className="panel"
              style={{
                width: "100%",
                display: "flex",
                flexDirection: "column",
                padding: 10,
                boxSizing: "border-box",
                backgroundImage: "url('/assets/spritebackground.jpg')",
                backgroundSize: "cover",
                backgroundPosition: "center",
                borderRadius: 10,
              }}
            >
              <div style={{ fontSize: 12, color: "black", marginBottom: 8, textAlign: "center" }}>GOD</div>
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <img
                  src="/assets/knightidle.gif"
                  alt="Player sprite"
                  style={{ width: "100%", height: "100%", maxWidth: 200, objectFit: "contain", borderRadius: 8 }}
                />
              </div>
            </div>
          </div>

        {/* game content (narrower chat) */}
        <div style={{ flex: 3, display: "flex", flexDirection: "column", minWidth: 0 }}>
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
                placeholder="Type a command (e.g., 'sneak into the camp')"
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
              Tip: try commands like <i>"inspect the camp"</i>, <i>"sneak closer"</i>, or <i>"grab the keg and run"</i>.
            </p>
          </div>
        </div>

        {/* Right column: stats/inventory (top) and map (bottom) */}
        <div style={{ flexBasis: 220, flexShrink: 0, display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <InventoryPanel hp={hp} maxHp={maxHp} inventory={inventory} />
          </div>

          <div className="panel" style={{ height: 180 }}>
            <div style={{ height: "100%", padding: 10, boxSizing: "border-box" }}>
              <MapPanel state={state} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
