const BASE_URL =
  import.meta.env.VITE_API_URL || "https://api.chillang.chillpickle.org/api/v1";

export async function lookupWord(text, browserId) {
  const res = await fetch(`${BASE_URL}/words`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, browser_id: browserId }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getAnswers(wordId, browserId) {
  const params = browserId ? `?browser_id=${browserId}` : "";
  const res = await fetch(`${BASE_URL}/words/${wordId}/answers${params}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function voteAnswer(wordId, answerId, browserId, value) {
  const res = await fetch(
    `${BASE_URL}/words/${wordId}/answers/${answerId}/vote`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ browser_id: browserId, value }),
    }
  );
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
