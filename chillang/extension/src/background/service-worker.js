import { lookupWord, voteAnswer } from "../lib/api.js";
import {
  getBrowserId,
  isWordSaved,
  saveWord,
  unsaveWord,
} from "../lib/storage.js";

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  handleMessage(msg).then(sendResponse);
  return true; // keep channel open for async
});

async function handleMessage(msg) {
  const browserId = await getBrowserId();

  switch (msg.action) {
    case "lookup": {
      const data = await lookupWord(msg.text, browserId);
      const saved = data.word ? await isWordSaved(data.word.id) : false;
      return { ...data, saved };
    }

    case "vote": {
      return voteAnswer(msg.wordId, msg.answerId, browserId, msg.value);
    }

    case "save": {
      await saveWord(msg.wordId, msg.text);
      return { saved: true };
    }

    case "unsave": {
      await unsaveWord(msg.wordId);
      return { saved: false };
    }

    default:
      return { error: "Unknown action" };
  }
}
