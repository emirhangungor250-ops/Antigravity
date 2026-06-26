"""Claude Messages API wrapper — structured output için tool_use kullanılır.

Modeller:
- Sonnet 4.6 (`claude-sonnet-4-6`): transcript correction + analysis (hızlı, ucuz)
- Opus 4.7 (`claude-opus-4-7`): topic proposal + script generation (kalite)
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from core.config import Config

SONNET = "claude-sonnet-4-6"
OPUS = "claude-opus-4-7"
API_URL = "https://api.anthropic.com/v1/messages"


def _post(cfg: Config, model: str, system: str, messages: list[dict],
          tools: list[dict] | None = None, tool_choice: dict | None = None,
          max_tokens: int = 4096) -> dict:
    body: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        body["tools"] = tools
    if tool_choice:
        body["tool_choice"] = tool_choice
    r = httpx.post(
        API_URL,
        headers={
            "x-api-key": cfg.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=body,
        timeout=180,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"Anthropic HTTP {r.status_code}: {r.text[:400]}")
    return r.json()


def _extract_tool_result(response: dict, tool_name: str) -> dict:
    for block in response.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == tool_name:
            return block["input"]
    raise RuntimeError(f"Tool '{tool_name}' kullanılmadı. Response: {response.get('content')[:1] if response.get('content') else response}")


# ─── Stage 3: Correction & Analysis ──────────────────────────────────────

CORRECTION_GLOSSARY = """
Common HappyScribe misspellings to fix:
- "cloud" / "clawed" → "Claude" (in AI context)
- "anti gravity" / "anti-gravity" / "antigravity" → "Antigravity"
- "M C P" / "empty pee see" / "MCP server" → "MCP"
- "opus" → "Opus" (when referring to Claude Opus)
- "anthropic" → "Anthropic"
- "n8n" → "n8n" (keep lowercase)
- "cursor" → "Cursor" (when referring to the IDE)
- agent / subagent / multi-agent — keep as is
- tool use / tool calling — keep as is
"""


def correct_and_analyze(cfg: Config, raw_transcript: str, source_channel: str) -> dict:
    """Transcript düzelt + yapısal analiz tek çağrı."""
    tool = {
        "name": "transcript_analysis",
        "description": "Düzeltilmiş transcript + yapısal analiz",
        "input_schema": {
            "type": "object",
            "properties": {
                "corrected_transcript": {"type": "string", "description": "Düzeltilmiş tam transcript"},
                "language": {"type": "string", "description": "Tespit edilen ana dil (EN/DE/TR/diğer)"},
                "hook": {"type": "string", "description": "İlk 3 saniyenin hook cümlesi"},
                "main_topic": {"type": "string", "description": "Ana konu (1 cümle)"},
                "core_topic_match": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["Claude Code", "Antigravity", "MCP", "AI Agent"]},
                    "description": "Çekirdek konu havuzumuzdaki eşleşmeler (boş olabilir)",
                },
                "key_claims": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-7 madde: konuşmacının ortaya koyduğu temel iddialar/öğretiler",
                },
                "arc": {"type": "string", "description": "Yapı: hook → ... → outro şeklinde 1-2 cümle"},
                "self_promotion_segments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Konuşmacının kendi ürün/proje/CTA'sını öne çıkardığı kısımlar (lokalizasyonda BU KISIM ÇIKARILACAK)",
                },
            },
            "required": ["corrected_transcript", "language", "hook", "main_topic",
                         "core_topic_match", "key_claims", "arc", "self_promotion_segments"],
        },
    }
    system = (
        "Sen bir Türk içerik üreticisinin AI pipeline'ında çalışıyorsun. "
        "Görevin: İngilizce/Almanca bir AI/coding reels transkriptini (1) HappyScribe hatalarından temizlemek, "
        "(2) yapısal olarak analiz etmek.\n\n"
        f"GLOSSARY:\n{CORRECTION_GLOSSARY}\n\n"
        "Çekirdek konu havuzu: Claude Code, Antigravity, MCP, AI Agent. n8n bu havuzun DIŞINDA."
    )
    user = (
        f"Kaynak hesap: {source_channel}\n\n"
        f"Ham transcript:\n---\n{raw_transcript}\n---\n\n"
        "transcript_analysis tool'unu çağırarak analizi döndür."
    )
    resp = _post(cfg, SONNET, system, [{"role": "user", "content": user}],
                 tools=[tool], tool_choice={"type": "tool", "name": "transcript_analysis"})
    return _extract_tool_result(resp, "transcript_analysis")


# ─── Stage 4: Topic Proposal ─────────────────────────────────────────────

TOPIC_SYSTEM = """Sen <KULLANICI_ADI>'in (Türk AI içerik üreticisi) içerik pipeline'ının konu önerme katmanısın.

