type Props = {
  narration: string | null;
  playerInput: string | null;
};

export default function TurnPanel({ narration, playerInput }: Props) {
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
                <div>{narration ?? "…"}</div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
