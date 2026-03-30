import Popup from "./Popup.svelte";

let popupHost = null;
let popupComponent = null;
let translateBtn = null;

// --- Popup lifecycle ---

function removePopup() {
  if (popupComponent) {
    popupComponent.$destroy();
    popupComponent = null;
  }
  if (popupHost) {
    popupHost.remove();
    popupHost = null;
  }
}

function removeTranslateBtn() {
  if (translateBtn) {
    translateBtn.remove();
    translateBtn = null;
  }
}

function showPopup(rect, data) {
  removePopup();
  removeTranslateBtn();

  popupHost = document.createElement("div");
  popupHost.id = "chillang-host";
  popupHost.style.cssText =
    "position:fixed;z-index:2147483647;pointer-events:auto;";

  // Position below the selection, or above if near bottom
  const top = rect.bottom + 8;
  const flipAbove = top + 440 > window.innerHeight;
  popupHost.style.top = flipAbove
    ? `${Math.max(8, rect.top - 440)}px`
    : `${top}px`;
  popupHost.style.left = `${Math.min(rect.left, window.innerWidth - 380)}px`;

  document.body.appendChild(popupHost);

  const shadow = popupHost.attachShadow({ mode: "open" });
  const mountEl = document.createElement("div");
  shadow.appendChild(mountEl);

  popupComponent = new Popup({
    target: mountEl,
    props: {
      data,
      onClose: removePopup,
      onVote: handleVote,
      onSave: handleSave,
    },
  });
}

function showLoading(rect, text) {
  removePopup();
  removeTranslateBtn();

  popupHost = document.createElement("div");
  popupHost.id = "chillang-host";
  popupHost.style.cssText =
    "position:fixed;z-index:2147483647;pointer-events:auto;";

  const top = rect.bottom + 8;
  popupHost.style.top = `${top}px`;
  popupHost.style.left = `${Math.min(rect.left, window.innerWidth - 380)}px`;

  document.body.appendChild(popupHost);

  const shadow = popupHost.attachShadow({ mode: "open" });
  const mountEl = document.createElement("div");
  shadow.appendChild(mountEl);

  // Show a minimal loading state
  popupComponent = new Popup({
    target: mountEl,
    props: {
      data: {
        word: { id: 0, text, is_phrase: text.includes(" ") },
        answer: null,
        answer_count: 0,
        status: "pending",
        saved: false,
      },
      onClose: removePopup,
      onVote: () => {},
      onSave: () => {},
    },
  });
}

// --- Message handlers ---

async function lookup(text, rect) {
  showLoading(rect, text);
  try {
    const data = await chrome.runtime.sendMessage({
      action: "lookup",
      text,
    });
    if (data.error) {
      removePopup();
      return;
    }
    showPopup(rect, data);
  } catch {
    removePopup();
  }
}

async function handleVote(wordId, answerId, value) {
  try {
    return await chrome.runtime.sendMessage({
      action: "vote",
      wordId,
      answerId,
      value,
    });
  } catch {
    return null;
  }
}

async function handleSave(wordId, text, shouldSave) {
  try {
    await chrome.runtime.sendMessage({
      action: shouldSave ? "save" : "unsave",
      wordId,
      text,
    });
  } catch {
    // silent
  }
}

// --- Selection detection ---

function getSelectedText() {
  const selection = window.getSelection();
  return selection ? selection.toString().trim() : "";
}

function getSelectionRect() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  return selection.getRangeAt(0).getBoundingClientRect();
}

function isSingleWord(text) {
  return text.length > 0 && !text.includes(" ");
}

// Double-click: single word → immediate lookup
document.addEventListener("dblclick", () => {
  const text = getSelectedText();
  const rect = getSelectionRect();
  if (text && isSingleWord(text) && rect) {
    lookup(text, rect);
  }
});

// Mouseup: multi-word selection → show translate button
document.addEventListener("mouseup", (e) => {
  // Ignore clicks inside our own popup or translate button
  if (e.target.closest?.("#chillang-host") || e.target.closest?.("#chillang-translate-btn")) {
    return;
  }

  // Small delay to let double-click handler fire first
  setTimeout(() => {
    const text = getSelectedText();
    const rect = getSelectionRect();

    if (text && !isSingleWord(text) && rect) {
      showTranslateButton(rect, text);
    } else if (!text) {
      removeTranslateBtn();
    }
  }, 200);
});

// Click outside → dismiss
document.addEventListener("mousedown", (e) => {
  if (
    popupHost &&
    !popupHost.contains(e.target) &&
    e.target.id !== "chillang-translate-btn"
  ) {
    removePopup();
  }
  if (
    translateBtn &&
    e.target.id !== "chillang-translate-btn"
  ) {
    removeTranslateBtn();
  }
});

// Escape key → dismiss
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    removePopup();
    removeTranslateBtn();
  }
});

// --- Translate button for phrases ---

function showTranslateButton(rect, text) {
  removeTranslateBtn();

  translateBtn = document.createElement("button");
  translateBtn.id = "chillang-translate-btn";
  translateBtn.textContent = "Translate";
  translateBtn.style.cssText = `
    position: fixed;
    z-index: 2147483647;
    top: ${rect.bottom + 4}px;
    left: ${rect.left}px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    transition: background 0.15s;
  `;
  translateBtn.addEventListener("mouseenter", () => {
    translateBtn.style.background = "#1d4ed8";
  });
  translateBtn.addEventListener("mouseleave", () => {
    translateBtn.style.background = "#2563eb";
  });
  translateBtn.addEventListener("click", () => {
    lookup(text, rect);
  });

  document.body.appendChild(translateBtn);
}
