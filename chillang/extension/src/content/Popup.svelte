<script>
  let { data = null, onClose = () => {}, onVote = () => {}, onSave = () => {} } = $props();

  let saved = $state(data?.saved ?? true);
  let userVote = $state(data?.answer?.user_vote ?? null);
  let score = $state(data?.answer?.score ?? 0);
  let loading = $state(false);

  $effect(() => {
    if (data) {
      saved = data.saved ?? true;
      userVote = data.answer?.user_vote ?? null;
      score = data.answer?.score ?? 0;
    }
  });

  function highlightWord(sentence, word) {
    if (!word || !sentence) return sentence;
    const regex = new RegExp(`(${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return sentence.replace(regex, '<strong>$1</strong>');
  }

  async function handleVote(value) {
    if (loading) return;
    const newValue = userVote === value ? 0 : value;
    loading = true;
    const result = await onVote(data.word.id, data.answer.id, newValue);
    if (result) {
      score = result.new_score;
      userVote = result.user_vote;
    }
    loading = false;
  }

  async function handleSave() {
    saved = !saved;
    await onSave(data.word.id, data.word.text, saved);
  }
</script>

{#if data}
<div class="chillang-popup" role="dialog" aria-label="ChilLang translation">
  <!-- Header -->
  <div class="header">
    <div class="word-info">
      <span class="word">{data.word.text}</span>
      {#if data.answer?.word_type && !data.word.is_phrase}
        <span class="badge">{data.answer.word_type}</span>
      {/if}
    </div>
    <button class="close-btn" onclick={onClose} aria-label="Close">&#x2715;</button>
  </div>

  {#if data.status === 'pending' || !data.answer}
    <div class="pending">
      <p>Translation is being generated...</p>
      <p class="hint">Try again in a moment.</p>
    </div>
  {:else}
    <!-- Translation -->
    <div class="section">
      <span class="label">VN</span>
      <span class="translation">{data.answer.translation}</span>
    </div>

    <!-- Meaning -->
    <div class="section">
      <span class="label">EN</span>
      <span class="meaning">{data.answer.meaning}</span>
    </div>

    <!-- Examples -->
    <div class="examples">
      <span class="label">Examples</span>
      <ol>
        {#each data.answer.examples as ex}
          <li>{@html highlightWord(ex, data.word.text)}</li>
        {/each}
      </ol>
    </div>

    <!-- Actions -->
    <div class="actions">
      <div class="vote-group">
        <button
          class="vote-btn"
          class:active={userVote === 1}
          onclick={() => handleVote(1)}
          disabled={loading}
          aria-label="Like"
        >
          &#x1F44D; {score}
        </button>
        <button
          class="vote-btn dislike"
          class:active={userVote === -1}
          onclick={() => handleVote(-1)}
          disabled={loading}
          aria-label="Dislike"
        >
          &#x1F44E;
        </button>
      </div>
      <button class="save-btn" class:saved onclick={handleSave}>
        {saved ? '&#x2713; Saved' : '&#x2B; Save'}
      </button>
    </div>

    <!-- Footer -->
    {#if data.answer_count > 1}
      <div class="footer">
        <span class="answer-nav">Answer 1 of {data.answer_count}</span>
      </div>
    {/if}
  {/if}
</div>
{/if}

<style>
  .chillang-popup {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    width: 360px;
    max-height: 420px;
    overflow-y: auto;
    background: #fff;
    color: #1a1a1a;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    padding: 16px;
    font-size: 14px;
    line-height: 1.5;
    z-index: 2147483647;
  }

  @media (prefers-color-scheme: dark) {
    .chillang-popup {
      background: #1e1e2e;
      color: #cdd6f4;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .badge { background: #45475a; color: #a6adc8; }
    .label { color: #a6adc8; }
    .meaning { color: #bac2de; }
    .examples ol li { color: #bac2de; }
    .vote-btn { background: #313244; color: #cdd6f4; border-color: #45475a; }
    .vote-btn:hover { background: #45475a; }
    .vote-btn.active { border-color: #89b4fa; background: #313244; }
    .vote-btn.dislike.active { border-color: #f38ba8; }
    .save-btn { background: #313244; color: #cdd6f4; border-color: #45475a; }
    .save-btn.saved { background: #1e4620; color: #a6e3a1; border-color: #a6e3a1; }
    .footer { border-color: #45475a; }
    .answer-nav { color: #a6adc8; }
    .close-btn { color: #a6adc8; }
    .close-btn:hover { color: #f38ba8; }
    .pending .hint { color: #a6adc8; }
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .word-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .word {
    font-size: 18px;
    font-weight: 700;
  }

  .badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    background: #e8e8e8;
    color: #666;
    font-weight: 500;
    text-transform: lowercase;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    color: #999;
    padding: 4px;
    line-height: 1;
  }
  .close-btn:hover { color: #e74c3c; }

  .section {
    margin-bottom: 10px;
  }

  .label {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    margin-right: 6px;
    min-width: 22px;
  }

  .translation {
    font-size: 16px;
    font-weight: 600;
    color: #2563eb;
  }

  @media (prefers-color-scheme: dark) {
    .translation { color: #89b4fa; }
  }

  .meaning {
    color: #444;
  }

  .examples {
    margin-bottom: 12px;
  }

  .examples ol {
    margin: 4px 0 0 0;
    padding-left: 20px;
  }

  .examples ol li {
    margin-bottom: 4px;
    color: #555;
    font-size: 13px;
  }

  .examples ol li :global(strong) {
    color: #2563eb;
    font-weight: 600;
  }

  @media (prefers-color-scheme: dark) {
    .examples ol li :global(strong) { color: #89b4fa; }
  }

  .actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
  }

  .vote-group {
    display: flex;
    gap: 6px;
  }

  .vote-btn {
    background: #f5f5f5;
    border: 1.5px solid #ddd;
    border-radius: 8px;
    padding: 4px 12px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.15s;
  }
  .vote-btn:hover { background: #e8e8e8; }
  .vote-btn.active { border-color: #2563eb; background: #eff6ff; }
  .vote-btn.dislike.active { border-color: #e74c3c; background: #fef2f2; }
  .vote-btn:disabled { opacity: 0.6; cursor: not-allowed; }

  .save-btn {
    background: #f5f5f5;
    border: 1.5px solid #ddd;
    border-radius: 8px;
    padding: 4px 14px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.15s;
  }
  .save-btn.saved {
    background: #dcfce7;
    color: #166534;
    border-color: #86efac;
  }

  .footer {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid #eee;
    text-align: center;
  }

  .answer-nav {
    font-size: 12px;
    color: #888;
  }

  .pending {
    text-align: center;
    padding: 20px 0;
  }
  .pending .hint {
    font-size: 12px;
    color: #888;
    margin-top: 4px;
  }
</style>
