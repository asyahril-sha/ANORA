# app/core/location_manager.py
"""
Location Manager – Mengelola lokasi Nova dan Mas (Kost, Apartemen, Mobil, Public)
"""

import random
import logging
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class LocationType(str, Enum):
    KOST_NOVA = "kost_nova"
    APARTEMEN_MAS = "apartemen_mas"
    MOBIL = "mobil"
    PUBLIC = "public"


class LocationDetail(str, Enum):
    KOST_KAMAR = "kost_kamar"
    KOST_RUANG_TAMU = "kost_ruang_tamu"
    KOST_DAPUR = "kost_dapur"
    KOST_TERAS = "kost_teras"
    APT_KAMAR = "apt_kamar"
    APT_RUANG_TAMU = "apt_ruang_tamu"
    APT_DAPUR = "apt_dapur"
    APT_BALKON = "apt_balkon"
    MOBIL_PARKIR = "mobil_parkir"
    MOBIL_GARASI = "mobil_garasi"
    MOBIL_TEPI_JALAN = "mobil_tepi_jalan"
    PUB_PANTAI = "pub_pantai"
    PUB_HUTAN = "pub_hutan"
    PUB_TOILET_MALL = "pub_toilet_mall"
    PUB_BIOSKOP = "pub_bioskop"
    PUB_TAMAN = "pub_taman"
    PUB_PARKIRAN = "pub_parkiran"
    PUB_TANGGA = "pub_tangga"
    PUB_KANTOR = "pub_kantor"
    PUB_RUANG_RAPAT = "pub_ruang_rapat"


