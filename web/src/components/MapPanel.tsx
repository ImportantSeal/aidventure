import React from "react";

type Props = {
  state: any;
  cols?: number;
  rows?: number;
};

// 4x4 grid: mapping from backend location names to tile coordinates (col, row)
const LOCATION_TO_COORD: Record<string, [number, number]> = {
  "Village": [1, 1],
  "Market": [1, 2],
  "Tavern": [2, 1],
  "Cave": [2, 2],
  "Blacksmith": [3, 1],
};

const COORD_TO_LOCATION: Record<string, string> = Object.fromEntries(
  Object.entries(LOCATION_TO_COORD).map(([name, [col, row]]) => [[col, row].join(","), name])
);

export default function MapPanel({ state, cols = 4, rows = 4 }: Props) {
  // Player's current location from backend state
  const playerLoc = state?.world?.location ?? "Town";
  const coord = LOCATION_TO_COORD[playerLoc] || [1, 1];
  const [px, py] = coord;

  const tiles: React.ReactNode[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const isPlayer = c === px && r === py;
      const locName = COORD_TO_LOCATION[[c, r].join(",")];
      tiles.push(
        <div
          key={`${r}-${c}`}
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: isPlayer ? "linear-gradient(180deg,#fde68a,#fca5a5)" : locName ? "#b3e0ff" : "#e0e0e0",
            border: "1px solid rgba(0,0,0,0.10)",
            boxSizing: "border-box",
            fontSize: 13,
            fontWeight: locName ? 600 : 400,
            color: isPlayer ? "#a21caf" : locName ? "#222" : "#aaa",
          }}
        >
          {isPlayer ? (
            <img src="/assets/knightidle.gif" alt="player" style={{ width: "60%", height: "60%", objectFit: "contain" }} />
          ) : locName ? locName : ""}
        </div>
      );
    }
  }

  return (
    <div style={{ width: "100%", height: "100%", display: "grid", gridTemplateColumns: `repeat(${cols}, 1fr)`, gridAutoRows: "1fr", gap: 6 }}>
      {tiles}
    </div>
  );
}
