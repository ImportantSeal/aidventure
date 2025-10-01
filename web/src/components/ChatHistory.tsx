type Props = {
  items: string[];
};

export default function ChatHistory({ items }: Props) {
  return (
    <section aria-label="History" style={{ marginBottom: 16 }}>
      <h2 className="panelTitle">History</h2>
      <div className="panel" style={{ maxHeight: 300, overflow: "auto" }}>
        <div className="panelBody">
          {items.length === 0 ? (
            <div style={{ opacity: 0.8 }}>No earlier turns yet.</div>
          ) : (
            <ul className="historyList">
              {items.map((n, i) => (
                <li key={i} className="historyItem">{n}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
