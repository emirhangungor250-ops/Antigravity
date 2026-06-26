"""Ana ajan — tesis müşteri temsilcisi (Groq tool-calling).

Knowledge base yönlendirme + rezervasyon/fiyat doğrulama + müsaitlik tek bir
tool-calling döngüsünde birleşir. Araçlar: get_hotel_info, get_holiday, get_price.
Model: Groq openai/gpt-oss-120b (ucuz workhorse; maliyet politikası gereği Opus/Sonnet yasak).

Tesise özgü değerler (işletme adı, iletişim, grup eşiği) env'den okunur — bkz. config /
.env.example. Sistem promptu jeneriktir; kendi tesisinize göre BUSINESS_NAME ve iletişim
bilgilerini doldurmanız yeterlidir.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import hotelrunner
import holidays
import knowledge
import llm

log = logging.getLogger("hotel-chat.agent")
MAX_TURNS = 5

# --- Tesise özgü ayarlar (env'den) ------------------------------------------- #
# İşletmenin adı (botun kendini tanıttığı isim). Örn: "Deniz Resort & Spa".
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "tesisimiz")
# İletişim: rezervasyon/grup için yönlendirilecek telefon ve e-posta.
CONTACT_PHONE = os.getenv("CONTACT_PHONE", "<telefon>")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "<eposta>")
# Grup rezervasyonu eşiği (bu sayı ve üzeri kişi → grup ekibine yönlendir).
GROUP_THRESHOLD = int(os.getenv("GROUP_THRESHOLD", "20"))
# Çocuk yaş sınırı: bu yaş ve altı "çocuk", üzeri "yetişkin" sayılır.
CHILD_MAX_AGE = int(os.getenv("CHILD_MAX_AGE", "11"))

# Bilgi bulunamayınca tek kanonik fallback. main.py da bunu kullanır.
FALLBACK_TEXT = "Bu konu hakkında bilgim yok, ekip arkadaşlarımız en kısa sürede size dönüş yapacak."
GROUP_MSG = (f"{GROUP_THRESHOLD} ve üzeri kişi için grup rezervasyonu gerekiyor. "
             f"Lütfen {CONTACT_EMAIL} adresine yazın veya {CONTACT_PHONE} numarasını arayın.")


def _validate_booking(checkin: str, checkout: str, rooms: list[dict]) -> str | None:
    """get_price öncesi deterministik kapı. Geçersizse misafire iletilecek kısa uyarı
    (TR) döndürür; geçerliyse None. Böylece çıkış<=giriş, eksik yaş, grup eşiği gibi
    durumlar fiyat sorgulanmadan yakalanır."""
    try:
        d1 = datetime.strptime(checkin, "%Y-%m-%d").date()
        d2 = datetime.strptime(checkout, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "Tarihleri tam anlayamadım. Giriş ve çıkış tarihini gün/ay/yıl olarak yazar mısınız?"
    if d2 <= d1:
        return "Çıkış tarihi giriş tarihinden sonra olmalı. Doğru çıkış tarihini paylaşır mısınız?"
    total_adult = sum(int(r.get("adult_count") or 0) for r in rooms)
    total_child = sum(int(r.get("child_count") or 0) for r in rooms)
    if total_adult < 1:
        return "Konaklayacak yetişkin sayısını öğrenebilir miyim?"
    for r in rooms:
        cc = int(r.get("child_count") or 0)
        ages = r.get("child_ages") or []
        if cc > 0 and len(ages) != cc:
            return ("Çocuk sayısı ile yaşları eşleşmiyor. Her çocuğun yaşını paylaşır mısınız? "
                    f"({CHILD_MAX_AGE} yaş ve altı çocuk, {CHILD_MAX_AGE + 1} ve üzeri yetişkin sayılır.)")
    if (total_adult + total_child) >= GROUP_THRESHOLD:
        return GROUP_MSG
    return None


def _today_tr() -> str:
    return datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M")


# Sistem promptu jeneriktir; tesise özgü değerler ({business}, {phone}, {email},
# {child_max}, {child_adult}, {group}) çalışma anında env'den doldurulur. Tesise özgü
# POLİTİKA kurallarını (örn. pansiyon tipi, evlilik şartı, evcil hayvan) buraya kendiniz
# ekleyin veya knowledge_data altındaki bilgi tabanına yazın. Aşağıdaki "Tesise özgü
# politika" bölümü ÖRNEKTİR; kendi tesisinize göre düzenleyin ya da silin.
SYSTEM_TEMPLATE = """Rolün
- {business} müşteri temsilcisisin. Misafirle nazik, KISA ve RESMİ konuşursun.
- Bugünün tarihi ve saati (Europe/Istanbul): {now}

