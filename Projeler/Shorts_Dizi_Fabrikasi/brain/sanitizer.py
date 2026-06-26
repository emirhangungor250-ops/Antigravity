"""İçerik güvenliği regex katmanı — YT_Otomasyonu/core/prompt_sanitizer.py portu.

Gemini Omni / Kie AI content safety filtresini tetikleyebilecek ifadeleri
gönderim ÖNCESİ yumuşatır. action/sfx alanlarına sanitize_text uygulanır;
diyalog satırları otomatik yeniden yazılmaz, check_dialogue sadece tetik raporlar
(tetik varsa pipeline o sahne için 1 LLM re-ask yapar).
"""
import logging
import re
from typing import List, Tuple

log = logging.getLogger("Sanitizer")

# Her tuple: (regex pattern, güvenli alternatif, açıklama)
REPLACEMENT_RULES = [
    # Hırsızlık / suç
    (r"\bsteal(?:s|ing)?\b", "grab", "hırsızlık→alma"),
    (r"\bstole\b", "grabbed", "hırsızlık→alma"),
    (r"\btheft\b", "prank", "hırsızlık→şaka"),
    (r"\bthief\b", "prankster", "hırsız→şakacı"),
    (r"\brob(?:s|bing|bed)?\b", "take", "soygun→alma"),
    (r"\brobbery\b", "commotion", "soygun→kargaşa"),
    (r"\bcrime\b", "mischief", "suç→yaramazlık"),
    (r"\bcriminal\b", "troublemaker", "suçlu→belalı"),

    # Polis / yasal otorite
    (r"\bpolice officer\b", "security guard", "polis→güvenlik"),
    (r"\bcop(?:s)?\b", "security guard", "polis→güvenlik"),
    (r"\bpolice\b", "security", "polis→güvenlik"),
    (r"\barrest(?:s|ed|ing)?\b", "catch", "tutuklama→yakalama"),
    (r"\bpulled over\b", "stopped", "çevirme→durdurma"),
    (r"\bchased by (?:a )?(?:police|cop|officer)\b", "chased by the owner", "polis kovalamacası→sahibi kovalıyor"),

    # Silah / şiddet
    (r"\bgun(?:s)?\b", "water gun", "silah→su tabancası"),
    (r"\bweapon(?:s)?\b", "toy", "silah→oyuncak"),
    (r"\bknife\b", "spatula", "bıçak→spatula"),
    (r"\bknives\b", "utensils", "bıçaklar→mutfak aletleri"),
    (r"\bblood(?:y)?\b", "red paint", "kan→kırmızı boya"),
    (r"\bviolence\b", "chaos", "şiddet→kaos"),
    (r"\bviolent\b", "chaotic", "şiddetli→kaotik"),
    (r"\bfight(?:s|ing)?\b", "wrestle", "kavga→güreş"),
    (r"\battack(?:s|ing|ed)?\b", "approach", "saldırı→yaklaşma"),
    (r"\bsmash(?:es|ed|ing)?\b", "push through", "kırma→itme"),
    (r"\bkill(?:s|ing|ed)?\b", "scare away", "öldürme→korkutma"),
    (r"\bdestroy(?:s|ed|ing)?\b", "mess up", "yıkma→dağıtma"),
    (r"\bexplod(?:e|es|ed|ing)?\b", "pop", "patlama→patlama (güvenli)"),

    # Tehlikeli hayvan etkileşimleri (çocuk bağlamında)
    (r"\bbaby .{0,30}crocodile\b", "baby and a friendly turtle", "bebek+timsah→bebek+kaplumbağa"),
    (r"\bcrocodile .{0,30}baby\b", "friendly turtle near the baby", "timsah+bebek→kaplumbağa+bebek"),
    (r"\bchild .{0,30}crocodile\b", "child and a friendly turtle", "çocuk+timsah→çocuk+kaplumbağa"),
    (r"\bkid .{0,30}crocodile\b", "kid and a friendly turtle", "çocuk+timsah→çocuk+kaplumbağa"),
    (r"\bkid .{0,30}(?:lion|tiger|shark|wolf)\b", "kid and a friendly puppy", "çocuk+yırtıcı→çocuk+köpek"),
    (r"\bbaby .{0,30}(?:lion|tiger|shark|wolf)\b", "baby and a friendly puppy", "bebek+yırtıcı→bebek+köpek"),
    (r"\b(?:bear|lion|tiger|shark) .{0,30}(?:baby|child|kid|toddler)\b", "friendly dog near the family", "yırtıcı+çocuk→köpek+aile"),

    # Trafik / araç tehlikesi
    (r"\bfloors it\b", "honks the horn", "gaza basma→korna çalma"),
    (r"\bspeeds? (?:off|away)\b", "drives slowly away", "hızla kaçma→yavaşça uzaklaşma"),
    (r"\bruns? from\b", "walks away from", "kaçma→uzaklaşma"),

    # Kaza / acil durum
    (r"\bcrash(?:es|ed|ing)?\b", "tumble", "kaza→düşme"),
    (r"\baccident\b", "incident", "kaza→olay"),
    (r"\bdrown(?:s|ed|ing)?\b", "splash", "boğulma→sıçrama"),

    # Uyuşturucu
    (r"\bdrug(?:s)?\b", "candy", "uyuşturucu→şeker"),
]

# Yüksek riskli pattern'ler (sadece uyarı — otomatik düzeltilemez)
HIGH_RISK_PATTERNS = [
    (r"\bchild(?:ren)? .{0,30}(?:danger|harm|hurt|injur)", "Çocuk+tehlike"),
    (r"\bbaby .{0,30}(?:danger|harm|hurt|fall)", "Bebek+tehlike"),
    (r"\bkid .{0,30}(?:electr|outlet|socket|window)", "Çocuk+elektrik/pencere"),
    (r"\btornado .{0,20}(?:child|baby|kid)", "Doğal afet+çocuk"),
]


def sanitize_text(text: str) -> Tuple[str, List[str]]:
    """action/sfx metnini regex ile temizler.

    Returns: (temizlenmiş metin, tetiklenen kural listesi)
    """
    triggered: List[str] = []
    sanitized = text

    for pattern, replacement, description in REPLACEMENT_RULES:
        matches = re.findall(pattern, sanitized, flags=re.IGNORECASE)
        if matches:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            triggered.append(f"{description}: '{matches[0]}' -> '{replacement}'")

    for pattern, risk_name in HIGH_RISK_PATTERNS:
        if re.search(pattern, sanitized, flags=re.IGNORECASE):
            log.warning("Yüksek riskli pattern: %s", risk_name)
            triggered.append(f"UYARI: {risk_name} (manuel düzeltme gerekebilir)")

    if triggered:
        log.info("Sanitize: %d kural tetiklendi: %s", len(triggered), "; ".join(triggered))

    return sanitized, triggered


def check_dialogue(line: str) -> List[str]:
    """Diyalog satırında tetiklenen kuralları raporlar — metni DEĞİŞTİRMEZ.

    Boş olmayan dönüş = pipeline o sahne için LLM re-ask yapmalı.
    """
    triggered: List[str] = []
    for pattern, _replacement, description in REPLACEMENT_RULES:
        if re.search(pattern, line, flags=re.IGNORECASE):
            triggered.append(description)
    for pattern, risk_name in HIGH_RISK_PATTERNS:
        if re.search(pattern, line, flags=re.IGNORECASE):
            triggered.append(risk_name)
    return triggered
