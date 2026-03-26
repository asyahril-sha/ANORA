# app/core/emotional_engine.py
"""
Emotional Engine – Jantung ANORA Ultimate
5 dimensi: sayang, rindu, trust, mood, arousal
"""

import time
import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionalStyle(str, Enum):
    COLD = "cold"
    CLINGY = "clingy"
    WARM = "warm"
    FLIRTY = "flirty"
    NEUTRAL = "neutral"


class EmotionalEngine:
    def __init__(self, user_id: int, initial_state: Dict = None):
        self.user_id = user_id
        if initial_state:
            self.sayang = initial_state.get('sayang', 50.0)
            self.rindu = initial_state.get('rindu', 0.0)
            self.trust = initial_state.get('trust', 50.0)
            self.mood = initial_state.get('mood', 0.0)
            self.arousal = initial_state.get('arousal', 0.0)
            self.last_interaction = initial_state.get('last_interaction', time.time())
        else:
            self.sayang = 50.0
            self.rindu = 0.0
            self.trust = 50.0
            self.mood = 0.0
            self.arousal = 0.0
            self.last_interaction = time.time()
        self.last_update = time.time()

    def update(self, force: bool = False) -> None:
        now = time.time()
        elapsed_hours = (now - self.last_update) / 3600
        if elapsed_hours <= 0 and not force:
            return

        # Rindu growth
        hours_inactive = (now - self.last_interaction) / 3600
        if hours_inactive > 1:
            gain = 5.0 * hours_inactive
            self.rindu = min(100, self.rindu + gain)
            logger.debug(f"Rindu +{gain:.1f} (inactive {hours_inactive:.1f}h)")

        # Mood decay towards 0
        if self.mood > 0:
            decay = 2.0 * elapsed_hours
            self.mood = max(-50, self.mood - decay)
        elif self.mood < 0:
            decay = 1.0 * elapsed_hours
            self.mood = min(0, self.mood + decay)

        # Arousal decay
        if self.arousal > 0:
            decay = 5.0 * elapsed_hours
            self.arousal = max(0, self.arousal - decay)

        self.last_update = now

    def update_from_message(self, text: str, level: int) -> Dict[str, float]:
        self.update()
        now = time.time()
        self.last_interaction = now
        msg = text.lower()
        changes = {}

        # Positive triggers
        if any(k in msg for k in ['sayang', 'cinta', 'love']):
            self.sayang = min(100, self.sayang + 8)
            self.mood = min(50, self.mood + 10)
            self.trust = min(100, self.trust + 5)
            changes.update({'sayang': 8, 'mood': 10, 'trust': 5})

        if any(k in msg for k in ['kangen', 'rindu']):
            self.sayang = min(100, self.sayang + 5)
            self.rindu = max(0, self.rindu - 15)
            self.mood = min(50, self.mood + 8)
            changes.update({'sayang': 5, 'rindu': -15, 'mood': 8})

        if any(k in msg for k in ['cantik', 'ganteng', 'seksi']):
            self.mood = min(50, self.mood + 12)
            if level >= 7:
                self.arousal = min(100, self.arousal + 5)
                changes['arousal'] = 5
            changes['mood'] = 12

        # Physical touch
        if any(k in msg for k in ['pegang', 'sentuh', 'raba']):
            gain = 12
            if level >= 11:
                gain = 18
            self.arousal = min(100, self.arousal + gain)
            changes['arousal'] = gain

        if any(k in msg for k in ['cium', 'kiss']):
            gain = 20
            if level >= 11:
                gain = 30
            self.arousal = min(100, self.arousal + gain)
            changes['arousal'] = gain

        if any(k in msg for k in ['peluk', 'rangkul']):
            gain = 8
            self.arousal = min(100, self.arousal + gain)
            self.mood = min(50, self.mood + 5)
            changes.update({'arousal': gain, 'mood': 5})

        # Negative triggers (mood only, conflict handled separately)
        if any(k in msg for k in ['cewek', 'perempuan']) and any(k in msg for k in ['cerita', 'ketemu', 'bareng']):
            self.mood = max(-50, self.mood - 10)
            changes['mood'] = -10

        self._clamp()
        return changes

    def _clamp(self):
        self.sayang = max(0, min(100, self.sayang))
        self.rindu = max(0, min(100, self.rindu))
        self.trust = max(0, min(100, self.trust))
        self.mood = max(-50, min(50, self.mood))
        self.arousal = max(0, min(100, self.arousal))

    def get_style(self) -> EmotionalStyle:
        self.update()
        if self.mood <= -20:
            return EmotionalStyle.COLD
        if self.rindu >= 70:
            return EmotionalStyle.CLINGY
        if self.arousal >= 70:
            return EmotionalStyle.FLIRTY
        if self.trust >= 70 and self.mood > 10:
            return EmotionalStyle.WARM
        return EmotionalStyle.NEUTRAL

    def get_state_dict(self) -> Dict:
        return {
            'sayang': self.sayang,
            'rindu': self.rindu,
            'trust': self.trust,
            'mood': self.mood,
            'arousal': self.arousal,
            'last_interaction': self.last_interaction,
        }

    def load_from_dict(self, data: Dict):
        self.sayang = data.get('sayang', 50)
        self.rindu = data.get('rindu', 0)
        self.trust = data.get('trust', 50)
        self.mood = data.get('mood', 0)
        self.arousal = data.get('arousal', 0)
        self.last_interaction = data.get('last_interaction', time.time())
