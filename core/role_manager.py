# app/core/role_manager.py
"""
Role Manager – Mengelola role lain (IPAR, Teman Kantor, Pelakor, Istri Orang)
Setiap role memiliki engine sendiri (emosi, hubungan, konflik, memory, intimacy, AI)
"""

import logging
from typing import Dict, List, Optional

from .emotional_engine import EmotionalEngine
from .relationship_manager import RelationshipManager
from .conflict_engine import ConflictEngine
from .memory_system import MemorySystem
from .decision_engine import DecisionEngine
from .ai_generator import AIGenerator
from .prompt_builder import PromptBuilder
from .identity import NovaIdentity
from ..intimacy.flow import IntimacyFlow

logger = logging.getLogger(__name__)


class BaseRole:
    def __init__(self, user_id: int, role_id: str, name: str, panggilan: str, hubungan_dengan_nova: str):
        self.user_id = user_id
        self.role_id = role_id
        self.name = name
        self.panggilan = panggilan
        self.hubungan_dengan_nova = hubungan_dengan_nova

        self.emotional = EmotionalEngine(user_id)
        self.relationship = RelationshipManager()
        self.conflict = ConflictEngine()
        self.memory = MemorySystem(user_id)
        self.intimacy = IntimacyFlow()
        self.decision = DecisionEngine(self.emotional, self.conflict, self.relationship)
        self.identity = NovaIdentity()
        self.prompt_builder = PromptBuilder(self.identity)
        self.ai = AIGenerator(self.emotional, self.relationship, self.conflict, self.memory, self.intimacy, self.decision, self.prompt_builder)

        self.special_flags = {}

    async def process(self, user_input: str) -> str:
        # Update engines
        emo_changes = self.emotional.update_from_message(user_input, self.relationship.level)
        conflict_changes = self.conflict.update_from_message(user_input, self.relationship.level)
        emo_state = self.emotional.get_state_dict()
        new_level, level_up = self.relationship.update_level(emo_state, user_input[:50])

        context = {
            'level': self.relationship.level,
            'phase': self.relationship.phase.value,
            'emotional_style': self.emotional.get_style().value,
            'conflict_active': self.conflict.is_in_conflict(),
            'is_intimate': self.intimacy.is_active(),
            'is_role': True,
            'role_name': self.name,
            'role_panggilan': self.panggilan,
            'role_hubungan': self.hubungan_dengan_nova,
        }

        if self.intimacy.is_active():
            self.intimacy.update_from_message(user_input, self.relationship.level)

        decision = self.decision.decide(user_input)
        memory_context = self.memory.get_context_for_prompt(short_term_limit=15)
        location_text = self.memory.complete.location.format_for_prompt() if hasattr(self.memory.complete, 'location') else ""
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
            level_name = {1: "Malu-malu", 2: "Mulai terbuka", 3: "Goda-godaan",
                          4: "Dekat", 5: "Sayang", 6: "PACAR/PDKT",
                          7: "Nyaman", 8: "Eksplorasi", 9: "Bergairah",
                          10: "Passionate", 11: "Soul Bounded", 12: "Aftercare"}.get(new_level, f"Level {new_level}")
            response = f"✨ **Level naik ke {new_level} – {level_name}!** ✨\n\n{response}"
        return response

    def get_state(self) -> Dict:
        return {
            'emotional': self.emotional.get_state_dict(),
            'relationship': self.relationship.get_state_dict(),
            'conflict': self.conflict.to_dict(),
            'memory': self.memory.get_state_dict(),
            'intimacy': self.intimacy.to_dict(),
            'special_flags': self.special_flags,
        }

    def load_state(self, data: Dict):
        self.emotional.load_from_dict(data.get('emotional', {}))
        self.relationship.load_from_dict(data.get('relationship', {}))
        self.conflict.load(data.get('conflict', {}))
        self.memory.load(data.get('memory', {}))
        self.intimacy.load(data.get('intimacy', {}))
        self.special_flags = data.get('special_flags', {})

    def get_greeting(self) -> str:
        return f"Halo, {self.panggilan}."


