"""Seed the ChilLang database with common English words."""

import asyncio
import sys
import time

import httpx

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api/v1"
DELAY = 1.0  # seconds between requests (rate limit)

# Top 100 common English words to seed (expand as needed)
WORDS = [
    "abandon", "ability", "able", "about", "above", "abroad", "absence", "absolute",
    "absorb", "abstract", "abuse", "academic", "accept", "access", "accident",
    "accomplish", "according", "account", "accurate", "achieve", "acknowledge",
    "acquire", "across", "action", "active", "actual", "adapt", "addition",
    "address", "adequate", "adjust", "administration", "admire", "admit", "adopt",
    "adult", "advance", "advantage", "adventure", "advice", "affair", "affect",
    "afford", "afraid", "afternoon", "again", "against", "age", "agency", "agent",
    "aggressive", "agree", "agreement", "ahead", "aid", "aim", "air", "aircraft",
    "alive", "allow", "almost", "alone", "along", "already", "also", "alternative",
    "although", "always", "amazing", "ambition", "among", "amount", "analysis",
    "ancient", "anger", "angle", "angry", "animal", "announce", "annual", "anxiety",
    "anxious", "anybody", "anymore", "anything", "anyway", "anywhere", "apart",
    "apartment", "apparent", "appeal", "appear", "apple", "application", "apply",
    "appointment", "approach", "appropriate", "approve", "argue", "argument",
    "arise", "arrange", "arrive", "article", "artist",
]


async def seed():
    async with httpx.AsyncClient(timeout=60) as client:
        total = len(WORDS)
        for i, word in enumerate(WORDS, 1):
            try:
                res = await client.post(
                    f"{API_URL}/words",
                    json={"text": word},
                )
                status = "created" if res.status_code == 201 else "exists"
                data = res.json()
                has_answer = data.get("answer") is not None
                print(f"[{i}/{total}] {word}: {status}, answer={'yes' if has_answer else 'pending'}")
            except Exception as e:
                print(f"[{i}/{total}] {word}: ERROR - {e}")

            if i < total:
                await asyncio.sleep(DELAY)

    print(f"\nDone! Seeded {total} words.")


if __name__ == "__main__":
    asyncio.run(seed())
