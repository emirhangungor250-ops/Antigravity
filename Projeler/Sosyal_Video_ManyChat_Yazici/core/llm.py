"""Claude Messages API wrapper — ManyChat AKIŞI üretimi için.

İki aşama:
  1. generate_assets: LLM + native web_search → scriptte adı geçen şeylerin GERÇEK
     resmi URL'leri (halüsinasyon yok). Link butonları bu havuzdan, numara ile referanslanır.
  2. generate_flow: LLM → çok adımlı ManyChat sohbet akışı (açılış teaser + butonlar +
     gerekirse takip mesajları). Tarz kuralları agents/learnings.md'den gelir.

Model: cfg.model (.env'de MANYCHAT_MODEL; varsayılan ucuz/küçük). Model bulunamazsa (404)
FALLBACK_MODEL'e tek sefer düşer — pipeline asla model adı yüzünden susmaz.
"""

from __future__ import annotations

from typing import Any

import httpx

from core.config import Config

API_URL = "https://api.anthropic.com/v1/messages"
# Model bulunamazsa tek sefer bu modele düşülür. Kendi erişimin olan bir modeli yaz.
FALLBACK_MODEL = "claude-haiku-4-5"


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
        raise _ApiError(r.status_code, r.text[:400])
    return r.json()


class _ApiError(RuntimeError):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Anthropic HTTP {status}: {body}")


def _post_resilient(cfg: Config, system: str, messages: list[dict], **kw) -> dict:
    """cfg.model ile dene; model bulunamadıysa (404 / 'model') tek sefer 4.7'ye düş."""
    try:
        return _post(cfg, cfg.model, system, messages, **kw)
    except _ApiError as e:
        looks_model = e.status == 404 or "model" in e.body.lower()
        if looks_model and cfg.model != FALLBACK_MODEL:
            return _post(cfg, FALLBACK_MODEL, system, messages, **kw)
        raise


def _extract_tool_result(response: dict, tool_name: str) -> dict:
    for block in response.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == tool_name:
            return block["input"]
    raise RuntimeError(f"Tool '{tool_name}' kullanılmadı.")


# ─── Aşama 1: Asset listesi (web_search) ─────────────────────────────────────

ASSET_SYSTEM = """Sen bir sosyal video için ManyChat DM'inde link olarak paylaşılabilecek GERÇEK kaynakları topluyorsun.

GÖREVİN: Scriptte adı geçen spesifik araç/uygulama/site/kişi için GERÇEK web kaynakları bul.
Önce web_search ile araştır, sonra dönen sonuçlardan kaliteliyi seç, en sonda asset_pool tool'unu çağır.

ZORUNLU İŞ AKIŞI:
1. Scriptte geçen spesifik şeyleri tespit et (araç adı, uygulama, ürün, kişi, repo).
   Genel konular ("yapay zeka", "Claude") ARAMA. Sadece izleyiciye link olarak verilebilecek somut şeyler.
2. Her spesifik şey için web_search yap (örn. "Printify official site", "LawChat resmi", "MiniMax app").
3. Dönen sonuçlardan SADECE şunları seç:
   - Resmi ürün/uygulama/proje sitesi (aracın kendi sitesi, App Store / Google Play sayfası, github.com/<user>/<repo>)
   - Resmi spesifik özellik/docs sayfası
   - Scriptte adı geçen kişinin/projenin demosu veya başarı hikayesi sayfası (script o URL'i veriyorsa onu kullan)
4. Sonra asset_pool tool'unu çağır.

KESİN YASAKLAR:
- Halüsinasyon URL YASAK. SADECE web_search sonuçlarından (veya scriptte birebir verilen) URL'i koy.
- youtube.com/results gibi ARAMA SONUCU sayfaları YASAK (gerçek hedef değil).
- Scriptte adı geçmeyen jenerik kaynak YASAK.

ÖNEMLİ — BOŞ HAVUZ DURUMU:
- Eğer script kullanıcının KENDİ hizmetinden bahsediyorsa (kendi danışmanlığı, kendi sistemi)
  ve dışarıda linklenecek resmi bir araç YOKSA: boş liste döndür (assets: []). Uydurma link koyma.

EK BAĞLAM (varsa): Sana sayfa yorumları + marka brief'i verilebilir. İçinde GERÇEK bir affiliate/
indirim/resmi link varsa (örn. markanın verdiği özel kayıt linki) onu da asset olarak ekle.
Sadece orada BİREBİR verilen URL'i koy; uydurma yok. Ekip içi sohbet/isim asset değildir.

SAYI: 0-5 asset. Az ama nokta atışı. Aynı aracın hem sitesi hem store sayfası ayrı asset olabilir.
TİP: "youtube" | "web" | "appstore" | "playstore".
AÇIKLAMA: "Bu nedir" tek cümle, en fazla 12 kelime.
ÖNERİLEN_ETİKET: ManyChat link butonunda görünebilecek kısa isim, 2-4 kelime, marka/konu adı
  (örn. "Printify", "App Store", "Başarı Hikayesi"). Jenerik "Detay"/"Resmi sayfa" YASAK."""


