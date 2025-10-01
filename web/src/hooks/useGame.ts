import { useEffect, useMemo, useRef, useState } from "react";
import { postTurn, type ApiResponse } from "../api/client";

export function useGame() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [history, setHistory] = useState<string[]>([]);
  const [current, setCurrent] = useState<string | null>(null);
  const [choices, setChoices] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // helper: push new narration, move previous current into history
  function pushNarration(n: string) {
    if (current && current.trim().length) {
      setHistory((h) => [current, ...h]); // newest first on top
    }
    setCurrent(n);
  }

  async function send(text: string) {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const data: ApiResponse = await postTurn(sessionId, text);
      pushNarration(data.narration ?? "");
      setChoices(data.choices ?? []);
      return data;
    } finally {
      setLoading(false);
    }
  }

  // kick off
  useEffect(() => {
    send("Start the adventure.");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { sessionId, history, current, choices, loading, send };
}
