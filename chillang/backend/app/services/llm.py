import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a bilingual English-Vietnamese dictionary assistant. "
    "You respond ONLY with valid JSON, no other text. "
    "Your translations are natural, commonly-used Vietnamese equivalents (not literal). "
    "Your English definitions are clear and concise (one sentence). "
    "Your example sentences use the word in everyday, natural contexts."
)

WORD_PROMPT = """Generate a dictionary entry for the English word "{text}".
Respond with this exact JSON structure:
{{
  "translation": "<Vietnamese translation, 1-3 common equivalents separated by commas>",
  "meaning": "<concise English definition in one sentence>",
  "examples": [
    "<example sentence 1 using the word>",
    "<example sentence 2 using the word in a different context>",
    "<example sentence 3 using the word in yet another context>"
  ],
  "word_type": "<one of: noun, verb, adj, adv, prep, conj, pron, det, interj>"
}}"""

PHRASE_PROMPT = """Generate a translation entry for the English phrase "{text}".
Respond with this exact JSON structure:
{{
  "translation": "<natural Vietnamese translation>",
  "meaning": "<explanation of the phrase meaning in English, one sentence>",
  "examples": [
    "<example sentence 1 using the phrase>",
    "<example sentence 2 using the phrase in a different context>",
    "<example sentence 3 using the phrase in yet another context>"
  ]
}}"""


@dataclass
class WordEntry:
    translation: str
    meaning: str
    examples: list[str]
    word_type: str | None


class LLMProvider(ABC):
    @abstractmethod
    async def generate_word_entry(self, text: str, is_phrase: bool) -> WordEntry | None:
        ...


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate_word_entry(self, text: str, is_phrase: bool) -> WordEntry | None:
        prompt = PHRASE_PROMPT if is_phrase else WORD_PROMPT
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt.format(text=text)},
                ],
                response_format={"type": "json_object"},
                timeout=settings.llm_timeout,
            )
            data = json.loads(response.choices[0].message.content)
            return WordEntry(
                translation=data["translation"],
                meaning=data["meaning"],
                examples=data["examples"][:3],
                word_type=data.get("word_type") if not is_phrase else None,
            )
        except Exception:
            logger.exception("OpenAI generation failed for '%s'", text)
            return None


class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def generate_word_entry(self, text: str, is_phrase: bool) -> WordEntry | None:
        prompt = PHRASE_PROMPT if is_phrase else WORD_PROMPT
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": SYSTEM_PROMPT,
                        "prompt": prompt.format(text=text),
                        "format": "json",
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = json.loads(response.json()["response"])
                return WordEntry(
                    translation=data["translation"],
                    meaning=data["meaning"],
                    examples=data["examples"][:3],
                    word_type=data.get("word_type") if not is_phrase else None,
                )
        except Exception:
            logger.exception("Ollama generation failed for '%s'", text)
            return None


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    return OpenAIProvider()