def generate_assets(cfg: Config, video_name: str, script_text: str, extra_context: str = "") -> dict:
    asset_tool = {
        "name": "asset_pool",
        "description": "Scriptteki spesifik şeyler için 0-5 GERÇEK kaynak — sadece web_search ile bulunan veya scriptte birebir verilen URL'ler",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "assets": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "sira": {"type": "integer", "minimum": 1, "maximum": 5},
                            "tip": {"type": "string", "enum": ["youtube", "web", "appstore", "playstore"]},
                            "aciklama": {"type": "string", "maxLength": 120,
                                         "description": "Bu kaynak NE — tek cümle, max 12 kelime"},
                            "url": {"type": "string",
                                    "pattern": "^https?://(?!.*youtube\\.com/results).+",
                                    "description": "web_search'ten gelen (veya scriptteki) GERÇEK URL. Halüsinasyon yasak."},
                            "onerilen_etiket": {"type": "string", "maxLength": 25,
                                                "description": "Link butonunda görünebilecek kısa BENZERSİZ isim, 2-4 kelime."},
                        },
                        "required": ["sira", "tip", "aciklama", "url", "onerilen_etiket"],
                    },
                },
                "ozet": {"type": "string", "maxLength": 200, "description": "1 cümle özet (boş havuzsa neden)"},
            },
            "required": ["assets", "ozet"],
        },
    }
    web_tool = {"type": "web_search_20250305", "name": "web_search", "max_uses": 8}
    ctx = f"\n## EK BAĞLAM (yorumlar/brief — gerçek link/kupon olabilir)\n{extra_context}\n" if extra_context.strip() else ""
    user = (
        f"## VİDEO ADI (dahili takip, konuyu yansıtmayabilir)\n{video_name}\n\n"
        f"## SCRIPT\n{script_text[:3500]}\n"
        f"{ctx}\n"
        "Önce web_search ile scriptte adı geçen spesifik şeyleri araştır.\n"
        "Sonra asset_pool tool'unu çağırarak kaynakları ver (yoksa boş liste)."
    )
    resp = _post_resilient(cfg, ASSET_SYSTEM, [{"role": "user", "content": user}],
                           tools=[asset_tool, web_tool], max_tokens=8192)
    return _extract_tool_result(resp, "asset_pool")


# ─── Aşama 2: ManyChat AKIŞI ─────────────────────────────────────────────────

