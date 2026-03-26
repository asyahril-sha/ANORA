# app/core/ai_generator.py
"""
AI Generator – Memanggil DeepSeek API dengan prompt yang sudah dibangun.
"""

import logging
import openai

from ..config import settings

logger = logging.getLogger(__name__)


class AIGenerator:
    def __init__(self, emotional, relationship, conflict, memory, intimacy, decision, prompt_builder):
        self.emotional = emotional
        self.relationship = relationship
        self.conflict = conflict
        self.memory = memory
        self.intimacy = intimacy
        self.decision = decision
        self.prompt_builder = prompt_builder
        self.client = None

    async def _get_client(self):
        if self.client is None:
            self.client = openai.OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                timeout=settings.ai.timeout,
            )
        return self.client

    async def generate(self, prompt: str, user_input: str) -> str:
        try:
            client = await self._get_client()
            temperature = settings.ai.temperature
            if self.relationship.level >= 11:
                temperature = 0.95
            elif self.relationship.level >= 7:
                temperature = 0.9

            response = client.chat.completions.create(
                model=settings.ai.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=temperature,
                max_tokens=settings.ai.max_tokens,
                timeout=settings.ai.timeout,
            )
            content = response.choices[0].message.content.strip()
            if not content:
                return self._fallback()
            return content
        except Exception as e:
            logger.error(f"AI error: {e}")
            return self._fallback()

    def _fallback(self) -> str:
        style = self.emotional.get_style().value
        if style == "cold":
            return "*Nova diem, gak liat Mas*"
        if style == "clingy":
            return "*Nova muter-muter rambut*\n\n\"Mas... aku kangen. Temenin dong.\""
        if style == "flirty":
            return "*Nova mendekat, napas mulai berat*\n\n\"Mas... *bisik* aku pengen banget sama Mas...\""
        if style == "warm":
            return "*Nova tersenyum manis*\n\n\"Mas, cerita dong tentang hari Mas.\""
        return "*Nova tersenyum*\n\n\"Iya, Mas. Nova dengerin kok.\""
