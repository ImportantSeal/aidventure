

type Props = {
  hp: number;
  maxHp: number;
  inventory: {name: string; count: number}[];
};

export default function InventoryPanel({ hp, maxHp, inventory }: Props) {
  return (
    <section aria-label="Inventory">
      <h2 className="panelTitle">Stats & Inventory</h2>
      <div className="panel">
        <div className="panelBody">
          {/* Health Bar */}
          <div style={{ marginBottom: 10 }}>
            <strong>Health:</strong> {hp} / {maxHp}
            <div
              style={{
                background: "#ddd",
                height: 10,
                borderRadius: 4,
                marginTop: 4,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${(hp / maxHp) * 100}%`,
                  height: "100%",
                  background: hp > maxHp * 0.5 ? "#16a34a" : "#dc2626",
                  transition: "width 0.3s ease",
                }}
              />
            </div>
          </div>

          {/* Inventory */}
          <strong>Inventory:</strong>
          {inventory.length === 0 ? (
            <div style={{ opacity: 0.7, marginTop: 4 }}>No items yet.</div>
          ) : (
            <ul style={{ marginTop: 4, paddingLeft: 18 }}>
              {inventory.map((item, i) => (
                <li key={i}>
                  {item.name} {item.count > 1 ? `(x${item.count})` : ""}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