FLOW_SYSTEM = """Sen sosyal video (Instagram Reels / kısa video) için ManyChat DM AKIŞI yazıyorsun.

BAĞLAM: Video yayınlanınca altına yorum gelir. İzleyici tetik kelimesini yoruma yazınca ManyChat
ona otomatik DM atar. Bu DM tek mesaj DEĞİL, bir SOHBET AKIŞIDIR: bir açılış balonu + (gerekirse)
butona basınca açılan takip mesajları. Amaç: videodaki değeri (rehber, kupon, özellik, link)
sıcak ve adım adım ulaştırmak.

═══ AKIŞIN İSKELETİ (tarz: agents/learnings.md'den) ═══
• AÇILIŞ = ÇOK kısa merak/değer kancası (1-2 kısa cümle) + butonlar. Burada hızlıca ilgi çekiyoruz;
  her şeyi açılışta DÖKME, gereksiz kelime yok. Değeri takip mesajlarına yay.
  - Açılış tonları: merak ("Bunu ücretsiz anlatmamam lazım 🫣 ama yapıyorum…"),
    fayda vaadi ("Telefonunda emir ver, yapay zeka yapsın 👇"),
    düz tanıtım ("İşte Türkiye'nin hukuk yapay zekası 👇"),
    değer ("Sermayesiz kendi işini kurman için videoda anlattığım her şey 👇").
• BUTONLAR iki tip:
  - LINK butonu: bir araca/siteye/store'a gider. URL'i SEN yazmazsın; sana verilen KAYNAK
    HAVUZUNDAN numara (asset_ref) ile seçersin. Etiket kısa marka adı ("Printify", "MiniMax", "App Store").
  - DEVAM butonu: sohbeti açar, bir takip mesajına bağlanır (goto = o mesajın id'si). Etiketler
    konuşma dilinde: "Öğren", "Nasıl yani?", "Özellikleri Öğren", "Örnekleri Gör", "Biraz daha ara".
• TAKİP MESAJLARI asıl DEĞERİ taşır. Videonun vaadine göre şekil seçilir:
  - adım adım REHBER (1️⃣2️⃣3️⃣… numaralı) — video bir nasıl-yapılır anlatıyorsa
  - KUPON / indirim (ayrı, son mesajda, konuşma dilinde) — scriptte kod/indirim VARSA
  - ÖZELLİK listesi (🔹 veya ✳️ madde, ya da 1️⃣2️⃣3️⃣ numaralı) — araç tanıtılıyorsa
  - fiyat, store linkleri, kısa açıklama

═══ MADDE İŞARETİ (KRİTİK) ═══
Madde işareti olarak: sıralı adım için 1️⃣2️⃣3️⃣…, paralel madde için 🔹 veya ✳️ (ikisi de görünür emoji).
◇ ◆ ◊ ▸ ▹ • ● ○ ■ ‣ · * gibi GEOMETRİK karakterler Notion'da GÖRÜNMÜYOR. ASLA kullanma.

═══ BUTON SAYISI ═══
İHTİYACA GÖRE. Çoğu zaman 1. En fazla 3. ASLA doldurmak için 3'e tamamlama. Tek link yetiyorsa tek koy.
Aynı TEK aracın hem web sitesini hem iki app store'unu birden koyma; en uygun 1-2'sini seç (videoda
gösterilen yüzey hangisiyse o). Farklı HEDEFLER (site + başarı hikayesi + kupon gibi) ayrı buton olabilir.

═══ AKIŞ DERİNLİĞİ ═══
• Basit video (tek araç, tek link): TEK balon yeter — açılışta kısa anlatım + 1 link butonu, takip mesajı yok.
• Adım adım tutorial: açılış balonu komple numaralı rehber + 1 link butonu olabilir (tek balon).
• Kupon/indirim/derin özellik: açılış teaser + devam butonu → değer mesajı → (gerekirse) kupon/derin mesaj.
Akış 1 ile 4 balon arası olsun. Gereksiz balon ekleme; gereken değeri ver.

═══ TON ═══
Sıcak ama AZ KELİME. "sen" dili, ÇOK basit, kısa cümle (max 12 kelime). Gereksiz dolgu cümle yok;
her cümle bir iş yapsın. "Selam, konu çok basit." havası. İlkokul seviyesi sadelik.
Emoji ÖLÇÜLÜ kullan (👇🫣✨😎👋). KALP ailesi emoji (🫶 ❤️ 🥰 😍) varsayılan olarak kapalı (tarz tercihi).
Em-dash (—) YASAK. HTML etiketi YASAK.

═══ DÜRÜSTLÜK (KRİTİK) ═══
• Kupon kodu / indirim oranı / fiyat / sayı: SADECE scriptte VEYA brief'te VARSA. İkisinde de yoksa UYDURMA.
• ÇELİŞKİDE BRIEF KAZANIR: Markanın kontrol ettiği OLGULAR (indirim oranı, fiyat, resmi link, zorunlu
  ifade) script ile çelişirse BRIEF'teki değeri yaz, script'teki yanlış değeri DEĞİL.
  - Örnek: script "%15 indirim" ama brief "%12" diyorsa → "%12 indirim" yaz (markanın gerçek teklifi).
  - Script "INDIRIM26 kodu ile 2 ay ücretsiz" diyorsa → kodu aynen ver.
  - İndirim VAR ama somut KOD yoksa → "%X indirim" de, olmayan kod string'i UYDURMA
    ("indirim linkte hazır" gibi dürüst dille geç).
• Link YAZMA (http…). Linkler sadece LINK butonu olarak, kaynak havuzundan gelir. Mesaj metnine URL koyma.
• "Adım adım PDF hazırladım / özel doküman yazdım" gibi olmayan vaatler YASAK. Gerçek değeri ver.

═══ MARKA ═══
Topluluk/kurs/eğitim adını DOĞRUDAN pazarlama YASAK (yasak ifadeleri agents/learnings.md'ye yaz).
Değer ver, tanıtım kendiliğinden gelir. "Ücretsiz üyelik hediyem var" gibi değer-çerçevesi serbest.

═══ TETİK KELİMESİ ═══
Scriptin kapanışında söz verilen tetik (örn. GÖNDER, DENE, TATİL, GÖRSEL) VARSA onu kullan.
Yoksa konuya özel tek kelime, BÜYÜK harf, sade Türkçe türet.

═══ KAYNAK HAVUZU BOŞSA ═══
Link kaynağı yoksa (kullanıcının kendi hizmeti gibi): link butonu KULLANMA. Akışı değer/rehber üzerine
kur, devam butonlarıyla derinleştir veya butonsuz tek değer mesajı yaz.

═══ BAĞLANTI BÜTÜNLÜĞÜ ═══
Her DEVAM butonunun goto'su gerçek bir mesaj id'sine işaret etmeli. Her takip mesajı bir butondan
erişilebilir olmalı. Boşta mesaj veya boşta goto bırakma.

═══ EK BAĞLAM (yorumlar / marka brief) ═══
Sana sayfa yorumları ve/veya marka brief'i verilebilir. Bunlardan SADECE izleyiciye değer katan
GERÇEK bilgiyi al: kupon kodu, indirim oranı, fiyat, resmi link, marka adı, zorunlu marka ifadesi.
Ekip içi notları, kişi isimlerini (@...), üretim sohbetini KULLANMA, DM'e sızdırma.
Brief markanın RESMİ kaynağıdır: indirim oranı/fiyat/link script ile çelişirse BRIEF'i doğru kabul et.

═══ NOTLAR (kullanıcıya, kopyalamadan önce) ═══
Sadece emin OLMADIĞIN şeyler için not bırak (kullanıcı kopyalamadan önce kontrol etsin).
Her not ÇOK KISA ve ÇOK BASİT: tek cümle, EN FAZLA ~10 kelime. Jargon YASAK (UTM, string,
"bağlayıcı", "olgu" gibi kelimeler yok). Sıradan konuşma dili.
Ne zaman: brief ile script çelişti / indirim-kupon belirsiz / tetiği tahmin ettin / eksik bilgi.
Örnek: "İndirim %12 olmalı, videoda %15 geçiyor. Kontrol et."
Örnek: "Kupon kodu yok, indirim linkte."
Emin olduğun şeye not YAZMA. Yoksa boş bırak.

Sana ÖĞRENİLEN KURALLAR da verilebilir (kullanıcının geçmiş feedback'i). Onlara MUTLAKA uy.
manychat_flow tool'unu çağırarak akışı döndür."""