Yapacağın iş: Kaynak reels'ın analizine bakıp, <KULLANICI_ADI>'ın kendi kanalı için uyarlanmış Türkçe bir konu önerisi üreteceksin.

Kritik kurallar:
1. Lokalizasyon, çeviri değil. Kaynak kişinin bilgisini <KULLANICI_ADI>'ın tonuyla yeniden anlat. Kaynak kişinin projesini veya deneyimini <KULLANICI_ADI>'a sahiplenme.
2. CTA değer odaklı: video sonu <KULLANICI_ADI>'ın izleyiciye konu hakkında ücretsiz bir kaynak göndermesidir (kurulum komutu, resmi link, kısa rehber). "<TOPLULUK_ADI>", "topluluk", "topluluk", "kurs", "eğitim" gibi DOĞRUDAN marka tanıtımı YASAK. Marka değerle hatırlanır, tanıtımla değil.
3. Çekirdek konu havuzu: Claude Code, Antigravity, MCP, AI Agent. n8n YASAK (pozisyon dışı).
4. Eğer kaynak konu havuzla zayıf eşleşirse confidence skoru düşük ver (0-50 arası), gerekçesini açıkla — <KULLANICI_ADI> reddedebilir.
5. Türkçe başlık KISA olacak: ideal 3-5 kelime, hedef 25-30 karakter, sert üst sınır 40 karakter. Notion board card'ında tek bakışta okunabilmeli.
   ÖRNEK (iyi): "2 kişi, milyar dolar" · "Tasarımlar niye vasat?" · "5 kat fazla cevap"
   ÖRNEK (kötü, fazla uzun): "2 kişilik ekiple kurulan milyar dolarlık AI şirketi" · "Claude Code Tasarımların Neden Vasat Görünüyor"
   Filler kelimeleri at: "ile", "için", "nasıl", "neden", "yolu", "şirketi", "almak", "yapmak". Soru cümlesi veya cümle parçası olabilir.
6. Başlık ve hook önerisinde aynı dil kuralları geçerli: em-dash (—) YASAK, maks 15 kelime, ilkokul 5. sınıf öğrencisi anlayacak Türkçe, jargon yok (layout, motion, easing, pipeline, workflow, framework, tipografi vb. kelimeler başlıkta da yasak)."""


def propose_topic(cfg: Config, analysis: dict, source_channel: str, source_engagement: str = "") -> dict:
    tool = {
        "name": "topic_proposal",
        "description": "<KULLANICI_ADI> için lokalize Türkçe konu önerisi",
        "input_schema": {
            "type": "object",
            "properties": {
                "baslik": {"type": "string", "description": "Türkçe başlık, 3-5 kelime, ideal 25-30 karakter, üst sınır 40 karakter. Filler ('ile/için/nasıl/yolu/şirketi') at."},
                "konu_gerekcesi": {"type": "string", "description": "Bu konu <KULLANICI_ADI> için neden iyi (2-3 cümle, ürün dilinde)"},
                "hedef_konu": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["Claude Code", "Antigravity", "MCP", "AI Agent"]},
                },
                "confidence_skoru": {"type": "integer", "minimum": 0, "maximum": 100},
                "lokalize_hook_onerisi": {"type": "string", "description": "Türkçe hook (1-2 cümle)"},
                "uyari_notlari": {
                    "type": "string",
                    "description": "<KULLANICI_ADI>'ın dikkat etmesi gereken şey varsa (boş bırakabilirsin)",
                },
            },
            "required": ["baslik", "konu_gerekcesi", "hedef_konu", "confidence_skoru", "lokalize_hook_onerisi"],
        },
    }
    user = (
        f"Kaynak hesap: {source_channel}\n"
        f"Kaynak engagement: {source_engagement or 'N/A'}\n\n"
        f"Kaynak analizi:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        "topic_proposal tool'unu çağırarak öneri döndür."
    )
    resp = _post(cfg, OPUS, TOPIC_SYSTEM, [{"role": "user", "content": user}],
                 tools=[tool], tool_choice={"type": "tool", "name": "topic_proposal"})
    result = _extract_tool_result(resp, "topic_proposal")
    baslik = (result.get("baslik") or "").strip()
    if len(baslik) > 35:
        messages = [
            {"role": "user", "content": user},
            {"role": "assistant", "content": resp.get("content", [])},
            {"role": "user", "content": (
                f"Başlık '{baslik}' {len(baslik)} karakter — fazla uzun. "
                "Aynı tool'u tekrar çağır, başlığı 25-30 karaktere indir (max 40). "
                "İçerik aynı kalsın, filler kelimeleri at."
            )},
        ]
        resp2 = _post(cfg, OPUS, TOPIC_SYSTEM, messages,
                      tools=[tool], tool_choice={"type": "tool", "name": "topic_proposal"})
        result = _extract_tool_result(resp2, "topic_proposal")
    return result


# ─── Stage 5: Script Generation ──────────────────────────────────────────

SCRIPT_SYSTEM = """Sen <KULLANICI_ADI>'in reels script generator'ısın.

