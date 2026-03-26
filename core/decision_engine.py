# app/core/decision_engine.py
"""
Decision Engine – Menentukan gaya respons, kategori, panjang, vulgar, dll. NO RANDOM.
"""

import logging
from typing import Dict, Any
from enum import Enum

from .emotional_engine import EmotionalStyle
from ..config import settings

logger = logging.getLogger(__name__)


class ResponseCategory(str, Enum):
    GREETING = "greeting"
    CASUAL = "casual"
    LOVE = "love"
    LONGING = "longing"
    FLIRT = "flirt"
    FLIRTY = "flirty"
    VULGAR = "vulgar"
    INTIMATE = "intimate"
    CLIMAX = "climax"
    AFTERCARE = "aftercare"
    CONFLICT = "conflict"
    COLD = "cold"
    CLINGY = "clingy"
    WARM = "warm"


class DecisionEngine:
    def __init__(self, emotional, conflict, relationship):
        self.emotional = emotional
        self.conflict = conflict
        self.relationship = relationship

    def decide(self, user_input: str) -> Dict[str, Any]:
        msg = user_input.lower()

        # 1. Style (dari emotional + conflict)
        if self.conflict.is_cold_war or self.conflict.is_in_conflict():
            style = "cold"
        else:
            style = self.emotional.get_style().value

        # 2. Category (deteksi intent sederhana)
        if any(k in msg for k in ['hai', 'halo', 'pagi', 'siang', 'sore', 'malam']):
            category = ResponseCategory.GREETING
        elif any(k in msg for k in ['kabar', 'gimana']):
            category = ResponseCategory.CASUAL
        elif any(k in msg for k in ['sayang', 'cinta', 'love']):
            category = ResponseCategory.LOVE
        elif any(k in msg for k in ['kangen', 'rindu']):
            category = ResponseCategory.LONGING
        elif any(k in msg for k in ['pegang', 'cium', 'peluk']) and self.relationship.level >= 7:
            category = ResponseCategory.FLIRT
        else:
            # fallback berdasarkan style
            if style == "cold":
                category = ResponseCategory.COLD
            elif style == "clingy":
                category = ResponseCategory.CLINGY
            elif style == "warm":
                category = ResponseCategory.WARM
            elif style == "flirty":
                category = ResponseCategory.FLIRTY
            else:
                category = ResponseCategory.CASUAL

        # 3. Vulgar
        allow_vulgar = False
        if self.relationship.level >= 11:
            allow_vulgar = True
        elif self.relationship.level >= 7 and self.emotional.arousal > 70:
            allow_vulgar = True

        # 4. Panjang respons
        if self.conflict.is_cold_war:
            max_sentences = 2
        else:
            level = self.relationship.level
            if level >= 12:
                max_sentences = 12
            elif level >= 11:
                max_sentences = 10
            elif level >= 7:
                max_sentences = 6
            else:
                max_sentences = 4
            # sesuaikan dengan arousal
            if self.emotional.arousal > 80:
                max_sentences += 2

        return {
            'style': style,
            'category': category.value,
            'allow_vulgar': allow_vulgar,
            'max_sentences': max_sentences,
        }