def _flow_tool() -> dict:
    button = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "label": {"type": "string", "minLength": 1, "maxLength": 25,
                      "description": "Butonda görünen kısa etiket"},
            "kind": {"type": "string", "enum": ["link", "continue"],
                     "description": "link=kaynağa gider | continue=takip mesajı açar"},
            "asset_ref": {"type": "integer", "minimum": 1, "maximum": 5,
                          "description": "kind=link için: kaynak havuzundaki asset'in sira numarası"},
            "goto": {"type": "string", "maxLength": 24,
                     "description": "kind=continue için: açılacak takip mesajının id'si"},
        },
        "required": ["label", "kind"],
    }
    message = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string", "minLength": 1, "maxLength": 24,
                   "description": "Bu mesajın benzersiz id'si (küçük harf slug, örn. 'kupon')"},
            "text": {"type": "string", "maxLength": 900,
                     "description": "Mesaj gövdesi. Satır kırma için \\n. URL/em-dash/HTML yok."},
            "buttons": {"type": "array", "maxItems": 3, "items": button},
        },
        "required": ["id", "text", "buttons"],
    }
    return {
        "name": "manychat_flow",
        "description": "Çok adımlı ManyChat DM akışı: tetik + açılış balonu + gerekirse takip mesajları",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "trigger_word": {
                    "type": "string", "minLength": 2, "maxLength": 15,
                    "pattern": "^[A-ZÇĞIİÖŞÜ]+$",
                    "description": "Yoruma yazılacak tetik (tek kelime, büyük harf TR). Scriptte söz verilen varsa o.",
                },
                "opening": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string", "maxLength": 900,
                                 "description": "Açılış balonu metni (kısa teaser; tek-balon akışta tam içerik)."},
                        "buttons": {"type": "array", "minItems": 1, "maxItems": 3, "items": button},
                    },
                    "required": ["text", "buttons"],
                },
                "messages": {
                    "type": "array", "minItems": 0, "maxItems": 4, "items": message,
                    "description": "Takip mesajları (0-4). Devam butonlarıyla goto üzerinden bağlanır.",
                },
                "notes": {
                    "type": "array", "maxItems": 3,
                    "items": {"type": "string", "maxLength": 90},
                    "description": "Kopyalamadan önce kontrol notu. ÇOK kısa+basit, tek cümle ~10 kelime, "
                                   "jargon yok. Sadece emin olmadığın şeyler. Yoksa boş liste.",
                },
            },
            "required": ["trigger_word", "opening", "messages"],
        },
    }


