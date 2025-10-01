export type ApiResponse = {
  narration: string;
  choices: string[];
  end_game: boolean;
  state: any;
};

export async function postTurn(sessionId: string, text: string): Promise<ApiResponse> {
  const res = await fetch("/api/turn", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, text }),
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}
