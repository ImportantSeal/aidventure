import { useEffect, useRef, useState } from "react";
import { postTurn, type ApiResponse } from "../api/client";

type HistoryEntry = { player: string; gm: string };

export function useGame() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [currentGM, setCurrentGM] = useState<string | null>(null);
  const [choices, setChoices] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPlayer, setCurrentPlayer] = useState<string | null>(null);

  const [hp, setHp] = useState<number>(10);
  const [maxHp, setMaxHp] = useState<number>(10);
  const [inventory, setInventory] = useState<{name: string; count: number}[]>([]);

  // store the "last player command" so we can pair it with GM narration on the next turn
  const lastPlayerRef = useRef<string | null>(null);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    setLoading(true);
    try {
      // keep track of previous GM narration and player command
      const prevCurrent = currentGM;
      const prevPlayer = lastPlayerRef.current;
      const sentNow = trimmed;

      const data: ApiResponse = await postTurn(sessionId, trimmed);

      // if we have a previous pair, move it into history now
      if (prevCurrent && prevPlayer) {
        setHistory((h) => [...h, { player: prevPlayer, gm: prevCurrent }]);
      }

      // update current GM narration and choices
      setCurrentGM(data.narration ?? "");
      setChoices(data.choices ?? []);

      // Update stats from backend state
      setHp(data.state.player.hp);
      setMaxHp(data.state.player.max_hp);
      setInventory(data.state.inventory);

      // remember the player's command for the next turn
      lastPlayerRef.current = sentNow;
      setCurrentPlayer(sentNow);

      return data;
    } finally {
      setLoading(false);
    }
  }

  // start the game automatically on mount
  useEffect(() => {
    setCurrentPlayer("Start the adventure.");
    send("Start the adventure.");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { sessionId, history, currentGM, choices, loading, send, currentPlayer, hp, maxHp, inventory };
}