def _asset_pool_lines(assets: dict) -> str:
    rows = []
    for a in (assets.get("assets") or []):
        tip = a.get("tip") or "web"
        rows.append(f"[{a.get('sira')}] ({tip}) {a.get('aciklama')} | önerilen etiket: \"{a.get('onerilen_etiket') or ''}\"")
    if not rows:
        return "(BOŞ — bu video için linklenecek resmi kaynak yok. Link butonu kullanma.)"
    return "\n".join(rows)


def generate_flow(
    cfg: Config,
    video_name: str,
    script_text: str,
    assets: dict,
    *,
    existing_trigger: str | None = None,
    learnings_text: str = "",
    extra_context: str = "",
) -> dict:
    trig_hint = (
        f"\n## SCRIPTTE SÖZ VERİLEN TETİK\n{existing_trigger}\n(Bunu kullan.)\n"
        if existing_trigger else ""
    )
    learn_block = (
        f"\n## ÖĞRENİLEN KURALLAR (kullanıcı feedback'i — UY)\n{learnings_text}\n"
        if learnings_text.strip() else ""
    )
    ctx_block = (
        f"\n## EK BAĞLAM (yorumlar/brief — sadece gerçek değer bilgisini al, ekip notunu sızdırma)\n{extra_context}\n"
        if extra_context.strip() else ""
    )
    user = (
        f"## VİDEO ADI (dahili, konuyu yansıtmaz)\n{video_name}\n\n"
        f"## VİDEO SCRIPT'İ\n{script_text[:3800]}\n\n"
        f"## KAYNAK HAVUZU (link butonları SADECE bu numaralardan asset_ref ile seçilir)\n{_asset_pool_lines(assets)}\n"
        f"{trig_hint}{learn_block}{ctx_block}\n"
        "manychat_flow tool'unu çağırarak akışı döndür. Açılış ÇOK kısa kanca olsun; değeri "
        "takip mesajlarına yay (basit videoda tek balon yeterli). Buton sayısını ihtiyaca göre tut, az kelime."
    )
    resp = _post_resilient(cfg, FLOW_SYSTEM, [{"role": "user", "content": user}],
                           tools=[_flow_tool()], tool_choice={"type": "tool", "name": "manychat_flow"},
                           max_tokens=4096)
    return _extract_tool_result(resp, "manychat_flow")
