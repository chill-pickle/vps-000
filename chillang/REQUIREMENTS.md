# ChilLang — Requirements

> A Chrome extension for learning English through everyday browsing, with Vietnamese translation, community voting, and a personal word bank.

## 1. Overview

ChilLang lets users look up English words and phrases while browsing any website. When a user double-clicks a word or highlights a phrase, a popup appears with the Vietnamese translation, English definition, usage examples, and word type. Users can vote on answer quality and save words to a personal bank stored in the browser. A self-hosted backend manages the shared word database and generates translations via LLM.

## 2. Chrome Extension (Frontend)

### 2.1 Word Selection

| Trigger | Input | Behavior |
|---------|-------|----------|
| Double-click | Single word | Popup appears immediately near the word |
| Text highlight (mouseup) | Multi-word phrase/sentence | A small "Translate" button appears near selection; clicking it opens the popup |

- Clicking outside the popup dismisses it.
- Only one popup visible at a time.

### 2.2 Popup Content

For **single words**, the popup displays:

| Field | Description |
|-------|-------------|
| Word | The selected word |
| Word type | Part of speech — noun, verb, adj, adv, etc. |
| Vietnamese translation | Natural Vietnamese equivalent(s) |
| English meaning | Concise definition in English |
| Examples | 3 example sentences using the word (word bolded in each) |
| Vote buttons | Like / Dislike with current score |
| Save toggle | Checkbox to save the word (default: ON) |
| Answer navigation | "Answer 1 of N" with option to see all answers |

For **phrases/sentences**, same layout but **without** word type.

### 2.3 Voting

- Each answer can be liked or disliked.
- The popup shows the highest-voted answer by default.
- Users can browse alternative answers via "See all".
- One vote per answer per browser instance (tracked by a generated UUID).
- Votes are toggleable: click again to undo, or switch between like/dislike.

### 2.4 Word Bank (Save)

- Save toggle defaults to ON — words are saved passively as users browse.
- Saved word IDs are stored in `chrome.storage.local` (no account needed).
- Clicking the extension toolbar icon opens the Word Bank page listing all saved words.

### 2.5 Flashcard Game (Future)

- Accessible from the Word Bank page.
- Shows saved words one at a time as flashcards.
- User taps to reveal the Vietnamese translation.
- User marks "Remember" or "Don't Remember".
- Progress tracked locally in the browser.

### 2.6 UX/UI Guidelines

- Popup width: ~360px, max height ~400px (scrollable).
- Clean, minimal design — enough info to be useful, not overwhelming.
- Dark/light mode based on system preference.
- Loading skeleton while waiting for API response.
- Error state with retry button if backend is unreachable.
- Shadow DOM for CSS isolation from host page.

## 3. Backend (Self-hosted)

### 3.1 Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: SQLite (WAL mode)
- **LLM**: OpenAI API (gpt-4o-mini) — switchable to local Ollama in the future
- **Deployment**: Docker Compose

### 3.2 Data Model

#### words

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| text | TEXT | The word or phrase, trimmed |
| is_phrase | BOOLEAN | TRUE if multi-word |
| created_at | TIMESTAMP | Default: now |

- UNIQUE constraint on lowercased `text`.

#### answers

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| word_id | INTEGER FK | References words.id |
| translation | TEXT | Vietnamese translation |
| meaning | TEXT | English definition |
| example_1 | TEXT | Example sentence 1 |
| example_2 | TEXT | Example sentence 2 |
| example_3 | TEXT | Example sentence 3 |
| word_type | TEXT | noun/verb/adj/adv/etc. NULL for phrases |
| source | TEXT | "openai", "ollama", or "user" |
| score | INTEGER | Net votes (likes - dislikes), default 0 |
| created_at | TIMESTAMP | Default: now |

#### votes

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| answer_id | INTEGER FK | References answers.id |
| browser_id | TEXT | UUID from browser extension |
| value | INTEGER | +1 (like) or -1 (dislike) |
| created_at | TIMESTAMP | Default: now |

- UNIQUE constraint on `(answer_id, browser_id)`.

### 3.3 API Endpoints

Base path: `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/words` | Look up or create a word. If new, triggers LLM generation. Returns word + top-voted answer. |
| GET | `/words/{word_id}/answers` | List all answers for a word, sorted by score DESC. |
| POST | `/words/{word_id}/answers/{answer_id}/vote` | Cast, change, or remove a vote. |

#### POST /words

Request:
```json
{
  "text": "resilient",
  "browser_id": "uuid"
}
```

Response (200 if exists, 201 if created):
```json
{
  "word": { "id": 42, "text": "resilient", "is_phrase": false },
  "answer": {
    "id": 105,
    "translation": "kiên cường, bền bỉ",
    "meaning": "Able to recover quickly from difficulties; tough.",
    "examples": ["...", "...", "..."],
    "word_type": "adj",
    "score": 15,
    "user_vote": 1
  },
  "answer_count": 3
}
```

If the word is new and LLM generation fails, `answer` is `null` with `"status": "pending"`.

#### POST /words/{word_id}/answers/{answer_id}/vote

Request:
```json
{
  "browser_id": "uuid",
  "value": 1
}
```

`value`: 1 = like, -1 = dislike, 0 = remove vote.

### 3.4 LLM Integration

- **Provider pattern**: Abstract `LLMProvider` base class with `OpenAIProvider` (current) and `OllamaProvider` (future).
- Configured via `LLM_PROVIDER` env var (`openai` or `ollama`).
- Prompts the LLM to return structured JSON with: translation, meaning, 3 examples, word type.
- Timeout: 30 seconds.
- On failure: word is created but answer is not generated.

### 3.5 CORS

- Allow all origins (extension content scripts run on any webpage).
- Methods: GET, POST.
- Headers: Content-Type.

### 3.6 Authentication

- **None**. This is an open platform. No user accounts or login.
- Browser identity is tracked only by a locally-generated UUID for voting deduplication.

## 4. Deployment

- Single Docker Compose service for the backend.
- SQLite database persisted via Docker volume.
- Environment variables: `OPENAI_API_KEY`, `LLM_PROVIDER`, `OLLAMA_BASE_URL` (future).
- Chrome extension loaded as unpacked for development, publishable to Chrome Web Store later.

## 5. Seed Data

- A seed script pre-populates the database with the top 3,000 common English words.
- Runs against the backend API, rate-limited to respect LLM provider limits.

## 6. Non-Goals (for now)

- User accounts / authentication
- Multi-language support beyond English → Vietnamese
- Chrome Web Store publication (load unpacked for now)
- Mobile app
- Real-time collaboration features