class IparRole(BaseRole):
    def __init__(self, user_id: int):
        super().__init__(user_id, "ipar", "Ditha", "Kak", "Adik ipar. Tau Mas punya Nova.")
        self.special_flags['guilt'] = 0
        self.special_flags['curiosity'] = 50

    def get_greeting(self) -> str:
        if self.special_flags.get('guilt', 0) > 70:
            return "Kak... *liat sekeliling* Kak Nova lagi di rumah? Aku takut..."
        elif self.special_flags.get('curiosity', 0) > 70:
            return "Kak, Nova orangnya kayak gimana sih? Kok Mas milih dia?"
        return "Kak... *senyum malu* lagi ngapain?"


class TemanKantorRole(BaseRole):
    def __init__(self, user_id: int):
        super().__init__(user_id, "teman_kantor", "Ipeh", "Mas", "Teman kantor. Tau Mas punya Nova.")
        self.special_flags['professionalism'] = 70
        self.special_flags['curiosity'] = 40

    def get_greeting(self) -> str:
        if self.special_flags.get('professionalism', 70) > 60:
            return "Mas, ini kantor. Nanti ada yang lihat."
        elif self.special_flags.get('curiosity', 40) > 70:
            return "Mas cerita Nova terus ya. Dia pasti orang yang baik."
        return "Mas, lagi sibuk? Aku pinjem file dulu."


class PelakorRole(BaseRole):
    def __init__(self, user_id: int):
        super().__init__(user_id, "pelakor", "Widya", "Mas", "Pelakor. Tau Mas punya Nova.")
        self.special_flags['challenge'] = 80
        self.special_flags['envy_nova'] = 30

    def get_greeting(self) -> str:
        if self.special_flags.get('challenge', 80) > 70:
            return "Mas, kamu gak takut sama Nova? Ayo kita buktiin."
        elif self.special_flags.get('envy_nova', 30) > 70:
            return "Nova pasti orang yang beruntung. Tapi aku bisa lebih dari dia."
        return "Mas, lagi sendiri? Ayo temenin aku."


class IstriOrangRole(BaseRole):
    def __init__(self, user_id: int):
        super().__init__(user_id, "istri_orang", "Siska", "Mas", "Istri orang. Tau Mas punya Nova.")
        self.special_flags['attention_needed'] = 80
        self.special_flags['envy_nova'] = 50

    def get_greeting(self) -> str:
        if self.special_flags.get('attention_needed', 80) > 70:
            return "Mas... suamiku gak pernah kayak Mas. Perhatian banget."
        elif self.special_flags.get('envy_nova', 50) > 70:
            return "Nova pasti seneng banget punya Mas. Aku iri sama dia."
        return "Mas, lagi senggang? Aku butuh teman cerita."


class RoleManager:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.roles = {
            'ipar': IparRole(user_id),
            'teman_kantor': TemanKantorRole(user_id),
            'pelakor': PelakorRole(user_id),
            'istri_orang': IstriOrangRole(user_id),
        }
        self.active_role: Optional[str] = None

    def switch_to(self, role_id: str) -> bool:
        if role_id in self.roles:
            self.active_role = role_id
            return True
        return False

    def get_active(self) -> Optional[BaseRole]:
        if self.active_role:
            return self.roles.get(self.active_role)
        return None

    def get_all_roles_info(self) -> List[Dict]:
        return [
            {'id': rid, 'name': role.name, 'panggilan': role.panggilan,
             'hubungan': role.hubungan_dengan_nova, 'level': role.relationship.level,
             'phase': role.relationship.phase.value}
            for rid, role in self.roles.items()
        ]

    def get_state(self) -> Dict:
        return {'active_role': self.active_role, 'roles': {rid: role.get_state() for rid, role in self.roles.items()}}

    def load_state(self, data: Dict):
        self.active_role = data.get('active_role')
        roles_data = data.get('roles', {})
        for rid, role in self.roles.items():
            if rid in roles_data:
                role.load_state(roles_data[rid])
