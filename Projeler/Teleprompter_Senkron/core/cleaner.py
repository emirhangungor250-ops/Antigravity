"""Script gövdesini prompter'da okunacak düz metne çevirir — AI ile.

Neden AI: kartlar tek tip değil (diyalog, quiz, anlatım, soru-cevap). Hangi satırın
kamerada söylendiği, neyin prodüksiyon notu/DM'i olduğu bir YARGI. Sabit kural/regex
bunu sessizce yanlış keser (kör otomasyon). Bu yüzden modele bırakılır.
AI çıktısındaki markdown kaçışları (\\_ , \\[) deterministik olarak ayrıca temizlenir.

Model: birincil OpenAI (varsayılan ucuz model, .env'deki OPENAI_MODEL ile değiştirilebilir).
Anahtar yoksa veya çağrı patlarsa otomatik Anthropic (Claude) fallback — pipeline asla
susmaz. Bu basit temizleme işi için küçük/ucuz bir model yeterlidir.
"""
from __future__ import annotations

import os
import re

import httpx

# Modeller .env'den okunur; varsayılanlar ucuz/küçük sınıf.
GPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
CLAUDE_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

def _openai_key() -> str | None:
    """OpenAI anahtarı — ÇAĞRI anında okunur (.env import'tan sonra yükleniyor)."""
    return os.getenv("OPENAI_API_KEY")

# NOT: Bu sistem prompt'u, script gövdesini prompter metnine çeviren ÇEKİRDEK desendir.
# Aşağıdaki KORU/ÇIKAR kuralları örnek bir içerik yapısına göredir; kendi script
# formatınıza (etiketler, platform kapanışları, kaldırmak istediğiniz bölümler) göre
# uyarlayın. Mantık aynı kalır: kamerada okunacakları koru, prodüksiyon/dağıtım notlarını çıkar.
SYSTEM = """Sen bir teleprompter editörüsün. Sana bir video script'inin sayfa gövdesi
(düz metin) verilir. Görevin: bunu, çekim sırasında prompterdan OKUNACAK temiz metne
çevirmek. Sadece nihai metni döndür, başka hiçbir şey yazma.

KORU (aynen bırak, çevirme, yeniden yazma, özetleme):
- Kamerada söylenecek/okunacak her cümle.
- Diyalog konuşmacı etiketleri (D1:, D2: gibi).
- Ekrandaki harf ipuçları (ör. "O _ _ _ _ _") — harf, alt çizgi ve boşluk dizilimini
  AYNEN koru; sayısını veya aralığını DEĞİŞTİRME.
- "Yanlış: ... → Doğru: ..." satırları.
- "BİTİŞ" gibi bitiş işaretleri.
- Platform kapanış cümleleri (söylenen alternatif kapanışlar) — hepsini bırak.

ÇIKAR (tamamen sil):
- "ilham:" / referans / kaynak linkleri, brief linkleri, her türlü URL.
- Hashtag/etiket notları (#... , "ETİKETLE", "@kullanici").
- Kalın/italik/renk işaretleri, ✅ ve diğer emojiler, gereksiz tırnaklar.
- "Soru:" gibi etiketler (soru metnini tut, etiketi at).
- Parantez içi prodüksiyon/sahne yönergeleri: (ekran kaydı), (Voice over), (yorgun...), (Açılış...) vb.
- Dağıtım/otomasyon bölümlerinin TAMAMI (ör. DM akışı, buton metinleri, gönderilecek mesajlar).
- Çekimle ilgisi olmayan panel/revizyon bölümleri ve altındaki her şey.
- "Shared with ..." gibi alt-sayfa referansları.

BİÇİM:
- "— — —" ayracını YALNIZCA kaynakta büyük boşluk (üst üste birden çok boş satır) veya
  divider çizgisi olan yere koy. Ardışık satırların/soruların/maddelerin arasına ASLA koyma.
- Ardışık boş satırları teke indir. Metni olduğu gibi koru; uydurma/ekleme yapma.
- Çıktı DÜZ METİN: başlık, kod bloğu, markdown işareti OLMASIN.
- Markdown KAÇIŞ karakteri kullanma: hiçbir karakterin önüne ters bölü (\\) koyma. Yani
  \\_ , \\[ , \\] DEĞİL; _ , [ , ] olduğu gibi kalsın.
- Okunacak hiçbir şey yoksa boş döndür."""

_ESCAPE_RE = re.compile(r"\\([_\[\]*`#.()+!>~\-])")


def _strip_md_escapes(text: str) -> str:
    """AI yer yer markdown kaçışı (\\_ , \\[) ekleyebiliyor — prompterda ters bölü görünmesin."""
    return _ESCAPE_RE.sub(r"\1", text)


def _via_gpt(raw: str, key: str) -> str:
    """OpenAI ile temizle. Boş/hatada exception fırlatır -> Claude'a düşülür."""
    r = httpx.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
        json={
            "model": GPT_MODEL,
            "max_completion_tokens": 4000,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": raw},
            ],
        },
        timeout=120,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"OpenAI HTTP {r.status_code}: {r.text[:300]}")
    text = (r.json()["choices"][0]["message"].get("content") or "").strip()
    if not text:
        raise RuntimeError("OpenAI boş döndü")
    return text


def _via_claude(raw: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content": raw}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def clean_script(raw_body: str) -> str:
    raw = raw_body.strip()
    text = ""
    key = _openai_key()
    if key:
        try:
            text = _via_gpt(raw, key)
        except Exception as e:  # OpenAI patlarsa sus, Claude'a geç
            print(f"  (OpenAI düştü, Claude'a geçildi: {str(e)[:120]})")
    if not text:
        text = _via_claude(raw)
    return _strip_md_escapes(text)
