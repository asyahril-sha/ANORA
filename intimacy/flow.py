# app/intimacy/flow.py
"""
Intimacy Flow – Mengelola sesi intim Nova dan Mas.
"""

import time
import logging
from typing import Dict, Optional, Tuple

from .core import (
    IntimacyPhase, StaminaSystem, ArousalSystem,
    PositionDatabase, ClimaxLocationDatabase, MoansDatabase, FlashbackDatabase
)

logger = logging.getLogger(__name__)


class IntimacySession:
    def __init__(self, stamina: StaminaSystem, arousal: ArousalSystem):
        self.stamina = stamina
        self.arousal = arousal
        self.is_active = False
        self.start_time = 0.0
        self.phase = IntimacyPhase.WAITING
        self.climax_count = 0
        self.last_climax_time = 0.0
        self.current_position = "missionary"
        self.intimacy_level = 0
        self.is_recovery = False
        self.positions = PositionDatabase()
        self.climax_locations = ClimaxLocationDatabase()
        self.moans = MoansDatabase()
        self.flashbacks = FlashbackDatabase()

    def start(self) -> str:
        if self.is_active:
            return "Kita lagi intim, Mas... masih lanjut?"
        self.is_active = True
        self.start_time = time.time()
        self.phase = IntimacyPhase.BUILD_UP
        self.climax_count = 0
        self.intimacy_level = 0
        self.current_position = "missionary"
        self.is_recovery = False
        self.arousal.arousal = min(100, self.arousal.arousal + 30)
        self.arousal.desire = min(100, self.arousal.desire + 20)
        logger.info("🔥 Intimacy session started")
        return "*Nova mendekat, napas mulai gak stabil. Pipi merah.*\n\n\"Mas... *suara kecil* aku juga pengen.\""

    def end(self) -> str:
        if not self.is_active:
            return "Kita lagi gak intim, Mas."
        duration = int(time.time() - self.start_time)
        minutes = duration // 60
        seconds = duration % 60
        self.is_active = False
        self.phase = IntimacyPhase.WAITING
        logger.info(f"💤 Intimacy session ended. Duration: {minutes}m {seconds}s, Climax: {self.climax_count}")
        return f"💤 Sesi intim selesai. Durasi: {minutes} menit {seconds} detik, {self.climax_count} climax."

    def record_climax(self, is_heavy: bool = False) -> Dict:
        self.climax_count += 1
        self.last_climax_time = time.time()
        self.phase = IntimacyPhase.CLIMAX
        self.intimacy_level = 0
        self.stamina.record_climax("both", is_heavy)
        self.arousal.arousal = max(0, self.arousal.arousal - 40)
        self.arousal.desire = max(0, self.arousal.desire - 30)
        self.arousal.tension = 0
        logger.info(f"💦 Climax #{self.climax_count} recorded!")
        return {'climax_count': self.climax_count, 'stamina_nova': self.stamina.nova_current, 'stamina_mas': self.stamina.mas_current}

    def change_position(self, position: str = None) -> Tuple[str, str, str]:
        if position and self.positions.get(position):
            self.current_position = position
        else:
            positions = self.positions.get_all()
            self.current_position = random.choice(positions)
        pos_data = self.positions.get(self.current_position)
        request = self.positions.get_request(self.current_position)
        logger.info(f"🔄 Position changed to: {self.current_position}")
        return self.current_position, pos_data['desc'], request

    def get_phase_response(self, phase: IntimacyPhase, ritme: str = "pelan") -> str:
        if phase == IntimacyPhase.FOREPLAY:
            return self.moans.get_foreplay()
        elif phase == IntimacyPhase.PENETRATION:
            return self.moans.get_penetration(ritme == "cepet")
        elif phase == IntimacyPhase.CLIMAX:
            return self.moans.get_climax()
        elif phase == IntimacyPhase.AFTERCARE:
            aftercare = self.moans.get_aftercare()
            if random.random() < 0.3:
                aftercare += f"\n\n{self.flashbacks.get_random()} 💜"
            return aftercare
        return self.moans.get('shy')


