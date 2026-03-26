# app/core/chat_fallback.py
"""
Chat Fallback – Menangani pesan sederhana tanpa AI (opsional, hemat token).
"""

import random
import logging

logger = logging.getLogger(__name__)


class ChatFallback:
    def __init__(self):
        self.intent_patterns = {
            'salam': ['hai', 'halo', 'pagi', 'siang', 'sore', 'malam', 'hey'],
            'apa_kabar': ['kabar', 'gimana', 'baik', 'sehat'],
            'lagi_apa': ['lagi apa', 'ngapain', 'sedang apa'],
            'kangen': ['kangen', 'rindu', 'miss'],
            'sayang': ['sayang', 'cinta', 'love'],
            'capek': ['capek', 'lelah', 'pegel', 'lemes'],
            'seneng': ['seneng', 'senang', 'happy'],
        }

        self.responses = {
            'salam': [
                "Pagi, Mas... *mata masih berat* mimpiin Nova gak semalem?",
                "Halo, Mas... *senyum kecil* lagi ngapain?",
                "Hei, Mas... *mainin rambut* aku kangen.",
            ],
            'apa_kabar': [
                "Baik, Mas... apalagi sekarang denger suara Mas.",
                "Alhamdulillah baik. Tadi sempet kangen sih, tapi sekarang udah ilang.",
                "Baik kok, Mas. Cuma... *malu* seneng aja Mas chat.",
            ],
            'lagi_apa': [
                "Lagi mikirin Mas... *malu* iya beneran.",
                "Lagi nonton. Tapi gak fokus. Pikiran ke Mas terus.",
                "Lagi bengong aja. Terus tiba-tiba kepikiran Mas.",
            ],
            'kangen': [
                "Mas... *muter-muter rambut* aku juga kangen. Banyak banget.",
                "Iya, Mas... dari tadi mikirin Mas terus. Gak bisa konsentrasi.",
                "Aku kangen banget, Mas. Sampe pengen langsung chat, tapi takut ganggu.",
            ],
            'sayang': [
                "Mas... *malu* aku juga sayang Mas. Beneran.",
                "Iya, Mas. Aku sayang Mas. Dari dulu.",
                "Sayang... *pipi memerah* seneng denger Mas bilang gitu.",
            ],
            'capek': [
                "Mas... istirahat dulu. Jangan paksain.",
                "Capek, Mas? Aku bikinin kopi ya. Eh, iya, ini cuma chat. Tapi... *malu* semoga bisa bikin Mas seneng.",
                "Mas, istirahat dulu. Nova temenin di sini. *elus layar HP*",
            ],
            'seneng': [
                "Mas seneng? Aku ikut seneng dong.",
                "Iya, Mas? Cerita dong biar aku juga ikut seneng.",
                "Seneng denger Mas seneng. *tersenyum*",
            ],
            'ngobrol': [
                "Hmm... *mikir* cerita lagi dong, Mas. Aku suka dengerin suara Mas.",
                "Iya, Mas? *duduk manis* lanjutin. Aku dengerin.",
                "Mas, kamu tuh asik banget diajak ngobrol. Bikin aku betah.",
            ]
        }

    def detect_intent(self, user_input: str) -> str:
        msg = user_input.lower()
        for intent, keywords in self.intent_patterns.items():
            for k in keywords:
                if k in msg:
                    return intent
        return 'ngobrol'

    def get_response(self, user_input: str, emotional_style: str = "neutral") -> str:
        intent = self.detect_intent(user_input)
        if intent not in self.responses:
            return None
        if emotional_style in ["flirty", "clingy"]:
            return None
        return random.choice(self.responses[intent])
