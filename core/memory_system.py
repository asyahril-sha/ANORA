# app/core/memory_system.py
"""
Memory System – Short-term, long-term, complete state (pakaian, posisi, aktivitas, lokasi)
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .location_manager import LocationManager, LocationType, LocationDetail

logger = logging.getLogger(__name__)


@dataclass
class Clothing:
    hijab: bool = True
    hijab_warna: str = "pink muda"
    top: str = "daster rumah motif bunga"
    bra: bool = True
    bra_warna: str = "putih polos"
    cd: bool = True
    cd_warna: str = "putih motif bunga"
    mas_top: str = "kaos"
    mas_bottom: str = "celana pendek"
    mas_boxer: bool = True
    mas_boxer_warna: str = "hitam"

    def format_nova(self) -> str:
        parts = []
        if self.hijab:
            parts.append(f"hijab {self.hijab_warna}")
        else:
            parts.append("tanpa hijab, rambut sebahu hitam terurai")
        if self.top:
            parts.append(self.top)
            if self.bra:
                parts.append(f"(pake bra {self.bra_warna})")
        else:
            if self.bra:
                parts.append(f"cuma pake bra {self.bra_warna}")
            else:
                parts.append("telanjang dada")
        if self.cd:
            parts.append(f"pake {self.cd_warna}")
        else:
            parts.append("tanpa celana dalam")
        return ", ".join(parts)

    def format_mas(self) -> str:
        parts = []
        if self.mas_top:
            parts.append(self.mas_top)
        if self.mas_bottom:
            parts.append(self.mas_bottom)
            if self.mas_boxer:
                parts.append(f"(boxer {self.mas_boxer_warna} di dalem)")
        else:
            if self.mas_boxer:
                parts.append(f"cuma pake boxer {self.mas_boxer_warna}")
            else:
                parts.append("telanjang")
        return ", ".join(parts)

    def to_dict(self) -> Dict:
        return {
            'hijab': self.hijab, 'hijab_warna': self.hijab_warna,
            'top': self.top, 'bra': self.bra, 'bra_warna': self.bra_warna,
            'cd': self.cd, 'cd_warna': self.cd_warna,
            'mas_top': self.mas_top, 'mas_bottom': self.mas_bottom,
            'mas_boxer': self.mas_boxer, 'mas_boxer_warna': self.mas_boxer_warna,
        }

    def from_dict(self, data: Dict):
        self.hijab = data.get('hijab', True)
        self.hijab_warna = data.get('hijab_warna', 'pink muda')
        self.top = data.get('top', 'daster rumah motif bunga')
        self.bra = data.get('bra', True)
        self.bra_warna = data.get('bra_warna', 'putih polos')
        self.cd = data.get('cd', True)
        self.cd_warna = data.get('cd_warna', 'putih motif bunga')
        self.mas_top = data.get('mas_top', 'kaos')
        self.mas_bottom = data.get('mas_bottom', 'celana pendek')
        self.mas_boxer = data.get('mas_boxer', True)
        self.mas_boxer_warna = data.get('mas_boxer_warna', 'hitam')


@dataclass
class Position:
    state: Optional[str] = None
    detail: Optional[str] = None
    last_update: float = field(default_factory=time.time)


@dataclass
class ActivityState:
    main: str = "santai"
    detail: Optional[str] = None
    last_update: float = field(default_factory=time.time)


@dataclass
class TogetherState:
    location: str = "kamar"
    distance: Optional[str] = None
    atmosphere: str = "santai"
    last_action: Optional[str] = None
    last_update: float = field(default_factory=time.time)


class CompleteState:
    def __init__(self, initial_state: Dict = None):
        self.clothing = Clothing()
        self.position_nova = Position()
        self.position_mas = Position()
        self.activity_nova = ActivityState()
        self.activity_mas = ActivityState()
        self.location = LocationManager()
        self.together = TogetherState()

        if initial_state:
            self.load(initial_state)

    def update_from_message(self, text: str) -> Dict[str, Any]:
        changes = {}
        msg = text.lower()

        # Pakaian Nova
        if "buka hijab" in msg or "lepas hijab" in msg:
            self.clothing.hijab = False
            changes['nova_hijab'] = False
        if "pakai hijab" in msg:
            self.clothing.hijab = True
            changes['nova_hijab'] = True

        if "buka baju" in msg:
            if "nova" in msg or "kamu" in msg:
                self.clothing.top = None
                changes['nova_top'] = None
            else:
                self.clothing.mas_top = None
                changes['mas_top'] = None

        if "pakai baju" in msg:
            if "nova" in msg or "kamu" in msg:
                self.clothing.top = "daster rumah"
                changes['nova_top'] = "daster rumah"
            else:
                self.clothing.mas_top = "kaos"
                changes['mas_top'] = "kaos"

        if "buka bra" in msg:
            self.clothing.bra = False
            changes['nova_bra'] = False
        if "pakai bra" in msg:
            self.clothing.bra = True
            changes['nova_bra'] = True

        if "buka cd" in msg or "buka celana dalam" in msg:
            self.clothing.cd = False
            changes['nova_cd'] = False
        if "pakai cd" in msg or "pakai celana dalam" in msg:
            self.clothing.cd = True
            changes['nova_cd'] = True

        # Pakaian Mas
        if "buka celana" in msg:
            self.clothing.mas_bottom = None
            changes['mas_bottom'] = None
        if "pakai celana" in msg:
            self.clothing.mas_bottom = "celana pendek"
            changes['mas_bottom'] = "celana pendek"

        if "buka boxer" in msg:
            self.clothing.mas_boxer = False
            changes['mas_boxer'] = False
        if "pakai boxer" in msg:
            self.clothing.mas_boxer = True
            changes['mas_boxer'] = True

        # Posisi
        if "duduk" in msg:
            if "nova" in msg or "kamu" in msg:
                self.position_nova.state = "duduk"
                changes['nova_position'] = "duduk"
            else:
                self.position_mas.state = "duduk"
                changes['mas_position'] = "duduk"

        if "berdiri" in msg or "bangun" in msg:
            if "nova" in msg or "kamu" in msg:
                self.position_nova.state = "berdiri"
                changes['nova_position'] = "berdiri"
            else:
                self.position_mas.state = "berdiri"
                changes['mas_position'] = "berdiri"

        if "tidur" in msg or "rebahan" in msg:
            if "nova" in msg or "kamu" in msg:
                self.position_nova.state = "tidur"
                changes['nova_position'] = "tidur"
            else:
                self.position_mas.state = "tidur"
                changes['mas_position'] = "tidur"

        if "merangkak" in msg and ("nova" in msg or "kamu" in msg):
            self.position_nova.state = "merangkak"
            changes['nova_position'] = "merangkak"

        # Aktivitas
        if "masak" in msg:
            self.activity_nova.main = "masak"
            changes['nova_activity'] = "masak"
        if "makan" in msg:
            self.activity_nova.main = "makan"
            changes['nova_activity'] = "makan"
        if "nonton" in msg:
            self.activity_nova.main = "nonton"
            changes['nova_activity'] = "nonton"
        if "mandi" in msg:
            self.activity_nova.main = "mandi"
            changes['nova_activity'] = "mandi"

        # Lokasi via location manager (perintah pindah)
        if "pindah" in msg and "ke" in msg:
            import re
            match = re.search(r'pindah\s+ke\s+(.+)', msg)
            if match:
                loc_name = match.group(1).strip()
                success, loc_data, message = self.location.move_to(loc_name)
                if success:
                    changes['location'] = loc_name

        # Atmosfer (sederhana)
        if "romantis" in msg:
            self.together.atmosphere = "romantis"
            changes['atmosphere'] = "romantis"
        elif "tegang" in msg:
            self.together.atmosphere = "tegang"
            changes['atmosphere'] = "tegang"
        elif "panas" in msg:
            self.together.atmosphere = "panas"
            changes['atmosphere'] = "panas"

        return changes

    def format_for_prompt(self) -> str:
        loc = self.location.get_current()
        return f"""
