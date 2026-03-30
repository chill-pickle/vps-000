const storage = chrome.storage.local;

export async function getBrowserId() {
  const data = await storage.get("browser_id");
  if (data.browser_id) return data.browser_id;
  const id = crypto.randomUUID();
  await storage.set({ browser_id: id });
  return id;
}

export async function saveWord(wordId, text) {
  const data = await storage.get("saved_words");
  const words = data.saved_words || [];
  if (words.some((w) => w.wordId === wordId)) return;
  words.push({ wordId, text, savedAt: Date.now() });
  await storage.set({ saved_words: words });
}

export async function unsaveWord(wordId) {
  const data = await storage.get("saved_words");
  const words = (data.saved_words || []).filter((w) => w.wordId !== wordId);
  await storage.set({ saved_words: words });
}

export async function getSavedWords() {
  const data = await storage.get("saved_words");
  return data.saved_words || [];
}

export async function isWordSaved(wordId) {
  const data = await storage.get("saved_words");
  return (data.saved_words || []).some((w) => w.wordId === wordId);
}
