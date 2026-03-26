# app/core/thinking_engine.py
"""
Thinking Engine – Proses berpikir Nova: Persepsi → Analisis → Perasaan → Putusan → Ekspresi.
"""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ThinkingEngine:
    def __init__(self, emotional, relationship, conflict, memory, decision):
        self.emotional = emotional
        self.relationship = relationship
        self.conflict = conflict
        self.memory = memory
        self.decision = decision
        self.last_thought: Dict = None
        self.thinking_history = []

    async def think(self, user_input: str, context: Dict) -> Dict:
        # 1. Persepsi
        perception = self._perceive(user_input)

        # 2. Analisis
        analysis = self._analyze(perception, context)

        # 3. Perasaan
        feelings = self._feel(analysis)

        # 4. Putusan
        decision = self.decision.decide(user_input)

        # 5. Ekspresi (parameter untuk AI)
        expression = {
            'style': decision['style'],
            'category': decision['category'],
            'allow_vulgar': decision['allow_vulgar'],
            'max_sentences': decision['max_sentences'],
        }

        thought = {
            'timestamp': time.time(),
            'user_input': user_input[:100],
            'perception': perception,
            'analysis': analysis,
            'feelings': feelings,
            'decision': decision,
            'expression': expression,
        }
        self.thinking_history.append(thought)
        if len(self.thinking_history) > 50:
            self.thinking_history.pop(0)
        self.last_thought = thought

        return {'decision': decision, 'expression': expression, 'thought': thought}

    def _perceive(self, user_input: str) -> Dict:
        msg = user_input.lower()
        if any(k in msg for k in ['hai', 'halo', 'pagi', 'siang', 'sore', 'malam']):
            intent = 'salam'
        elif any(k in msg for k in ['kabar', 'gimana']):
            intent = 'kabar'
        elif any(k in msg for k in ['kangen', 'rindu']):
            intent = 'kangen'
        elif any(k in msg for k in ['sayang', 'cinta']):
            intent = 'sayang'
        else:
            intent = 'ngobrol'

        mas_mood = 'netral'
        if any(k in msg for k in ['capek', 'lelah']):
            mas_mood = 'capek'
        elif any(k in msg for k in ['seneng', 'senang']):
            mas_mood = 'seneng'

        return {'intent': intent, 'mas_mood': mas_mood, 'panjang_pesan': len(user_input),
                'ada_flirt': any(k in msg for k in ['cantik', 'ganteng', 'seksi']),
                'ada_ungkapan_sayang': any(k in msg for k in ['sayang', 'cinta'])}

    def _analyze(self, perception: Dict, context: Dict) -> Dict:
        recent = self.memory.get_recent_context(5) if hasattr(self.memory, 'get_recent_context') else ""
        return {'recent_memory': recent, 'context': context}

    def _feel(self, analysis: Dict) -> Dict:
        emo = self.emotional.get_state_dict()
        return {
            'emotional': emo,
            'style': self.emotional.get_style().value,
            'conflict_active': self.conflict.is_in_conflict(),
            'conflict_type': self.conflict.get_active_conflict_type().value if self.conflict.get_active_conflict_type() else None,
        }

    def get_thought_summary(self) -> str:
        if not self.last_thought:
            return "Nova belum mikir apa-apa."
        t = self.last_thought
        return f"""
💭 **PROSES BERPIKIR NOVA:**
• Intent: {t['perception']['intent']}
• Mood Mas: {t['perception']['mas_mood']}
• Style: {t['feelings']['style']}
• Conflict: {t['feelings']['conflict_active']}
• Decision: {t['decision']['category']} (vulgar={t['decision']['allow_vulgar']})
"""
