from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Answer
from app.schemas import (
    AnswerListResponse,
    AnswerResponse,
    VoteRequest,
    VoteResponse,
    WordLookupRequest,
    WordLookupResponse,
    WordResponse,
)
from app.services.llm import get_llm_provider
from app.services.word_service import (
    cast_vote,
    create_word,
    find_word,
    generate_and_save_answer,
    get_all_answers,
    get_answer_count,
    get_top_answer,
)

router = APIRouter(prefix="/api/v1", tags=["words"])


def _answer_response(answer: Answer, user_vote: int | None) -> AnswerResponse:
    return AnswerResponse(
        id=answer.id,
        translation=answer.translation,
        meaning=answer.meaning,
        examples=[answer.example_1, answer.example_2, answer.example_3],
        word_type=answer.word_type,
        score=answer.score,
        source=answer.source,
        user_vote=user_vote,
    )


def _word_response(word) -> WordResponse:
    return WordResponse(id=word.id, text=word.text, is_phrase=word.is_phrase)


@router.post("/words", response_model=WordLookupResponse, status_code=200)
async def lookup_or_create_word(
    req: WordLookupRequest,
    db: AsyncSession = Depends(get_db),
):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    word = await find_word(db, text)
    created = False
    if word is None:
        word = await create_word(db, text)
        created = True

    answer, user_vote = await get_top_answer(db, word.id, req.browser_id)

    if answer is None and created:
        llm = get_llm_provider()
        answer = await generate_and_save_answer(db, word, llm)
        user_vote = None

    await db.commit()

    count = await get_answer_count(db, word.id)
    return WordLookupResponse(
        word=_word_response(word),
        answer=_answer_response(answer, user_vote) if answer else None,
        answer_count=count,
        status="ok" if answer else "pending",
    )


@router.get(
    "/words/{word_id}/answers", response_model=AnswerListResponse, status_code=200
)
async def list_answers(
    word_id: int,
    browser_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    from app.models import Word

    word = await db.get(Word, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    items = await get_all_answers(db, word_id, browser_id)
    return AnswerListResponse(
        word=_word_response(word),
        answers=[_answer_response(a, v) for a, v in items],
    )


@router.post(
    "/words/{word_id}/answers/{answer_id}/vote",
    response_model=VoteResponse,
    status_code=200,
)
async def vote_on_answer(
    word_id: int,
    answer_id: int,
    req: VoteRequest,
    db: AsyncSession = Depends(get_db),
):
    if req.value not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="Value must be -1, 0, or 1")

    answer = await db.get(Answer, answer_id)
    if answer is None or answer.word_id != word_id:
        raise HTTPException(status_code=404, detail="Answer not found")

    new_score, user_vote = await cast_vote(db, answer_id, req.browser_id, req.value)
    await db.commit()

    return VoteResponse(answer_id=answer_id, new_score=new_score, user_vote=user_vote)
