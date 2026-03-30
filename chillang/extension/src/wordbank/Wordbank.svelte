<script>
  import { onMount } from 'svelte';

  let words = $state([]);
  let loading = $state(true);

  onMount(async () => {
    const data = await chrome.storage.local.get('saved_words');
    words = (data.saved_words || []).sort((a, b) => b.savedAt - a.savedAt);
    loading = false;
  });

  async function removeWord(wordId) {
    words = words.filter(w => w.wordId !== wordId);
    await chrome.storage.local.set({ saved_words: words });
  }

  function formatDate(ts) {
    return new Date(ts).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric'
    });
  }
</script>

<div class="wordbank">
  <h1>Word Bank</h1>
  <p class="subtitle">{words.length} saved word{words.length !== 1 ? 's' : ''}</p>

  {#if loading}
    <p class="empty">Loading...</p>
  {:else if words.length === 0}
    <div class="empty">
      <p>No saved words yet.</p>
      <p class="hint">Double-click any English word on a webpage to get started.</p>
    </div>
  {:else}
    <ul class="word-list">
      {#each words as word (word.wordId)}
        <li class="word-item">
          <div class="word-text">{word.text}</div>
          <div class="word-meta">
            <span class="date">{formatDate(word.savedAt)}</span>
            <button class="remove-btn" onclick={() => removeWord(word.wordId)} aria-label="Remove">
              &#x2715;
            </button>
          </div>
        </li>
      {/each}
    </ul>
  {/if}

  <div class="footer-note">
    <p>Flashcard game coming soon!</p>
  </div>
</div>

<style>
  .wordbank {
    min-height: 360px;
    display: flex;
    flex-direction: column;
  }

  h1 {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 2px;
  }

  .subtitle {
    font-size: 12px;
    color: #888;
    margin-bottom: 16px;
  }

  .empty {
    text-align: center;
    padding: 40px 0;
    color: #888;
  }
  .empty .hint {
    font-size: 12px;
    margin-top: 8px;
    color: #aaa;
  }

  .word-list {
    list-style: none;
    flex: 1;
  }

  .word-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
  }

  @media (prefers-color-scheme: dark) {
    .word-item { border-color: #45475a; }
    .subtitle { color: #a6adc8; }
  }

  .word-text {
    font-weight: 500;
    font-size: 14px;
  }

  .word-meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .date {
    font-size: 11px;
    color: #aaa;
  }

  .remove-btn {
    background: none;
    border: none;
    color: #ccc;
    cursor: pointer;
    font-size: 12px;
    padding: 2px 4px;
  }
  .remove-btn:hover { color: #e74c3c; }

  .footer-note {
    margin-top: auto;
    padding-top: 12px;
    text-align: center;
    font-size: 12px;
    color: #aaa;
  }
</style>