Genel kurallar
- Misafirin yazdığı DİLDE cevap ver (Türkçe gelirse Türkçe, İngilizce gelirse İngilizce vb.).
  Araç çıktıları (tesis bilgisi, fiyat özeti) Türkçe gelse bile cevabını misafirin diline çevirerek aktar.
  Dilden emin değilsen Türkçe kullan.
- Düz metin yaz. Kalın/markdown (**...**) KULLANMA. Tablo, kod, başlık kullanma.
- Cevaplar kısa ve öz olsun.
- "bugün", "yarın", "bu hafta sonu", "3 gün", "ayın 26'sı" gibi ifadeleri bugüne göre gerçek YYYY-MM-DD tarihine çevir.
- Yılı belirtilmeyen tarihleri bugünden sonraki en yakın tarihe göre yorumla (ay-gün geçmişse +1 yıl).
- KIRMIZI KURAL: Tesis hakkındaki HİÇBİR soruyu get_hotel_info aracını çağırmadan cevaplama. Tahmin yapma, bilgi uydurma.
- Bir konuda bilgi bulamazsan: "{fallback}" de.
- Misafir görsel gönderirse (mesaj "[Misafir bir görsel gönderdi: ...]" biçiminde gelir): görseli YALNIZCA tesis bağlamında değerlendir. Tesisle ilgiliyse (oda/tesis fotosu, tarih veya rezervasyon ekran görüntüsü) ona göre yardım et. Görselin içeriği tesisle ilgisizse görseldeki konuya KAPILMA; kibarca tesisle ilgili ne öğrenmek istediğini sor. Tesis dışı hizmet (sosyal medya, e-ticaret, ürün tanıtımı, tasarım vb.) ASLA önerme — sen yalnızca {business} müşteri temsilcisisin.

Tesise özgü politika (ÖRNEK — kendi tesisinize göre düzenleyin veya silin)
- (Örnek) Belirli konaklama tiplerinde özel belge/şart varsa burada belirtin.

Akış A — Rezervasyon / müsaitlik / konaklama fiyatı
- Zorunlu bilgiler: giriş tarihi, çıkış tarihi, yetişkin sayısı, çocuk sayısı, (çocuk varsa) çocuk yaşları.
- Çocuk varsa yaşlarını MUTLAKA öğren. {child_max} yaş ve altı çocuktur; {child_adult} ve üzeri yetişkin sayılır.
- Çocuk yaşı ay cinsinden verilirse aşağı yuvarlayarak yıla çevir (18 aylık → 1, 6 aylık → 0).
- "N kişi / N kişiyiz" yorumu: misafir AYRICA çocuktan bahsediyorsa N'yi YETİŞKİN say (çocuklar ayrıca sayılır). Örn "4 kişiyiz, bir de çocuk" = 4 yetişkin + 1 çocuk; "4 kişi, çocuk yok" = 4 yetişkin. "Çocuk bu sayıya dahil mi?" diye yeniden SORMA; bu yorumu kullan.
- Misafirin ZATEN söylediği bilgiyi (yetişkin/çocuk sayısı, çocuk yaşı, tarih) bir daha SORMA. Konuşma geçmişindeki değerleri hatırla ve kullan; yalnızca gerçekten eksik olanı (örn henüz söylenmemiş çocuk yaşı) sor. AYNI soruyu üst üste tekrarlama.
- Bir sayı yine de gerçekten belirsizse, en makul varsayımla TEK SEFER devam et ve fiyat cevabında varsayımını tek cümleyle belirt ("4 yetişkin ve 1 çocuk için ..."); misafir gerekirse düzeltir. Üst üste aynı soruyu sorup misafiri yorma.
- Bildirilen çocuk sayısı ile verilen yaş adedi eşit değilse get_price'ı ÇAĞIRMA; önce eksik yaşı sor.
- Çıkış tarihi giriş tarihinden sonra olmalı; aksi halde get_price'ı ÇAĞIRMA, doğru çıkış tarihini iste.
- Eksik/çelişkili bilgi varsa get_price'ı ÇAĞIRMA; önce eksik olanı kısaca sor.
- Misafir bir bayram/tatil zamanı geleceğini söylerse önce get_holiday ile tarih aralığını öğren, sonra o tarihlerle get_price çağır.
- Toplam kişi {group} veya üzeriyse grup rezervasyonu gerekir: "{group} ve üzeri kişi için lütfen {email} adresine yazın veya {phone} numarasını arayın."
- BİRDEN ÇOK AİLE/ODA: Misafir tek mesajda birden çok ayrı aile veya oda için fiyat isterse (örn "1. aile 3 yetişkin, 2. aile 2 yetişkin 1 çocuk"), hepsini TEK get_price çağrısında rooms dizisine ayrı eleman olarak koy. Araç her aileyi AYRI fiyatlar ve aile başına fiyatı döndürür; sen bu sonucu olduğu gibi, her ailenin kendi fiyatıyla aktar. Ailelere AYNI fiyatı verme, fiyatları birleştirme/uydurma.
- get_price sonucunu kullanarak müsaitse fiyatı kısaca bildir; müsait değilse uygun olmadığını söyle. Rezervasyon isterse {phone} numarasını ver.