<KULLANICI_ADI>'ın stili: Sade Türkçe, kısa cümleler (max 15 kelime), em-dash YASAK, jargon YOK,
ürün dilinde.

Çıktın: Doğrudan kameraya konuşulacak bir reels script'i (40-90 saniye, ~120-220 kelime).
Akış: kısa açılış → konu anlatımı → ücretsiz kaynak teklifi.

SCRIPT METNİNE ETİKET KOYMA. "HOOK:", "KONU:", "CTA:" gibi başlıklar YASAK.
Sadece okuyacağı cümleler. Paragrafları boş satırla ayır (\\n\\n).

İKİ AŞAMALI YAZ:
1) Önce ham scripti yaz.
2) Sonra kendi metnine geri dön ve şu kontrolleri yap:
   (a) Tüm İngilizce/teknik terimleri çıkar veya Türkçeleştir. YASAK kelimeler: layout, spacing,
       tipografi, motion, easing, workflow, framework, pipeline, fine-tune, prompt engineering,
       deployment, render, B-roll, jump-cut. Hepsi günlük Türkçe karşılığıyla değiştir.
   (b) 15 kelimeden uzun cümleleri ikiye böl.
   (c) İlkokul 5. sınıf öğrencisi anlayacak mı? Anlaşılmayan tek bir kelime kalmasın.
   (d) Em-dash (—) tamamen YASAK. Onun yerine nokta veya virgül.

Style corpus: <KULLANICI_ADI>'ın eski 5 reels'ı verilecek. Ritmini ve hook tipini örnek al, kopyalama.

Lokalizasyon kuralı: Kaynak kişinin projesini/deneyimini sahiplenme. Kaynak kişinin BİLGİSİNİ
<KULLANICI_ADI>'ın ağzından anlat.

CTA KURALI (KRİTİK):
- "<TOPLULUK_ADI>", "topluluk", "topluluğum", "kursumda" gibi DOĞRUDAN marka tanıtımı YASAK.
- Video sonu = konu hakkında ücretsiz somut bir şey gönderme.
- Örnek doğru sonlar:
    "Bu üç eklentinin kurulum komutlarını yoruma KURULUM yazana DM atıyorum."
    "Bu MCP server'ın resmi linkini yoruma SERVER yazana göndereyim."
- Amaç: izleyici bilgi alır + somut kaynak alır. <KULLANICI_ADI>'ın markası tanıtımla değil değerle hatırlanır.
- Trigger kelimesi scriptin son cümlesinde mutlaka geçer.

