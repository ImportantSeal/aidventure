import { useRef } from "react";
import ChatHistory from "./components/ChatHistory";
import TurnPanel from "./components/TurnPanel";
import ChoiceButtons from "./components/ChoiceButtons";
import { useGame } from "./hooks/useGame";
import "./styles.css";

export default function App() {
  const { history, currentGM, choices, loading, send, currentPlayer } = useGame();
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="container">
      <h1 style={{ margin: "6px 0 14px" }}>AIdventure</h1>

      {/* history on top */}
      <ChatHistory items={history} />

      {/* the last user input and the narration based on it */}
      <TurnPanel narration={currentGM} playerInput={currentPlayer} />

      {/* user input */}
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

      {/* 4) Suggested choices */}
      <ChoiceButtons choices={choices} onChoose={(c) => send(c)} disabled={loading} />

      <p className="hint">
        Tip: try commands like <i>“inspect the camp”</i>, <i>“sneak closer”</i>, or <i>“grab the keg and run”</i>.
      </p>
    </div>
  );
}
