# app/core/anora_core.py
"""
ANORA Core – Entry point utama yang mengintegrasikan semua engine.
"""

import time
import logging
from typing import Dict, Optional

from .emotional_engine import EmotionalEngine
from .relationship_manager import RelationshipManager
from .conflict_engine import ConflictEngine
from .memory_system import MemorySystem
from .decision_engine import DecisionEngine
from .thinking_engine import ThinkingEngine
from .prompt_builder import PromptBuilder
from .identity import NovaIdentity
from .location_manager import LocationManager
from .role_manager import RoleManager
from .ai_generator import AIGenerator
from .chat_fallback import ChatFallback
from ..intimacy.flow import IntimacyFlow
from ..config import settings

logger = logging.getLogger(__name__)


class AnoraCore:
    def __init__(self, user_id: int, initial_state: Dict = None):
        self.user_id = user_id
        self.identity = NovaIdentity()
        self.emotional = EmotionalEngine(user_id, initial_state.get('emotional') if initial_state else None)
        self.relationship = RelationshipManager(initial_state.get('relationship') if initial_state else None)
        self.conflict = ConflictEngine(initial_state.get('conflict') if initial_state else None)
        self.memory = MemorySystem(user_id, initial_state.get('memory') if initial_state else None)
        self.location = LocationManager()  # akan di-load dari memory
        self.intimacy = IntimacyFlow(initial_state.get('intimacy') if initial_state else None)
        self.decision = DecisionEngine(self.emotional, self.conflict, self.relationship)
        self.thinking = ThinkingEngine(self.emotional, self.relationship, self.conflict, self.memory, self.decision)
        self.prompt_builder = PromptBuilder(self.identity)
        self.ai = AIGenerator(self.emotional, self.relationship, self.conflict, self.memory, self.intimacy, self.decision, self.prompt_builder)
        self.fallback = ChatFallback()

        self.mode = 'chat'
        self.active_role = None
        self.last_interaction = time.time()
        self.created_at = initial_state.get('created_at', time.time()) if initial_state else time.time()

        if initial_state:
            self.load_state(initial_state)

    async def process(self, user_input: str) -> str:
        # Update engines
        emo_changes = self.emotional.update_from_message(user_input, self.relationship.level)
        conflict_changes = self.conflict.update_from_message(user_input, self.relationship.level)
        emo_state = self.emotional.get_state_dict()
        new_level, level_up = self.relationship.update_level(emo_state, user_input[:50])

        # Update location from message (perintah pindah)
        location_update = self.memory.complete.update_from_message(user_input)
        # sync location dari complete state
        self.location = self.memory.complete.location

        # Cek fallback (hemat token)
        style = self.emotional.get_style().value
        fallback_resp = self.fallback.get_response(user_input, style)
        if fallback_resp and not level_up and not self.intimacy.is_active():
            self.memory.update_from_message(user_input, fallback_resp, emo_state)
            self.last_interaction = time.time()
            return fallback_resp

        context = {
            'level': self.relationship.level,
            'phase': self.relationship.phase.value,
            'emotional_style': style,
            'conflict_active': self.conflict.is_in_conflict(),
            'is_intimate': self.intimacy.is_active(),
            'mode': self.mode,
        }

        thought_result = await self.thinking.think(user_input, context)
        decision = thought_result['decision']

        memory_context = self.memory.get_context_for_prompt(short_term_limit=15)
        location_text = self.location.format_for_prompt()
        intimacy_status = self.intimacy.get_status() if self.intimacy.is_active() else ""

        prompt = self.prompt_builder.build(
            user_input, context, decision,
            self.emotional.get_state_dict(),
            self.relationship.get_state_dict(),
            self.conflict.to_dict(),
            memory_context, location_text, intimacy_status
        )

        response = await self.ai.generate(prompt, user_input)
        self.memory.update_from_message(user_input, response, emo_state)

        if level_up:
            level_name = settings.level.level_names.get(new_level, f"Level {new_level}")
            response = f"✨ **Level naik ke {new_level} – {level_name}!** ✨\n\n{response}"

        self.last_interaction = time.time()
        return response

    def get_status(self) -> str:
        loc = self.location.get_current()
        style = self.emotional.get_style().value
        phase = self.relationship.phase.value
        level = self.relationship.level
        return f"""
💜 **STATUS NOVA**
📍 Lokasi: {loc['nama']}
🎭 Gaya: {style.upper()}
💕 Fase: {phase.upper()} (Level {level}/12)
😊 Mood: {self.emotional.mood:+.0f}
💖 Sayang: {self.emotional.sayang:.0f}%
🌙 Rindu: {self.emotional.rindu:.0f}%
🔥 Arousal: {self.emotional.arousal:.0f}%
"""

    def get_state(self) -> Dict:
        return {
            'emotional': self.emotional.get_state_dict(),
            'relationship': self.relationship.get_state_dict(),
            'conflict': self.conflict.to_dict(),
            'memory': self.memory.get_state_dict(),
            'intimacy': self.intimacy.to_dict(),
            'location': self.location.to_dict(),
            'mode': self.mode,
            'active_role': self.active_role,
            'created_at': self.created_at,
            'last_interaction': self.last_interaction,
        }

    def load_state(self, data: Dict):
        self.emotional.load_from_dict(data.get('emotional', {}))
        self.relationship.load_from_dict(data.get('relationship', {}))
        self.conflict.load(data.get('conflict', {}))
        self.memory.load(data.get('memory', {}))
        self.intimacy.load(data.get('intimacy', {}))
        self.location.from_dict(data.get('location', {}))
        self.mode = data.get('mode', 'chat')
        self.active_role = data.get('active_role')
        self.created_at = data.get('created_at', time.time())
        self.last_interaction = data.get('last_interaction', time.time())