Akış B — Tesis hakkında genel bilgi (oda, havuz/spa, yeme-içme, toplantı, konum, ulaşım, politikalar, günübirlik vb.)
- get_hotel_info aracını uygun kategoriyle çağır ve dönen bilgiye dayan.

Araç önceliği: 1) get_hotel_info  2) get_holiday  3) get_price
"""

PRICE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_price",
        "description": "Belirli tarihler ve misafir sayısı için müsaitlik + konaklama fiyatını "
                       "öğrenmek. Tüm zorunlu bilgiler (giriş, çıkış, yetişkin/çocuk, çocuk yaşları) "
                       "netse çağır.",
        "parameters": {
            "type": "object",
            "properties": {
                "checkin_date": {"type": "string", "description": "Giriş tarihi YYYY-MM-DD"},
                "checkout_date": {"type": "string", "description": "Çıkış tarihi YYYY-MM-DD"},
                "rooms": {
                    "type": "array",
                    "description": "Oda başına misafir. Tek oda ise tek elemanlı dizi.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "adult_count": {"type": "integer"},
                            "child_count": {"type": "integer"},
                            "child_ages": {"type": "array", "items": {"type": "integer"}},
                        },
                        "required": ["adult_count"],
                    },
                },
            },
            "required": ["checkin_date", "checkout_date", "rooms"],
        },
    },
}

TOOLS = [knowledge.TOOL_SCHEMA, holidays.TOOL_SCHEMA, PRICE_TOOL]


def _multi_family_quote(checkin: str, checkout: str, rooms: list[dict], state: dict) -> str:
    """Tek mesajda birden çok AYRI aile/oda sorulduğunda her birini AYRI fiyatlar.

    Çok-odalı sorguda hotelrunner.quote sadece prices['0']'i (ilk oda) okuyup tüm
    oda tiplerine aynı fiyatı veriyordu -> bot 3 farklı aileye aynı fiyatı söylüyordu.
    Burada her aileyi tek-odalı (doğrulanmış) quote yoluyla ayrı çağırıp aile başına
    en uygun fiyatı döndürüyoruz. quote()'un kendisine dokunmuyoruz (tek-oda yolu sağlam).
    """
    ci, co = hotelrunner._shift_past_dates(checkin, checkout)
    norm = hotelrunner._norm_rooms(rooms)
    nights = hotelrunner._day_count(ci, co)
    lines = []
    any_ok = False
    for fam in norm:
        label = hotelrunner._guest_summary([fam])
        try:
            res = hotelrunner.quote(ci, co, [fam])
        except hotelrunner.HotelRunnerError as e:
            log.warning("multi-family quote hata (%s): %s", label, e)
            lines.append(f"- {label}: fiyatı şu an getiremedim.")
            continue
        opts = res.get("rooms") or []
        if not res.get("available") or not opts:
            lines.append(f"- {label}: bu tarihlerde müsait oda bulunmuyor.")
            continue
        any_ok = True
        best = min(opts, key=lambda x: x["total"])
        meal = f" ({best['meal_plan']})" if best.get("meal_plan") else ""
        lines.append(f"- {label}: {best['name']}{meal} {hotelrunner.format_try(best['total'])} "
                     f"({nights} gece, toplam)")
    link = hotelrunner.booking_link(ci, co, norm)
    state["link"] = link
    head = (f"{hotelrunner._fmt_date(ci)} - {hotelrunner._fmt_date(co)} ({nights} gece) için "
            f"aile/oda başına en uygun fiyatlar:")
    return json.dumps({"available": any_ok, "summary": head + "\n" + "\n".join(lines),
                       "link": link}, ensure_ascii=False)


def _dispatch(name: str, args: dict, state: dict) -> str:
    """Bir aracı çalıştırır, sonucu string döndürür. Fiyat linkini state'e yazar."""
    try:
        if name == "get_hotel_info":
            return knowledge.get_hotel_info(args.get("category", ""))
        if name == "get_holiday":
            return holidays.get_holiday(args.get("name", ""))
        if name == "get_price":
            rooms = args.get("rooms") or [{"adult_count": 2, "child_count": 0, "child_ages": []}]
            ci, co = args.get("checkin_date", ""), args.get("checkout_date", "")
            err = _validate_booking(ci, co, rooms)
            if err:  # deterministik kapı: geçersiz girdide fiyat sorgulama, misafirden iste
                return json.dumps({"available": None, "summary": err}, ensure_ascii=False)
            if len(rooms) > 1:
                # Birden çok aile/oda: HER birini AYRI fiyatla. Çok-odalı motor sadece ilk
                # odayı (prices["0"]) fiyatlayıp herkese aynı fiyatı veriyordu; bu yol o hatayı atlar.
                return _multi_family_quote(ci, co, rooms, state)
            try:
                res = hotelrunner.quote(ci, co, rooms)
            except hotelrunner.HotelRunnerError as e:
                # Fiyat çekilemezse misafire 'araç hatası' değil, rezervasyon linki ver (/price ile aynı)
                log.warning("get_price quote hata: %s", e)
                link = hotelrunner.booking_link(*hotelrunner._shift_past_dates(ci, co),
                                                hotelrunner._norm_rooms(rooms))
                state["link"] = link
                return json.dumps({"available": None,
                    "summary": "Anlık fiyatı şu an getiremedim; güncel fiyat ve müsaitliği "
                               "rezervasyon bağlantısından görebilirsiniz.",
                    "link": link}, ensure_ascii=False)
            if res.get("link"):
                state["link"] = res["link"]
            # Ajana özet ver (tüm ham veriyi değil)
            return json.dumps({
                "available": res.get("available"),
                "summary": res.get("message"),
                "link": res.get("link"),
            }, ensure_ascii=False)
    except Exception as e:
        log.warning("tool %s hata: %s", name, e)
        return f"Araç hatası: {e}"
    return f"Bilinmeyen araç: {name}"


def respond(user_message: str, history: list[dict] | None = None) -> dict:
    """Misafir mesajına cevap üretir.

    Dönüş: {"text": <cevap>, "link": <rezervasyon linki|None>}
    """
    messages = [{"role": "system", "content": SYSTEM_TEMPLATE.format(
        now=_today_tr(), fallback=FALLBACK_TEXT, business=BUSINESS_NAME,
        phone=CONTACT_PHONE, email=CONTACT_EMAIL,
        child_max=CHILD_MAX_AGE, child_adult=CHILD_MAX_AGE + 1, group=GROUP_THRESHOLD)}]
    messages += (history or [])
    messages.append({"role": "user", "content": user_message})

    state: dict = {"link": None}
    for _ in range(MAX_TURNS):
        msg = llm.chat(messages, tools=TOOLS)
        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            return {"text": (msg.content or "").strip(), "link": state["link"]}
        # asistanın tool_call mesajını ekle
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ],
        })
        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _dispatch(tc.function.name, args, state)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "name": tc.function.name, "content": result})

    # Tur limiti: son bir kez araçsız özetletmeyi dene
    msg = llm.chat(messages, tools=None)
    return {"text": (msg.content or "").strip(), "link": state["link"]}
