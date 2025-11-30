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
          <div style={{ flexBasis: 320, flexShrink: 0, display: "flex", flexDirection: "column" }}>
            {(() => {
              // Determine background image based on location
              const loc = state?.world?.location || "default";
              // Lowercase, no spaces, fallback to default
              const locKey = String(loc).toLowerCase().replace(/\s+/g, "");
              const bgUrl = `/assets/spritebg_${locKey}.jpg`;
              // If you want to check if the file exists, you could add logic or just let the browser fallback
              // If you want a default fallback, use a backgroundImage with multiple URLs
              const backgroundImage = `url('${bgUrl}'), url('/assets/spritebackground.jpg')`;
              return (
                <div
                  className="panel"
                  style={{
                    width: "100%",
                    minHeight: 320,
                    display: "flex",
                    flexDirection: "column",
                    padding: 18,
                    boxSizing: "border-box",
                    backgroundImage,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                    borderRadius: 16,
                  }}
                >
                  <div style={{ fontSize: 15, color: "black", marginBottom: 12, textAlign: "center", fontWeight: 700 }}>GOD</div>
                  <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <img
                      src="/assets/knightidle.gif"
                      alt="Player sprite"
                      style={{ width: "90%", height: "90%", maxWidth: 260, objectFit: "contain", borderRadius: 12, boxShadow: "0 2px 16px #0004" }}
                    />
                  </div>
                </div>
              );
            })()}
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
