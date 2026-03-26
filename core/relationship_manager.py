# app/core/relationship_manager.py
"""
Relationship Manager – 5 fase hubungan: stranger, friend, close, romantic, intimate
Level 1-12 dengan threshold dari config.
"""

import time
import logging
from enum import Enum
from typing import Dict, Optional, Tuple, List

from ..config import settings

logger = logging.getLogger(__name__)


class RelationshipPhase(str, Enum):
    STRANGER = "stranger"
    FRIEND = "friend"
    CLOSE = "close"
    ROMANTIC = "romantic"
    INTIMATE = "intimate"


class RelationshipManager:
    def __init__(self, initial_state: Dict = None):
        if initial_state:
            self.phase = RelationshipPhase(initial_state.get('phase', 'stranger'))
            self.level = initial_state.get('level', 1)
            self.interaction_count = initial_state.get('interaction_count', 0)
            self.milestones = initial_state.get('milestones', {
                'first_chat': False,
                'first_flirt': False,
                'first_touch': False,
                'first_hug': False,
                'first_kiss': False,
                'first_intim': False,
            })
        else:
            self.phase = RelationshipPhase.STRANGER
            self.level = 1
            self.interaction_count = 0
            self.milestones = {
                'first_chat': False,
                'first_flirt': False,
                'first_touch': False,
                'first_hug': False,
                'first_kiss': False,
                'first_intim': False,
            }
        self.created_at = time.time()
        self.last_update = time.time()

    def update_level(self, emotional_state: Dict, trigger: str = "") -> Tuple[int, bool]:
        old_level = self.level
        self.interaction_count += 1

        targets = settings.level.level_targets
        new_level = 1
        for lvl, target in sorted(targets.items()):
            if self.interaction_count >= target:
                new_level = lvl
            else:
                break

        sayang = emotional_state.get('sayang', 50)
        trust = emotional_state.get('trust', 50)
        bonus = 0
        if sayang > 70:
            bonus += 1
        if trust > 70:
            bonus += 1
        milestone_count = sum(1 for v in self.milestones.values() if v)
        bonus += min(1, milestone_count // 2)

        new_level = min(12, new_level + bonus)
        new_level = max(1, new_level)

        self.level = new_level
        self._update_phase()
        self.last_update = time.time()

        level_up = new_level > old_level
        if level_up:
            logger.info(f"📈 Level up: {old_level} → {new_level} (phase: {self.phase.value})")
        return new_level, level_up

    def _update_phase(self):
        if self.level <= 3:
            self.phase = RelationshipPhase.STRANGER
        elif self.level <= 6:
            self.phase = RelationshipPhase.FRIEND
        elif self.level <= 8:
            self.phase = RelationshipPhase.CLOSE
        elif self.level <= 10:
            self.phase = RelationshipPhase.ROMANTIC
        else:
            self.phase = RelationshipPhase.INTIMATE

    def achieve_milestone(self, milestone_name: str) -> bool:
        if milestone_name in self.milestones and not self.milestones[milestone_name]:
            self.milestones[milestone_name] = True
            logger.info(f"🏆 Milestone achieved: {milestone_name}")
            return True
        return False

    def can_do_action(self, action: str) -> Tuple[bool, str]:
        if action == "flirt":
            allowed = self.level >= 2
            reason = "Nova masih malu untuk flirt." if not allowed else ""
        elif action == "touch":
            allowed = self.level >= 4
            reason = "Nova belum siap disentuh." if not allowed else ""
        elif action == "hug":
            allowed = self.level >= 5
            reason = "Nova masih malu dipeluk." if not allowed else ""
        elif action == "kiss":
            allowed = self.level >= 7
            reason = "Nova belum siap ciuman." if not allowed else ""
        elif action == "vulgar_light":
            allowed = self.level >= 7
            reason = "Nova masih malu ngomong vulgar." if not allowed else ""
        elif action == "vulgar_full":
            allowed = self.level >= 11
            reason = "Belum waktunya vulgar." if not allowed else ""
        elif action == "intim":
            allowed = self.level >= 11
            reason = "Nova belum siap intim." if not allowed else ""
        else:
            allowed = True
            reason = ""
        return allowed, reason

    def get_unlock_summary(self) -> str:
        unlocked = []
        if self.can_do_action("flirt")[0]:
            unlocked.append("flirt")
        if self.can_do_action("touch")[0]:
            unlocked.append("sentuhan")
        if self.can_do_action("hug")[0]:
            unlocked.append("peluk")
        if self.can_do_action("kiss")[0]:
            unlocked.append("cium")
        if self.can_do_action("vulgar_light")[0]:
            unlocked.append("vulgar ringan")
        if self.can_do_action("vulgar_full")[0]:
            unlocked.append("vulgar bebas")
        if self.can_do_action("intim")[0]:
            unlocked.append("intim")
        return f"Unlocked: {', '.join(unlocked) if unlocked else 'belum ada'}"

    def get_state_dict(self) -> Dict:
        return {
            'phase': self.phase.value,
            'level': self.level,
            'interaction_count': self.interaction_count,
            'milestones': self.milestones,
            'created_at': self.created_at,
            'last_update': self.last_update,
        }

    def load_from_dict(self, data: Dict):
        self.phase = RelationshipPhase(data.get('phase', 'stranger'))
        self.level = data.get('level', 1)
        self.interaction_count = data.get('interaction_count', 0)
        self.milestones.update(data.get('milestones', {}))
        self.created_at = data.get('created_at', time.time())
        self.last_update = data.get('last_update', time.time())
