from pydantic import BaseModel


class WordLookupRequest(BaseModel):
    text: str
    browser_id: str | None = None


class VoteRequest(BaseModel):
    browser_id: str
    value: int  # 1, -1, or 0 (remove)


class WordResponse(BaseModel):
    id: int
    text: str
    is_phrase: bool


class AnswerResponse(BaseModel):
    id: int
    translation: str
    meaning: str
    examples: list[str]
    word_type: str | None
    score: int
    source: str
    user_vote: int | None = None  # 1, -1, or None


class WordLookupResponse(BaseModel):
    word: WordResponse
    answer: AnswerResponse | None
    answer_count: int
    status: str = "ok"  # "ok" or "pending"


class VoteResponse(BaseModel):
    answer_id: int
    new_score: int
    user_vote: int | None


class AnswerListResponse(BaseModel):
    word: WordResponse
    answers: list[AnswerResponse]