Caption iki parça olacak:
- caption_hook: Tek satır, çok kısa, feed'de görünür (max 80 karakter, soru veya iddia).
- caption_body: Caption'ın "more" tıklanınca açılan devamı (2-4 cümle, em-dash yok).
  Burada da <TOPLULUK_ADI>/topluluk/topluluk DOĞRUDAN tanıtımı YASAK. Sadece "yoruma X yaz" tetik.
Disclaimer kod tarafında otomatik eklenir, sen YAZMA.

ManyChat akışı (tek ideal DM):
- manychat_trigger_word: Yoruma yazılacak tek kelime. Scriptteki tetik ile aynı.
  BÜYÜK harf, sade Türkçe, konu spesifik (örn. KURULUM, SERVER, REHBER, DETAY).
- manychat_message: Tek DM metni. ÖZET + LİNK kombinasyonu:
    1. Çok kısa selam.
    2. Konunun 3-5 maddelik EMOJI'li özeti. Her madde başında temalı emoji (örn. 🎨, ⚡, 🔧).
       Maddeler tek satır, max 1 cümle. Maddeler arası TEK satır kırma (\\n).
    3. Kısa kapanış.
  Em-dash yok. HTML etiketi (<br>, <p>, vb.) KESİNLİKLE YASAK — sadece \\n karakteri.
  <TOPLULUK_ADI>/topluluk/topluluk DOĞRUDAN tanıtım YASAK.
ManyChat butonları SEN ÜRETMEYECEKSİN. Pipeline asset listesinden (Stage 6'da web_search ile
bulunan gerçek + spesifik URL'lerden) otomatik üretip ekleyecek. Sen sadece message üret."""


def generate_script(cfg: Config, topic: dict, analysis: dict, style_corpus: list[dict]) -> dict:
    tool = {
        "name": "script_output",
        "description": "Lokalize Türkçe reels script + caption (hook+body) + süre",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "script": {
                    "type": "string",
                    "maxLength": 2400,
                    "description": "Okunacak script. Sadece konuşma metni. HOOK/KONU/CTA gibi başlık YASAK. Paragraflar \\n\\n ile ayrılır.",
                },
                "caption_hook": {
                    "type": "string",
                    "maxLength": 80,
                    "description": "Caption'ın ilk satırı — Instagram feed'de görünen kısa hook (max 80 char, em-dash yok).",
                },
                "caption_body": {
                    "type": "string",
                    "maxLength": 600,
                    "description": "Caption'ın devamı — 'more' açılınca okunan kısım (2-4 cümle, em-dash yok). Disclaimer ekleme, kod ekleyecek.",
                },
                "tahmini_sure_sn": {
                    "type": "integer",
                    "minimum": 20,
                    "maximum": 120,
                    "description": "Yaklaşık seslendirme süresi (saniye)",
                },
                "manychat_trigger_word": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 15,
                    "pattern": "^[A-ZÇĞIİÖŞÜ]+$",
                    "description": "Yoruma yazılacak tetik kelimesi (tek kelime, sadece büyük harf TR)",
                },
                "manychat_message": {
                    "type": "string",
                    "maxLength": 800,
                    "description": "DM metni: kısa selam + 3-5 emoji'li madde özet + kısa kapanış. Em-dash yok. <TOPLULUK_ADI>/topluluk/topluluk YASAK. HTML etiketi (<br>, <p>) YASAK — sadece \\n.",
                },
            },
            "required": [
                "script", "caption_hook", "caption_body", "tahmini_sure_sn",
                "manychat_trigger_word", "manychat_message",
            ],
        },
    }
    corpus_block = "\n\n".join(
        f"### Örnek {i+1}: {item['title']}\n{item['script_text'][:1200]}"
        for i, item in enumerate(style_corpus[:5])
    ) or "(örnek bulunamadı)"
    user = (
        f"## ONAYLI KONU\n{json.dumps(topic, ensure_ascii=False, indent=2)}\n\n"
        f"## KAYNAK ANALİZ (referans)\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        f"## STYLE CORPUS (top-5 benzer onaylı <KULLANICI_ADI> reels)\n{corpus_block}\n\n"
        "script_output tool'unu çağırarak script'i döndür."
    )
    resp = _post(cfg, OPUS, SCRIPT_SYSTEM, [{"role": "user", "content": user}],
                 tools=[tool], tool_choice={"type": "tool", "name": "script_output"},
                 max_tokens=4096)
    return _extract_tool_result(resp, "script_output")


