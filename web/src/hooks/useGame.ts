import { useEffect, useRef, useState } from "react";
import { postTurn, type ApiResponse } from "../api/client";

type HistoryEntry = { player: string; gm: string };

export function useGame() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [current, setCurrent] = useState<string | null>(null);
  const [choices, setChoices] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // store the "last player command" so we can pair it with GM narration on the next turn
  const lastPlayerRef = useRef<string | null>(null);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    setLoading(true);
    try {
      // keep track of previous GM narration and player command
      const prevCurrent = current;
      const prevPlayer = lastPlayerRef.current;
      const sentNow = trimmed;

      const data: ApiResponse = await postTurn(sessionId, trimmed);

      // if we have a previous pair, move it into history now
      if (prevCurrent && prevPlayer) {
        setHistory((h) => [...h, { player: prevPlayer, gm: prevCurrent }]);
      }

      // update current GM narration and choices
      setCurrent(data.narration ?? "");
      setChoices(data.choices ?? []);

      // remember the player's command for the next turn
      lastPlayerRef.current = sentNow;

      return data;
    } finally {
      setLoading(false);
    }
  }

  // start the game automatically on mount
  useEffect(() => {
    send("Start the adventure.");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { sessionId, history, current, choices, loading, send };
}