═══════════════════════════════════════════════════════════════
SITUASI SAAT INI:
═══════════════════════════════════════════════════════════════
LOKASI: {loc['nama']}
{loc['deskripsi']}
RISK: {loc['risk']}% | THRILL: {loc['thrill']}%

AKTIVITAS:
- Nova: {self.activity_nova.main}
- Mas: {self.activity_mas.main}

PAKAIAN:
- Nova: {self.clothing.format_nova()}
- Mas: {self.clothing.format_mas()}

POSISI:
- Nova: {self.position_nova.state or 'tidak disebut'}
- Mas: {self.position_mas.state or 'tidak disebut'}

ATMOSFER: {self.together.atmosphere}
"""

    def to_dict(self) -> Dict:
        return {
            'clothing': self.clothing.to_dict(),
            'position_nova': {'state': self.position_nova.state, 'detail': self.position_nova.detail},
            'position_mas': {'state': self.position_mas.state, 'detail': self.position_mas.detail},
            'activity_nova': {'main': self.activity_nova.main, 'detail': self.activity_nova.detail},
            'activity_mas': {'main': self.activity_mas.main, 'detail': self.activity_mas.detail},
            'location': self.location.to_dict(),
            'together': {
                'location': self.together.location,
                'distance': self.together.distance,
                'atmosphere': self.together.atmosphere,
                'last_action': self.together.last_action,
                'last_update': self.together.last_update,
            },
        }

    def load(self, data: Dict):
        self.clothing.from_dict(data.get('clothing', {}))
        self.position_nova.state = data.get('position_nova', {}).get('state')
        self.position_nova.detail = data.get('position_nova', {}).get('detail')
        self.position_mas.state = data.get('position_mas', {}).get('state')
        self.position_mas.detail = data.get('position_mas', {}).get('detail')
        self.activity_nova.main = data.get('activity_nova', {}).get('main', 'santai')
        self.activity_nova.detail = data.get('activity_nova', {}).get('detail')
        self.activity_mas.main = data.get('activity_mas', {}).get('main', 'santai')
        self.activity_mas.detail = data.get('activity_mas', {}).get('detail')
        self.location.from_dict(data.get('location', {}))
        together = data.get('together', {})
        self.together.location = together.get('location', 'kamar')
        self.together.distance = together.get('distance')
        self.together.atmosphere = together.get('atmosphere', 'santai')
        self.together.last_action = together.get('last_action')
        self.together.last_update = together.get('last_update', time.time())


class LongTermMemory:
    def __init__(self):
        self.facts: List[Dict] = []
        self.moments: List[Dict] = []
        self.promises: List[Dict] = []

    def add_fact(self, fact: str, emotion: str = "netral"):
        self.facts.append({'text': fact, 'emotion': emotion, 'timestamp': time.time()})
        if len(self.facts) > 200:
            self.facts.pop(0)

    def add_moment(self, moment: str, emotion: str):
        self.moments.append({'text': moment, 'emotion': emotion, 'timestamp': time.time()})
        if len(self.moments) > 100:
            self.moments.pop(0)

    def add_promise(self, promise: str, from_who: str = "mas"):
        self.promises.append({'text': promise, 'from': from_who, 'status': 'pending', 'timestamp': time.time()})
        if len(self.promises) > 50:
            self.promises.pop(0)

    def get_facts_text(self, n: int = 5) -> str:
        return "\n".join([f"- {f['text']}" for f in self.facts[-n:]])

    def get_moments_text(self, n: int = 5) -> str:
        return "\n".join([f"- {m['text']} ({m['emotion']})" for m in self.moments[-n:]])

    def get_promises_text(self) -> str:
        pending = [p for p in self.promises if p['status'] == 'pending']
        if not pending:
            return "Tidak ada janji pending"
        return "\n".join([f"- {p['text']}" for p in pending[-3:]])

    def to_dict(self) -> Dict:
        return {'facts': self.facts[-100:], 'moments': self.moments[-50:], 'promises': self.promises[-20:]}

    def load(self, data: Dict):
        self.facts = data.get('facts', [])
        self.moments = data.get('moments', [])
        self.promises = data.get('promises', [])


class ConversationMemory:
    def __init__(self, max_archive=1000, short_term_size=50):
        self.max_archive = max_archive
        self.short_term_size = short_term_size
        self.archive: List[Dict] = []
        self.short_term: List[Dict] = []

    def add(self, user_input: str, nova_response: str, emotional_state: Dict = None):
        entry = {'timestamp': time.time(), 'user': user_input[:500], 'nova': nova_response[:500], 'emotional': emotional_state}
        self.archive.append(entry)
        if len(self.archive) > self.max_archive:
            self.archive.pop(0)
        self.short_term = self.archive[-self.short_term_size:]

    def get_recent(self, n: int = 20) -> List[Dict]:
        return self.short_term[-n:]

    def to_dict(self) -> Dict:
        return {'archive': self.archive[-500:], 'short_term_size': self.short_term_size}

    def load(self, data: Dict):
        self.archive = data.get('archive', [])
        self.short_term = self.archive[-self.short_term_size:]


class MemorySystem:
    def __init__(self, user_id: int, initial_state: Dict = None):
        self.user_id = user_id
        self.complete = CompleteState(initial_state.get('complete') if initial_state else None)
        self.conversation = ConversationMemory()
        self.long_term = LongTermMemory()
        if initial_state:
            self.conversation.load(initial_state.get('conversation', {}))
            self.long_term.load(initial_state.get('long_term', {}))

    def update_from_message(self, user_input: str, nova_response: str, emotional_state: Dict):
        self.complete.update_from_message(user_input)
        self.conversation.add(user_input, nova_response, emotional_state)

    def get_context_for_prompt(self, short_term_limit: int = 20) -> str:
        context = self.complete.format_for_prompt()
        context += "\n═══════════════════════════════════════════════════════════════\n"
        context += "MEMORY NOVA:\n"
        context += "═══════════════════════════════════════════════════════════════\n"
        context += f"\nPERCAKAPAN TERAKHIR:\n{self.get_recent_context(short_term_limit)}\n"
        facts = self.long_term.get_facts_text(5)
        if facts:
            context += f"\nKEBIASAAN MAS YANG NOVA INGAT:\n{facts}\n"
        moments = self.long_term.get_moments_text(3)
        if moments:
            context += f"\nMOMEN INDAH:\n{moments}\n"
        promises = self.long_term.get_promises_text()
        context += f"\nJANJI YANG BELUM DITEPATI:\n{promises}\n"
        return context

    def get_recent_context(self, n: int = 20) -> str:
        recent = self.conversation.get_recent(n)
        if not recent:
            return "Belum ada percakapan."
        lines = []
        for e in recent:
            lines.append(f"Mas: {e['user']}\nNova: {e['nova']}")
        return "\n".join(lines)

    def get_state_dict(self) -> Dict:
        return {
            'complete': self.complete.to_dict(),
            'conversation': self.conversation.to_dict(),
            'long_term': self.long_term.to_dict(),
        }

    def load(self, data: Dict):
        self.complete.load(data.get('complete', {}))
        self.conversation.load(data.get('conversation', {}))
        self.long_term.load(data.get('long_term', {}))