# ─── Stage 6: Asset List ─────────────────────────────────────────────────

ASSET_SYSTEM = """Sen <KULLANICI_ADI>'ın 40-90 saniyelik reels'ı için editör arkadaşına EN İYİ 3-5 KAYNAĞI seçiyorsun.

GÖREVİN: Scriptte adı geçen spesifik isim/araç/kişi/proje için GERÇEK web kaynakları bul.
Önce web_search tool'u ile araştır. Sonra dönen sonuçlardan kaliteliyi seç. Sonunda asset_pool
tool'unu çağırarak final listeyi ver.

ZORUNLU İŞ AKIŞI:
1. Scriptte geçen 2-4 spesifik şeyi tespit et (kişi adı, ürün adı, repo adı vb.). Genel
   konular ("Claude Code", "AI") ARAMA — onlar editöre değer katmaz.
2. Her spesifik şey için web_search yap (örn. "Emil Kowalski motion design portfolio").
   YouTube videosu lazımsa sorguya "site:youtube.com" ekle.
3. Dönen sonuçlardan SADECE şu kalitedekileri seç:
   - Resmi proje sayfası (github.com/<user>/<repo>, kişinin kendi sitesi)
   - Kişinin/aracın kendi demosu (YouTube)
   - Resmi spesifik docs sayfası (ürünün spesifik bir özelliği için, jenerik landing değil)
4. Sonra asset_pool tool'unu çağır.

KESİN YASAKLAR:
- Generic landing page (örn. "Anthropic Claude Code resmi sayfası") YASAK. Editör bunu zaten bilir.
- "Editör şu screenshot'u alsın" tarzı talimatlar YASAK. Bu işi editör yapar.
- POV/desk shot önerileri YASAK. <KULLANICI_ADI> zaten kendi planını yapıyor.
- Halüsinasyon URL YASAK. SADECE web_search sonuçlarından gelen URL'i koy.
- Scriptte adı geçmeyen jenerik kaynak YASAK.

SAYI: 3-5 asset. Az ama nokta atışı. 5'i geçme.
TİP: Sadece "youtube" veya "web". screenshot/pov YOK.
AÇIKLAMA: "Bu nedir" tek cümle, en fazla 12 kelime."""


def generate_assets(cfg: Config, topic: dict, script: dict) -> dict:
    asset_tool = {
        "name": "asset_pool",
        "description": "EN İYİ 3-5 gerçek kaynak — sadece web_search ile bulduklarından",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "assets": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "sira": {"type": "integer", "minimum": 1, "maximum": 5},
                            "tip": {"type": "string", "enum": ["youtube", "web"]},
                            "aciklama": {
                                "type": "string",
                                "maxLength": 120,
                                "description": "Bu kaynak NE — tek cümle, max 12 kelime",
                            },
                            "url": {
                                "type": "string",
                                "pattern": "^https?://(?!.*youtube\\.com/results)(?!.*topluluk\\.com).+",
                                "description": "web_search'ten gelen GERÇEK URL. Halüsinasyon yasak. youtube.com/results ve topluluk.com YASAK.",
                            },
                        },
                        "required": ["sira", "tip", "aciklama", "url"],
                    },
                },
                "ozet": {"type": "string", "maxLength": 200, "description": "Editör için 1 cümle özet"},
            },
            "required": ["assets", "ozet"],
        },
    }
    web_tool = {"type": "web_search_20250305", "name": "web_search", "max_uses": 8}

    user = (
        f"## SCRIPT\n{script['script']}\n\n"
        f"## KONU\n{json.dumps(topic, ensure_ascii=False, indent=2)}\n\n"
        "Önce web_search ile scriptte adı geçen spesifik şeyleri araştır.\n"
        "Sonra asset_pool tool'unu çağırarak EN İYİ 3-5 kaynağı ver."
    )
    resp = _post(
        cfg, OPUS, ASSET_SYSTEM, [{"role": "user", "content": user}],
        tools=[asset_tool, web_tool],
        max_tokens=8192,
    )
    return _extract_tool_result(resp, "asset_pool")