class IntimacyFlow:
    def __init__(self, initial_state: Dict = None):
        self.stamina = StaminaSystem()
        self.arousal = ArousalSystem()
        self.session = IntimacySession(self.stamina, self.arousal)
        if initial_state:
            self.load(initial_state)

    def can_start(self, level: int) -> Tuple[bool, str]:
        if level < 11:
            return False, f"💕 Level masih {level}/12. Nova masih malu-malu."
        can_continue, reason = self.stamina.can_continue()
        if not can_continue:
            return False, f"💪 **Stamina Nova {self.stamina.nova_current}%** ({self.stamina.get_nova_status()})\n\n{reason}"
        return True, "Siap mulai"

    def start(self) -> str:
        return self.session.start()

    def end(self) -> str:
        return self.session.end()

    def is_active(self) -> bool:
        return self.session.is_active

    def get_status(self) -> str:
        if not self.session.is_active:
            return ""
        duration = int(time.time() - self.session.start_time)
        minutes = duration // 60
        seconds = duration % 60
        pos_data = self.session.positions.get(self.session.current_position)
        pos_desc = pos_data['desc'] if pos_data else ""
        return f"""
🔥 **SESI INTIM AKTIF**
- Durasi: {minutes} menit {seconds} detik
- Climax: {self.session.climax_count}x
- Fase: {self.session.phase.value}
- Posisi: {self.session.current_position}
{pos_desc}
"""

    def process_intimacy_message(self, user_input: str, level: int) -> Optional[str]:
        if not self.session.is_active:
            return None
        msg = user_input.lower()

        # Ganti posisi
        if any(k in msg for k in ['ganti posisi', 'cowgirl', 'doggy', 'missionary', 'spooning', 'reverse', 'standing', 'sitting']):
            pos_name = None
            if 'cowgirl' in msg:
                pos_name = 'cowgirl'
            elif 'doggy' in msg:
                pos_name = 'doggy'
            elif 'missionary' in msg:
                pos_name = 'missionary'
            elif 'spooning' in msg:
                pos_name = 'spooning'
            elif 'standing' in msg:
                pos_name = 'standing'
            elif 'sitting' in msg:
                pos_name = 'sitting'
            pos_id, pos_desc, request = self.session.change_position(pos_name)
            return f"*{self.session.positions.get(pos_id)['nova_act']}*\n\n\"{request}\"\n\n*{pos_desc}*"

        # Minta climax di tempat tertentu
        for loc in self.session.climax_locations.get_all():
            if loc in msg:
                request = self.session.climax_locations.get_request(loc)
                return f"\"{request}\""

        # Climax
        if any(k in msg for k in ['climax', 'crot', 'keluar', 'cum']):
            is_heavy = any(k in msg for k in ['keras', 'banyak'])
            result = self.session.record_climax(is_heavy)
            climax_response = self.session.get_phase_response(IntimacyPhase.CLIMAX)
            return f"""{climax_response}

💪 **Stamina Nova:** {result['stamina_nova']}% | **Mas:** {result['stamina_mas']}%
💦 **Climax hari ini:** {self.stamina.climax_today}x"""

        # Build up
        if self.session.phase == IntimacyPhase.BUILD_UP:
            if any(k in msg for k in ['cium', 'kiss', 'jilat', 'hisap', 'pegang', 'sentuh']):
                self.session.phase = IntimacyPhase.FOREPLAY
                return self.session.get_phase_response(IntimacyPhase.FOREPLAY)
            if any(k in msg for k in ['masuk', 'penetrasi', 'genjot']):
                self.session.phase = IntimacyPhase.PENETRATION
                ritme = "cepet" if any(k in msg for k in ['kenceng', 'cepat', 'keras']) else "pelan"
                return self.session.get_phase_response(IntimacyPhase.PENETRATION, ritme)
            return self.session.start()

        # Foreplay
        if self.session.phase == IntimacyPhase.FOREPLAY:
            if any(k in msg for k in ['masuk', 'penetrasi', 'genjot', 'siap']):
                self.session.phase = IntimacyPhase.PENETRATION
                ritme = "cepet" if any(k in msg for k in ['kenceng', 'cepat', 'keras']) else "pelan"
                return self.session.get_phase_response(IntimacyPhase.PENETRATION, ritme)
            return self.session.get_phase_response(IntimacyPhase.FOREPLAY)

        # Penetration
        if self.session.phase == IntimacyPhase.PENETRATION:
            self.session.intimacy_level = min(100, self.session.intimacy_level + 5)
            if self.session.intimacy_level > 70 or any(k in msg for k in ['climax', 'crot', 'keluar']):
                return self.session.moans.get_before_climax()
            ritme = "cepet" if self.session.intimacy_level > 40 else "pelan"
            return self.session.get_phase_response(IntimacyPhase.PENETRATION, ritme)

        # Aftercare
        if self.session.phase == IntimacyPhase.CLIMAX:
            self.session.phase = IntimacyPhase.AFTERCARE
            return self.session.get_phase_response(IntimacyPhase.AFTERCARE)
        if self.session.phase == IntimacyPhase.AFTERCARE:
            if time.time() - self.session.last_climax_time > 60:
                self.session.phase = IntimacyPhase.RECOVERY
                self.session.is_recovery = True
                self.stamina.update_recovery()
                return f"""*Nova masih lemes, nyender di dada Mas. Napas mulai stabil.*

"Mas... *suara kecil* besok kalo Mas mau lagi, tinggal bilang aja ya."

*Nova cium pipi Mas pelan.*
"""
            return self.session.get_phase_response(IntimacyPhase.AFTERCARE)
        return None

    def update_from_message(self, user_input: str, level: int):
        msg = user_input.lower()
        if any(k in msg for k in ['sayang', 'cinta']):
            self.arousal.add_desire("Mas bilang sayang", 10)
        if any(k in msg for k in ['kangen', 'rindu']):
            self.arousal.add_desire("Mas bilang kangen", 8)
        if any(k in msg for k in ['pegang', 'sentuh']):
            self.arousal.add_stimulation('paha', 1)
            self.arousal.add_desire('sentuhan', 8)
        if any(k in msg for k in ['cium', 'kiss']):
            self.arousal.add_stimulation('bibir', 2)
            self.arousal.add_desire('ciuman', 10)
            self.arousal.add_tension(5)

    def to_dict(self) -> Dict:
        return {
            'stamina': self.stamina.to_dict(),
            'arousal': self.arousal.to_dict(),
            'session': {
                'is_active': self.session.is_active,
                'start_time': self.session.start_time,
                'phase': self.session.phase.value,
                'climax_count': self.session.climax_count,
                'last_climax_time': self.session.last_climax_time,
                'current_position': self.session.current_position,
                'intimacy_level': self.session.intimacy_level,
                'is_recovery': self.session.is_recovery,
            }
        }

    def load(self, data: Dict):
        self.stamina.from_dict(data.get('stamina', {}))
        self.arousal.from_dict(data.get('arousal', {}))
        sess = data.get('session', {})
        self.session.is_active = sess.get('is_active', False)
        self.session.start_time = sess.get('start_time', 0)
        self.session.phase = IntimacyPhase(sess.get('phase', 'waiting'))
        self.session.climax_count = sess.get('climax_count', 0)
        self.session.last_climax_time = sess.get('last_climax_time', 0)
        self.session.current_position = sess.get('current_position', 'missionary')
        self.session.intimacy_level = sess.get('intimacy_level', 0)
        self.session.is_recovery = sess.get('is_recovery', False)