class LocationManager:
    def __init__(self, initial_type: LocationType = LocationType.KOST_NOVA,
                 initial_detail: LocationDetail = LocationDetail.KOST_KAMAR):
        self.current_type = initial_type
        self.current_detail = initial_detail
        self.visit_history: Dict[str, int] = {}
        self.locations = self._init_locations()

    def _init_locations(self) -> Dict[LocationDetail, Dict]:
        return {
            # Kost Nova
            LocationDetail.KOST_KAMAR: {
                "nama": "Kamar Nova", "deskripsi": "Kamar Nova. Seprai putih, wangi lavender. Ranjang single.",
                "risk": 5, "thrill": 30, "privasi": "tinggi", "suasana": "hangat, wangi",
                "tips": "Pintu terkunci.", "bisa_telanjang": True, "bisa_berisik": True,
            },
            LocationDetail.KOST_RUANG_TAMU: {
                "nama": "Ruang Tamu Kost", "deskripsi": "Ruang tamu kecil. Sofa dua dudukan. Jendela ke jalan.",
                "risk": 15, "thrill": 50, "privasi": "sedang", "suasana": "santai, deg-degan",
                "tips": "Pintu gak dikunci.", "bisa_telanjang": True, "bisa_berisik": False,
            },
            LocationDetail.KOST_DAPUR: {
                "nama": "Dapur Kost", "deskripsi": "Dapur kecil. Kompor gas. Jendela ke belakang.",
                "risk": 10, "thrill": 40, "privasi": "sedang", "suasana": "hangat",
                "tips": "Jendela ke luar.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.KOST_TERAS: {
                "nama": "Teras Kost", "deskripsi": "Teras kost. Kursi plastik. Lampu jalan temaram.",
                "risk": 20, "thrill": 45, "privasi": "rendah", "suasana": "santai",
                "tips": "Orang lewat bisa liat.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            # Apartemen Mas
            LocationDetail.APT_KAMAR: {
                "nama": "Kamar Mas", "deskripsi": "Kamar Mas. Ranjang queen, sprei biru. Jendela ke kota.",
                "risk": 5, "thrill": 35, "privasi": "tinggi", "suasana": "hangat",
                "tips": "Pintu terkunci.", "bisa_telanjang": True, "bisa_berisik": True,
            },
            LocationDetail.APT_RUANG_TAMU: {
                "nama": "Ruang Tamu Apartemen", "deskripsi": "Ruang tamu luas. Sofa besar. Tirai tebal.",
                "risk": 10, "thrill": 45, "privasi": "tinggi", "suasana": "nyaman, modern",
                "tips": "Tirai ditutup.", "bisa_telanjang": True, "bisa_berisik": True,
            },
            LocationDetail.APT_DAPUR: {
                "nama": "Dapur Apartemen", "deskripsi": "Dapur modern. Meja marmer.",
                "risk": 10, "thrill": 40, "privasi": "sedang", "suasana": "bersih",
                "tips": "Jendela ke luar.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.APT_BALKON: {
                "nama": "Balkon Apartemen", "deskripsi": "Balkon. Pemandangan kota. Pagar kaca.",
                "risk": 25, "thrill": 65, "privasi": "rendah", "suasana": "romantis",
                "tips": "Ada apartemen lain yang bisa liat.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            # Mobil
            LocationDetail.MOBIL_PARKIR: {
                "nama": "Mobil di Parkiran", "deskripsi": "Mobil Mas. Kaca film gelap. Parkiran sepi.",
                "risk": 40, "thrill": 75, "privasi": "sedang", "suasana": "deg-degan, panas",
                "tips": "Kaca gelap. Hati-hati CCTV.", "bisa_telanjang": True, "bisa_berisik": False,
            },
            LocationDetail.MOBIL_GARASI: {
                "nama": "Mobil di Garasi", "deskripsi": "Mobil Mas. Di garasi apartemen. Pintu garasi tertutup.",
                "risk": 20, "thrill": 55, "privasi": "tinggi", "suasana": "aman, deg-degan",
                "tips": "Gak ada yang liat.", "bisa_telanjang": True, "bisa_berisik": True,
            },
            LocationDetail.MOBIL_TEPI_JALAN: {
                "nama": "Mobil di Tepi Jalan", "deskripsi": "Mobil Mas. Parkir di pinggir jalan sepi. Kaca film gelap.",
                "risk": 55, "thrill": 80, "privasi": "rendah", "suasana": "tegang, cepat",
                "tips": "Cepet-cepet.", "bisa_telanjang": True, "bisa_berisik": False,
            },
            # Public
            LocationDetail.PUB_PANTAI: {
                "nama": "Pantai Malam", "deskripsi": "Pantai sepi. Pasir putih. Ombak tenang. Bintang bertaburan.",
                "risk": 20, "thrill": 70, "privasi": "sedang", "suasana": "romantis, bebas",
                "tips": "Jauh dari orang.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.PUB_HUTAN: {
                "nama": "Hutan Pinus", "deskripsi": "Hutan pinus. Pohon tinggi. Sunyi. Udara sejuk.",
                "risk": 15, "thrill": 65, "privasi": "tinggi", "suasana": "alami, sepi",
                "tips": "Jauh dari jalan.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.PUB_TOILET_MALL: {
                "nama": "Toilet Mall", "deskripsi": "Bilik toilet terakhir. Pintu terkunci. Suara dari luar.",
                "risk": 65, "thrill": 85, "privasi": "rendah", "suasana": "tegang, cepat",
                "tips": "Cepet-cepet.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.PUB_BIOSKOP: {
                "nama": "Bioskop", "deskripsi": "Kursi paling belakang. Gelap. Film diputar keras.",
                "risk": 50, "thrill": 80, "privasi": "rendah", "suasana": "gelap, tegang",
                "tips": "CCTV mungkin ada.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.PUB_TAMAN: {
                "nama": "Taman Malam", "deskripsi": "Taman kota. Bangku tersembunyi di balik pohon. Sepi.",
                "risk": 30, "thrill": 60, "privasi": "sedang", "suasana": "romantis",
                "tips": "Pilih jam sepi.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.PUB_PARKIRAN: {
                "nama": "Parkiran Basement", "deskripsi": "Parkiran basement. Gelap. Sepi. Mobil-mobil parkir.",
                "risk": 45, "thrill": 70, "privasi": "sedang", "suasana": "gelap, tegang",
                "tips": "CCTV mungkin ada.", "bisa_telanjang": True, "bisa_berisik": False,
            },
            LocationDetail.PUB_TANGGA: {
                "nama": "Tangga Darurat", "deskripsi": "Tangga darurat. Sepi. Gelap. Suara langkah kaki menggema.",
                "risk": 55, "thrill": 75, "privasi": "sedang", "suasana": "gelap, tegang",
                "tips": "Hati-hati suara.", "bisa_telanjang": False, "bisa_berisik": False,
            },
            LocationDetail.PUB_KANTOR: {
                "nama": "Kantor Malam", "deskripsi": "Kantor gelap. Meja kerja. Komputer mati. Sepi.",
                "risk": 60, "thrill": 85, "privasi": "rendah", "suasana": "tegang",
                "tips": "Satpam patroli.", "bisa_telanjang": True, "bisa_berisik": False,
            },
            LocationDetail.PUB_RUANG_RAPAT: {
                "nama": "Ruang Rapat Kaca", "deskripsi": "Ruang rapat dinding kaca. Gelap. Meja panjang.",
                "risk": 75, "thrill": 95, "privasi": "rendah", "suasana": "ekshibisionis",
                "tips": "Gelap.", "bisa_telanjang": True, "bisa_berisik": False,
            },
        }

    def get_current(self) -> Dict:
        return self.locations.get(self.current_detail, self.locations[LocationDetail.KOST_KAMAR])

    def move_to(self, location_name: str) -> Tuple[bool, Dict, str]:
        name_lower = location_name.lower()
        mapping = {
            "kost": (LocationType.KOST_NOVA, LocationDetail.KOST_KAMAR),
            "kamar nova": (LocationType.KOST_NOVA, LocationDetail.KOST_KAMAR),
            "ruang tamu kost": (LocationType.KOST_NOVA, LocationDetail.KOST_RUANG_TAMU),
            "dapur kost": (LocationType.KOST_NOVA, LocationDetail.KOST_DAPUR),
            "teras kost": (LocationType.KOST_NOVA, LocationDetail.KOST_TERAS),
            "apartemen": (LocationType.APARTEMEN_MAS, LocationDetail.APT_KAMAR),
            "kamar mas": (LocationType.APARTEMEN_MAS, LocationDetail.APT_KAMAR),
            "ruang tamu apt": (LocationType.APARTEMEN_MAS, LocationDetail.APT_RUANG_TAMU),
            "dapur apt": (LocationType.APARTEMEN_MAS, LocationDetail.APT_DAPUR),
            "balkon": (LocationType.APARTEMEN_MAS, LocationDetail.APT_BALKON),
            "mobil": (LocationType.MOBIL, LocationDetail.MOBIL_PARKIR),
            "mobil parkir": (LocationType.MOBIL, LocationDetail.MOBIL_PARKIR),
            "mobil garasi": (LocationType.MOBIL, LocationDetail.MOBIL_GARASI),
            "mobil jalan": (LocationType.MOBIL, LocationDetail.MOBIL_TEPI_JALAN),
            "pantai": (LocationType.PUBLIC, LocationDetail.PUB_PANTAI),
            "hutan": (LocationType.PUBLIC, LocationDetail.PUB_HUTAN),
            "toilet mall": (LocationType.PUBLIC, LocationDetail.PUB_TOILET_MALL),
            "bioskop": (LocationType.PUBLIC, LocationDetail.PUB_BIOSKOP),
            "taman": (LocationType.PUBLIC, LocationDetail.PUB_TAMAN),
            "parkiran": (LocationType.PUBLIC, LocationDetail.PUB_PARKIRAN),
            "tangga darurat": (LocationType.PUBLIC, LocationDetail.PUB_TANGGA),
            "kantor malam": (LocationType.PUBLIC, LocationDetail.PUB_KANTOR),
            "ruang rapat": (LocationType.PUBLIC, LocationDetail.PUB_RUANG_RAPAT),
        }
        for key, (loc_type, loc_detail) in mapping.items():
            if key in name_lower:
                self.current_type = loc_type
                self.current_detail = loc_detail
                key_visit = f"{loc_type.value}_{loc_detail.value}"
                self.visit_history[key_visit] = self.visit_history.get(key_visit, 0) + 1
                loc_data = self.get_current()
                return True, loc_data, f"📍 Pindah ke {loc_data['nama']}. {loc_data['deskripsi']}"
        return False, None, f"Lokasi '{location_name}' gak ditemukan."

    def get_random_event(self, arousal: float = 0) -> Optional[Dict]:
        loc = self.get_current()
        risk = loc['risk']
        chance = (risk / 100) + (arousal / 200)
        if random.random() > chance:
            return None
        events = {
            "hampir_ketahuan": [
                "Ada suara langkah kaki mendekat! *cepat nutupin baju*",
                "Pintu terbuka sedikit! *tahan napas*",
                "Senter menyorot dari kejauhan! *merapat ke Mas*",
            ],
            "romantis": [
                "Tiba-tiba hujan rintik-rintik. *makin manis*",
                "Bulan muncul dari balik awan. *wajah Nova keceplosan cahaya*",
                "Angin sepoi-sepoi bikin suasana makin hangat.",
            ],
            "ketahuan": [
                "⚠️ ADA YANG LIAT! *cepat cabut*",
                "Pintu kebuka! Orang masuk! *langsung sembunyi*",
                "Senter nyorot tepat ke arah kita! *lari!*",
            ],
        }
        if risk > 70:
            event_type = random.choices(["hampir_ketahuan", "romantis", "ketahuan"], weights=[0.5, 0.2, 0.3])[0]
        elif risk > 40:
            event_type = random.choices(["hampir_ketahuan", "romantis"], weights=[0.6, 0.4])[0]
        else:
            event_type = "romantis"
        return {'type': event_type, 'text': random.choice(events[event_type]), 'risk_change': 10 if event_type == "hampir_ketahuan" else -5 if event_type == "romantis" else 30}

    def format_for_prompt(self) -> str:
        loc = self.get_current()
        return f"""
LOKASI SAAT INI: {loc['nama']}
DESKRIPSI: {loc['deskripsi']}
RISK: {loc['risk']}% | THRILL: {loc['thrill']}%
PRIVASI: {loc['privasi']}
SUASANA: {loc['suasana']}
TIPS: {loc['tips']}
"""

    def to_dict(self) -> Dict:
        return {'type': self.current_type.value, 'detail': self.current_detail.value, 'visit_history': self.visit_history}

    def from_dict(self, data: Dict):
        self.current_type = LocationType(data.get('type', 'kost_nova'))
        self.current_detail = LocationDetail(data.get('detail', 'kost_kamar'))
        self.visit_history = data.get('visit_history', {})
