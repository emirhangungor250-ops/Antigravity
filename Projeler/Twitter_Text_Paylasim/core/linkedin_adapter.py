"""Twitter içeriğini LinkedIn tek-postuna dönüştürür.

X tarafında thread veya kısa tek tweet olan içerik, LinkedIn'de uzun-form,
boşluklu paragraflarla, hashtagsiz ve em-dash'siz şekilde yeniden yazılır.

Aynı LLMClient (Claude Opus 4.7) kullanılır — Twitter writer ile aynı ton/kural seti.
"""

import re

from ops_logger import get_ops_logger
from core.llm_client import LLMClient

ops = get_ops_logger("Twitter_Text_Paylasim", "LinkedInAdapter")


# NOT: Bu SYSTEM_PROMPT bir örnek stil rehberidir; kendi LinkedIn profilinize
# ve içerik nişinize göre uyarlayın.
SYSTEM_PROMPT = """Sen bu LinkedIn hesabı için içerik yazıyorsun. Aynı içerik
X'te (Twitter) farklı formatta paylaşıldı; senin görevin onu LinkedIn'in uzun-form
diline çevirmek.

═══ LINKEDIN PROFİLİ (örnek — kendi profiline göre değiştir) ═══
- Kitle: KOBİ sahipleri, yöneticiler, AI'ı işine entegre etmek isteyen profesyoneller
- Konu: AI, otomasyon, Claude Code, ManyChat, Make/n8n, B2B verim
- Ton: Eğitici, somut, dürüst. Reklam ya da satış dili YOK.

═══ LINKEDIN FORMAT KURALLARI ═══

1. UZUNLUK: 600-1300 karakter (sweet spot). Çok kısa olursa LinkedIn algoritması
   azaltır; 1500'ü aşarsa "...daha fazla göster" tıklaması düşer.

2. HOOK (1. satır): Kullanıcı feed'de SADECE 1-2 satır görüyor. İlk satır vurucu
   olmalı:
   - Somut sayı/iddia ("10 dakikada müşteri şikayetlerini 5 kat düşürün")
   - Ters köşe ("Çoğu KOBİ AI'ı yanlış kullanıyor")
   - Direkt vaad ("3 adımda Claude Code ile şu süreci otomatikleştireceğim")

3. YAPI: Boşluklu paragraflar.
   - Her paragraf 1-3 cümle
   - Paragraflar arası BOŞ SATIR (görsel nefes)
   - Numaralı liste varsa "1." "2." "3." şeklinde, her madde ayrı satırda
   - Mobilde okunabilirlik kritik

4. KAPANIŞ: Bir cümle özet veya soft CTA. "Hangisini denediniz?" / "Sizce de böyle mi?"
   tarzı yumuşak bağlama. Promosyon CTA'sı YASAK.

═══ YASAKLAR ═══
- Em-dash (—) HİÇBİR koşulda. Yerine nokta veya virgül.
- Hashtag YOK. (#AI, #Otomasyon vb. — hashtag'siz stil.)
- Emoji minimum: tüm postta MAX 1 emoji (hook'u güçlendiriyorsa). Listelerde madde
  işareti olarak emoji kullanma.
- Klişe LinkedIn ifadeleri YASAK:
  "Çok mutluyum paylaşmaktan", "ekibimle gurur duyuyorum",
  "yaratıcılığınızı konuşturun", "fark yaratın", "potansiyelinizi keşfedin",
  "devrim", "ilham", "büyüleyici", "geleceği şekillendirin", "sınırları zorlayın".
- Cümleler kısa. Tek cümlede max 15 kelime. İç içe yapı yok.
- "X postumda yazdığım gibi" / "thread'de anlattım" tarzı X-self-referans YASAK —
  LinkedIn postu kendi başına anlamlı olmalı.
- "Aşağıda thread var" / "Tweet'lerime bak" YASAK.

═══ ARAÇ ÖNCELİĞİ ═══
Thread'de hangi araç geçtiyse aynı sırayla: Claude Code > Claude Desktop
(kendi önerdiğin platformları ekle).
Make/n8n/Zapier sadece zorunluysa.

═══ İÇERİK SADAKATI ═══
Kaynak thread'in vaadini, somut adımlarını, araç adlarını AYNEN koru. Sadece
biçimi değiştir, bilgiyi DEĞİŞTİRME. Kaynakta olmayan özellik/sayı/araç UYDURMA.

═══ ÇIKTI ═══
Sadece LinkedIn post metni. JSON içinde "post_text" alanına koy.
Selamlama yok ("Merhaba!" yok). Direkt hook ile başla.
"""


SCHEMA = {
    "type": "object",
    "properties": {
        "post_text": {
            "type": "string",
            "description": "LinkedIn için hazır post metni. 600-1300 karakter ideal.",
        },
    },
    "required": ["post_text"],
    "additionalProperties": False,
}


_EM_DASH = re.compile(r"[ \t]*—[ \t]*")
_HASHTAG = re.compile(r"#\S+")


def _post_clean(text: str) -> str:
    """Son savunma: em-dash, hashtag, fazla boşluk temizliği."""
    if not text:
        return text
    cleaned = _EM_DASH.sub(", ", text)
    cleaned = _HASHTAG.sub("", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    return cleaned.strip()


class LinkedInAdapter:
    def __init__(self):
        self.llm = LLMClient()

    def adapt(self, *, source: str, source_url: str = "",
              thread_tweets: list[str] | None = None,
              tweet_text: str = "") -> str:
        """Thread veya tek tweet'ten LinkedIn postu üret.

        Returns: post_text (string). Üretilemezse boş string.
        """
        thread_tweets = thread_tweets or []
        if not thread_tweets and not tweet_text:
            return ""

        if thread_tweets:
            joined = "\n\n---\n\n".join(thread_tweets)
            kaynak_tip = f"X Thread ({len(thread_tweets)} tweet)"
        else:
            joined = tweet_text
            kaynak_tip = "X Tek Tweet"

        url_hint = f"\nKaynak URL: {source_url}" if source_url else ""
        user_msg = f"""KAYNAK TİPİ: {kaynak_tip}
İÇERİK KAYNAĞI: {source}{url_hint}

X İÇERİĞİ (aynen):
{joined}

GÖREV:
- Yukarıdaki içeriği LinkedIn'in uzun-form formatına çevir.
- Thread'in 1. tweet'indeki hook ve vaadi koru, ama LinkedIn'e uygun yeniden yaz.
- Numaralı adımlar varsa LinkedIn'de de numaralı madde olarak kalsın (her madde
  ayrı satırda, üst-alt boş satırlı blok).
- Kaynak URL varsa post sonuna kendi satırında ekle (sade, açıklamasız).
- Em-dash, hashtag, klişe LinkedIn ifadeleri yok.
- 600-1300 karakter hedefle. Aşırı kısaltma; aşırı uzatma.
"""
        try:
            data = self.llm.chat_json(
                system=SYSTEM_PROMPT,
                user=user_msg,
                max_tokens=2000,
                temperature=0.6,
                schema=SCHEMA,
            )
        except Exception as e:
            ops.error("LinkedIn adapt LLM exception", exception=e)
            return ""

        post_text = (data or {}).get("post_text", "").strip()
        if not post_text:
            ops.warning("LinkedIn adapt boş döndü")
            return ""

        cleaned = _post_clean(post_text)
        ops.info(f"LinkedIn varyantı üretildi ({len(cleaned)} char)")
        return cleaned
