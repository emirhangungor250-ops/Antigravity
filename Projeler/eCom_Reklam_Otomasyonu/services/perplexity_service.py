"""
Perplexity Service — Marka Araştırması
=======================================
Perplexity API ile marka/ürün araştırması yapar.
Sonuçları yapılandırılmış formatta döndürür.
"""

import requests

from logger import get_logger
from utils.retry import retry_api_call

log = get_logger("perplexity_service")

# Perplexity API timeout
REQUEST_TIMEOUT = 30

# Perplexity bilgi bulamadığında ürettiği metinde geçen tipik fraz örnekleri.
# Bunlardan biri varsa response "found=False" sayılır ve scenario_engine
# generic ton'a düşer (uydurma marka bilgisi senaryoyu zehirlemesin).
_NO_INFO_PATTERNS = (
    "bulamadım",
    "could not find",
    "no information",
    "not available",
    "fictional",
    "made up",
    "doğrulanmış bilgi yok",
    "kaynak bulunamadı",
    "kaynağa ulaşılamadı",
    "bilgi mevcut değil",
    "veri bulunamadı",
    "sources not available",
)


def _looks_like_no_info(text: str) -> bool:
    """Perplexity'nin "bulamadım" tarzı yanıtını tespit eder."""
    if not text:
        return True
    lower = text.lower()
    return any(p in lower for p in _NO_INFO_PATTERNS)


class PerplexityService:
    """Perplexity API ile marka/ürün araştırması."""

    def __init__(self, api_key: str, base_url: str = "https://api.perplexity.ai"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def research_brand(self, brand_name: str, product_name: str = "",
                       language: str = "tr") -> str:
        """
        Marka ve ürün hakkında güncel web araştırması yapar.

        Geriye string döner (geriye uyumluluk). Aynı zamanda son çağrının
        "found" durumu `self.last_found` üzerinden okunabilir; "bulamadım"
        pattern'i tespit edilirse scenario_engine generic ton kullanmalı.

        Args:
            brand_name: Marka adı
            product_name: Ürün adı (opsiyonel)
            language: Yanıt dili ('tr' veya 'en')

        Returns:
            str: Araştırma sonuçları (metin); bilgi bulunamadıysa "" dönebilir.
        """
        lang_note = "Yanıtını Türkçe ver." if language == "tr" else "Answer in English."

        product_part = f"ve '{product_name}' ürünü" if product_name else ""
        query = (
            f"'{brand_name}' markası {product_part} hakkında detaylı bilgi ver. "
            f"Şunları öğrenmek istiyorum:\n"
            f"1. Marka nedir, ne iş yapar?\n"
            f"2. Hedef kitlesi kim?\n"
            f"3. Ürün kategorisi ve fiyat aralığı\n"
            f"4. Markanın tonu ve kimliği (lüks, genç, spor vb.)\n"
            f"5. Rakipleri kimler?\n"
            f"{lang_note}\n"
            f"Bilgi bulamazsan açıkça 'doğrulanmış bilgi yok' olarak belirt - "
            f"uydurma cevap verme."
        )

        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sen bir marka araştırma asistanısın. Verilen marka hakkında "
                        "güncel, doğrulanmış bilgiler sun. Bilgi bulamazsan 'doğrulanmış "
                        "bilgi yok' diye belirt - asla uydurma."
                    ),
                },
                {"role": "user", "content": query},
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        content = self._call_perplexity(payload, brand_name)

        # Hallucination filtresi - "bulamadım" pattern'i varsa caller'a
        # bilgi yokmuş gibi davranması için sinyal ver.
        if _looks_like_no_info(content):
            log.warning(
                f"Perplexity '{brand_name}' icin dogrulanmis bilgi bulamadi "
                "(no-info pattern) - generic ton kullanilacak"
            )
            self.last_found = False
            # Geriye uyumluluk: caller `len(brand_research)` vb. kontrol edebilir;
            # boş string açık bir sinyal ki "marka araştırması yok".
            return ""

        self.last_found = True
        return content

    @retry_api_call(max_retries=2, base_delay=2.0, operation_name="Perplexity research")
    def _call_perplexity(self, payload: dict, brand_name: str) -> str:
        """Perplexity API çağrısı — retry mekanizmalı."""
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        # Güvenli erişim — eksik key'lerde KeyError önlenir
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"Perplexity boş yanıt döndü: {brand_name}")
        content = choices[0].get("message", {}).get("content", "")
        if not content.strip():
            raise RuntimeError(f"Perplexity boş content döndü: {brand_name}")

        log.info(f"Marka araştırması tamamlandı: '{brand_name}' — {len(content)} karakter")
        return content
