type Props = {
  narration: string | null;
};

export default function TurnPanel({ narration }: Props) {
  return (
    <section aria-label="Current turn">
      <h2 className="panelTitle">Current turn</h2>
      <div className="panel">
        <div className="panelBody">
          {narration ?? "…"}
        </div>
      </div>
    </section>
  );
}
