import React, { useEffect, useState } from "react";
type Props = {
  narration: string | null;
  playerInput: string | null;
};

export default function TurnPanel({ narration, playerInput }: Props) {
  // Typewriter effect for narration
  const [displayed, setDisplayed] = useState("");
  useEffect(() => {
    if (!narration) {
      setDisplayed("");
      return;
    }
    setDisplayed("");
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setDisplayed(narration.slice(0, i));
      if (i >= narration.length) clearInterval(interval);
    }, 18); // ~55 chars/sec
    return () => clearInterval(interval);
  }, [narration]);
  return (
    <section aria-label="Current turn">
      <h2 className="panelTitle">Current turn</h2>
      <div className="panel">
        <div className="panelBody">
          {playerInput && (
            <div>
              <div style={{ color: "#2563eb", fontWeight: 600 }}>You:</div>
                <div style={{ marginBottom: 6 }}>{playerInput ?? "…"}</div>
            </div>
          )}
          {narration && (
            <div>
              <div style={{ color: "#16a34a", fontWeight: 600 }}>GM:</div>
                <div>{displayed || "…"}</div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
