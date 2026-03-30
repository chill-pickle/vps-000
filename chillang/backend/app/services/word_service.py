from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Answer, Vote, Word
from app.services.llm import LLMProvider


async def find_word(db: AsyncSession, text: str) -> Word | None:
    text_lower = text.strip().lower()
    result = await db.execute(select(Word).where(Word.text_lower == text_lower))
    return result.scalar_one_or_none()


async def create_word(db: AsyncSession, text: str) -> Word:
    text = text.strip()
    is_phrase = " " in text
    word = Word(text=text, text_lower=text.lower(), is_phrase=is_phrase)
    db.add(word)
    await db.flush()
    return word


async def generate_and_save_answer(
    db: AsyncSession, word: Word, llm: LLMProvider
) -> Answer | None:
    entry = await llm.generate_word_entry(word.text, word.is_phrase)
    if entry is None:
        return None
    answer = Answer(
        word_id=word.id,
        translation=entry.translation,
        meaning=entry.meaning,
        example_1=entry.examples[0] if len(entry.examples) > 0 else "",
        example_2=entry.examples[1] if len(entry.examples) > 1 else "",
        example_3=entry.examples[2] if len(entry.examples) > 2 else "",
        word_type=entry.word_type,
        source="openai",
    )
    db.add(answer)
    await db.flush()
    return answer


async def get_top_answer(
    db: AsyncSession, word_id: int, browser_id: str | None = None
) -> tuple[Answer | None, int | None]:
    result = await db.execute(
        select(Answer)
        .where(Answer.word_id == word_id)
        .order_by(Answer.score.desc(), Answer.id.asc())
        .limit(1)
    )
    answer = result.scalar_one_or_none()
    user_vote = None
    if answer and browser_id:
        vote_result = await db.execute(
            select(Vote.value).where(
                Vote.answer_id == answer.id, Vote.browser_id == browser_id
            )
        )
        user_vote = vote_result.scalar_one_or_none()
    return answer, user_vote


async def get_answer_count(db: AsyncSession, word_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(Answer).where(Answer.word_id == word_id)
    )
    return result.scalar_one()


async def get_all_answers(
    db: AsyncSession, word_id: int, browser_id: str | None = None
) -> list[tuple[Answer, int | None]]:
    result = await db.execute(
        select(Answer)
        .where(Answer.word_id == word_id)
        .order_by(Answer.score.desc(), Answer.id.asc())
    )
    answers = result.scalars().all()
    items = []
    for answer in answers:
        user_vote = None
        if browser_id:
            vote_result = await db.execute(
                select(Vote.value).where(
                    Vote.answer_id == answer.id, Vote.browser_id == browser_id
                )
            )
            user_vote = vote_result.scalar_one_or_none()
        items.append((answer, user_vote))
    return items


async def cast_vote(
    db: AsyncSession, answer_id: int, browser_id: str, value: int
) -> tuple[int, int | None]:
    """Returns (new_score, user_vote)."""
    existing = await db.execute(
        select(Vote).where(Vote.answer_id == answer_id, Vote.browser_id == browser_id)
    )
    vote = existing.scalar_one_or_none()

    answer = await db.get(Answer, answer_id)

    if value == 0:
        # Remove vote
        if vote:
            answer.score -= vote.value
            await db.delete(vote)
        await db.flush()
        return answer.score, None

    if vote:
        # Change vote
        answer.score += value - vote.value
        vote.value = value
    else:
        # New vote
        vote = Vote(answer_id=answer_id, browser_id=browser_id, value=value)
        db.add(vote)
        answer.score += value

    await db.flush()
    return answer.score, value
