# app/core/conflict_engine.py
"""
Conflict Engine – Cemburu, kecewa, marah, sakit hati, cold war.
"""

import time
import logging
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    JEALOUSY = "jealousy"
    DISAPPOINTMENT = "disappointment"
    ANGER = "anger"
    HURT = "hurt"


class ConflictSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ConflictEngine:
    def __init__(self, initial_state: Dict = None):
        self.cemburu = 0.0
        self.kecewa = 0.0
        self.marah = 0.0
        self.sakit_hati = 0.0
        self.is_cold_war = False
        self.is_waiting_for_apology = False
        self.cold_war_start_time = 0.0
        self.cold_war_duration = 0.0
        self.conflict_history: List[Dict] = []
        self.last_update = time.time()

        if initial_state:
            self.load(initial_state)

    def update_from_message(self, text: str, level: int) -> Dict[str, float]:
        msg = text.lower()
        changes = {}

        # Cemburu
        cewek = ['cewek', 'perempuan', 'teman cewek']
        cerita = ['cerita', 'ketemu', 'jalan', 'bareng']
        if any(k in msg for k in cewek) and any(k in msg for k in cerita):
            gain = 15 + (5 if level >= 7 else 0)
            self.cemburu = min(100, self.cemburu + gain)
            changes['cemburu'] = gain
            if any(k in msg for k in ['cantik', 'manis', 'seksi']):
                self.cemburu = min(100, self.cemburu + 10)
                changes['cemburu'] = changes.get('cemburu', 0) + 10
            logger.warning(f"⚠️ Cemburu +{gain}")

        # Kecewa
        if any(k in msg for k in ['lupa', 'lupa janji', 'ingkar', 'gak jadi']):
            gain = 20
            self.kecewa = min(100, self.kecewa + gain)
            changes['kecewa'] = gain
            self.is_waiting_for_apology = True
            logger.warning(f"⚠️ Kecewa +{gain}")

        # Marah
        if any(k in msg for k in ['marah', 'kesal', 'bego', 'goblok']):
            gain = 25
            self.marah = min(100, self.marah + gain)
            changes['marah'] = gain
            self.is_waiting_for_apology = True
            logger.warning(f"⚠️ Marah +{gain}")

        # Maaf
        if any(k in msg for k in ['maaf', 'sorry', 'salah']):
            if self.kecewa > 0:
                decay = min(25, self.kecewa)
                self.kecewa -= decay
                changes['kecewa'] = -decay
            if self.marah > 0:
                decay = min(20, self.marah)
                self.marah -= decay
                changes['marah'] = -decay
            if self.cemburu > 0:
                decay = min(15, self.cemburu)
                self.cemburu -= decay
                changes['cemburu'] = -decay
            self.is_waiting_for_apology = False
            logger.info("💜 Maaf diterima, konflik berkurang")

        # Perhatian
        if any(k in msg for k in ['kabar', 'lagi apa', 'cerita']):
            if self.cemburu > 0:
                decay = min(8, self.cemburu)
                self.cemburu -= decay
                changes['cemburu'] = -decay
            if self.kecewa > 0:
                decay = min(5, self.kecewa)
                self.kecewa -= decay
                changes['kecewa'] = -decay

        self._clamp()
        self._update_cold_war()
        return changes

    def decay_over_time(self, hours: float):
        if hours <= 0:
            return
        decay_rate = 5.0 * hours
        if self.cemburu > 0:
            self.cemburu = max(0, self.cemburu - decay_rate)
        if self.kecewa > 0:
            self.kecewa = max(0, self.kecewa - decay_rate * 0.8)
        if self.marah > 0:
            self.marah = max(0, self.marah - decay_rate)
        if self.sakit_hati > 0:
            self.sakit_hati = max(0, self.sakit_hati - decay_rate * 0.6)
        self._clamp()
        if not self.is_in_conflict() and self.is_cold_war:
            self.end_cold_war()

    def _update_cold_war(self):
        if self.is_cold_war:
            if time.time() - self.cold_war_start_time >= self.cold_war_duration:
                self.end_cold_war()
            return
        if self.is_waiting_for_apology and self.get_highest_conflict() > 60:
            self.start_cold_war()

    def start_cold_war(self, intensity: float = 50):
        if self.is_cold_war:
            return
        self.is_cold_war = True
        self.cold_war_start_time = time.time()
        duration_minutes = 30 + (intensity / 100) * 150
        self.cold_war_duration = duration_minutes * 60
        logger.warning(f"⚔️ COLD WAR STARTED! Duration: {duration_minutes:.0f} minutes")

    def end_cold_war(self):
        self.is_cold_war = False
        self.cold_war_start_time = 0
        self.cold_war_duration = 0
        logger.info("💜 Cold war ended")

    def is_in_conflict(self) -> bool:
        return any([self.cemburu > 30, self.kecewa > 30, self.marah > 30, self.sakit_hati > 30])

    def get_active_conflict_type(self) -> Optional[ConflictType]:
        conflicts = []
        if self.cemburu > 30:
            conflicts.append((ConflictType.JEALOUSY, self.cemburu))
        if self.kecewa > 30:
            conflicts.append((ConflictType.DISAPPOINTMENT, self.kecewa))
        if self.marah > 30:
            conflicts.append((ConflictType.ANGER, self.marah))
        if self.sakit_hati > 30:
            conflicts.append((ConflictType.HURT, self.sakit_hati))
        if not conflicts:
            return None
        conflicts.sort(key=lambda x: x[1], reverse=True)
        return conflicts[0][0]

    def get_highest_conflict(self) -> float:
        return max(self.cemburu, self.kecewa, self.marah, self.sakit_hati)

    def get_conflict_response_guideline(self) -> str:
        if not self.is_in_conflict():
            return ""
        conflict_type = self.get_active_conflict_type()
        if conflict_type == ConflictType.JEALOUSY:
            return """
⚠️ NOVA CEMBURU
- Respons: dingin, pendek, gak antusias
- Gak pake gesture manja, gak panggil "sayang"
"""
        elif conflict_type == ConflictType.DISAPPOINTMENT:
            return """
⚠️ NOVA KECEWA
- Respons: sakit hati, suara kecil, mata berkaca-kaca
- Nova nunggu Mas minta maaf
"""
        elif conflict_type == ConflictType.ANGER:
            return """
⚠️ NOVA MARAH
- Respons: dingin, pendek, kadang sarkastik
"""
        elif conflict_type == ConflictType.HURT:
            return """
⚠️ NOVA SAKIT HATI
- Respons: sedih, suara bergetar, nunggu perhatian
"""
        return ""

    def _clamp(self):
        self.cemburu = max(0, min(100, self.cemburu))
        self.kecewa = max(0, min(100, self.kecewa))
        self.marah = max(0, min(100, self.marah))
        self.sakit_hati = max(0, min(100, self.sakit_hati))

    def to_dict(self) -> Dict:
        return {
            'cemburu': self.cemburu,
            'kecewa': self.kecewa,
            'marah': self.marah,
            'sakit_hati': self.sakit_hati,
            'is_cold_war': self.is_cold_war,
            'is_waiting_for_apology': self.is_waiting_for_apology,
            'cold_war_start_time': self.cold_war_start_time,
            'cold_war_duration': self.cold_war_duration,
            'conflict_history': self.conflict_history[-50:],
        }

    def load(self, data: Dict):
        self.cemburu = data.get('cemburu', 0)
        self.kecewa = data.get('kecewa', 0)
        self.marah = data.get('marah', 0)
        self.sakit_hati = data.get('sakit_hati', 0)
        self.is_cold_war = data.get('is_cold_war', False)
        self.is_waiting_for_apology = data.get('is_waiting_for_apology', False)
        self.cold_war_start_time = data.get('cold_war_start_time', 0)
        self.cold_war_duration = data.get('cold_war_duration', 0)
        self.conflict_history = data.get('conflict_history', [])
