import { useEffect, useRef } from "react";

type Entry = { player: string; gm: string };
type Props = { items: Entry[] };

export default function ChatHistory({ items }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // scroll to bottom whenever items change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [items]);

  return (
    <section aria-label="History" style={{ marginBottom: 16 }}>
      <h2 className="panelTitle">History</h2>
      <div className="panel" style={{ maxHeight: 300, overflow: "auto" }}>
        <div className="panelBody">
          {items.length === 0 ? (
            <div style={{ opacity: 0.8 }}>No earlier turns yet.</div>
          ) : (
            <ul className="historyList">
              {items.map((entry, i) => (
                <li key={i} className="historyItem">
                  <div style={{ color: "#2563eb", fontWeight: 600 }}>You:</div>
                  <div style={{ marginBottom: 6 }}>{entry.player}</div>
                  <div style={{ color: "#16a34a", fontWeight: 600 }}>GM:</div>
                  <div>{entry.gm}</div>
                </li>
              ))}
              {/* invisible anchor for scroll-to-bottom */}
              <div ref={bottomRef} />
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
