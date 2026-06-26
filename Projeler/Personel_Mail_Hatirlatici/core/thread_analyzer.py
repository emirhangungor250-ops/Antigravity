"""
Personel Mail Hatırlatıcı — Thread LLM Analizi
================================================
Groq LLM ile thread'lerin kategorisini ve durumunu analiz eder.

Çıktı: structured JSON — kategori enum + confidence + is_personalized.
Karar (digest'e girer mi?) bu modülde değil, core/decision.py'da verilir.

NOT: Aşağıdaki SYSTEM_PROMPT "marka işbirliği takibi" örneğiyle yazılmıştır.
Kendi senaryona göre serbestçe değiştir — örn. satış lead'leri, müşteri
talepleri, başvuru takibi. Kategori ENUM adlarını değiştirirsen
core/decision.py'daki COLLAB_CATEGORIES setini de güncelle.
"""

import logging
from typing import Dict, Any, Optional

from services.groq_client import analyze_thread

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Sen bir ekibin gelen kutusunu analiz eden bir asistansın. Sana bir e-posta thread'inin son mesajları gelir; sen bu thread'i sınıflandırırsın.

Bağlam:
- İzlenen hesap, ekibin dış ilişkilerini yürüten bir personele aittir.
- Bu sistem SADECE gerçek, aksiyon gerektiren iş yazışmalarını öne çıkarmak için kullanılır.
- Toplu/şablon promosyon mailleri, sipariş onayları, sistem bildirimleri, fatura, kişisel mailler ELENMELİ.

Görev: Aşağıdaki 8 kategoriden biriyle thread'i sınıflandır.

Kategoriler:
1. "brand_collab_offer" — Dış bir taraftan personele yapılan KİŞİSEL, yeni bir iş/işbirliği teklifi.
   Belirteçler: kişiye hitap, spesifik brief/talep, tarih, ücret veya barter teklifi, "size", "sizinle çalışmak istiyoruz".
2. "brand_collab_followup" — Önceden başlamış bir işin devamı (brief, onay, tarih konfirmasyonu, ödeme takibi).
3. "promotional_marketing" — Toplu marketing/kampanya/indirim mailleri. İçinde "fırsat", "iş ortaklığı" gibi kelimeler GEÇSE BİLE kişisel teklif değildir; toplu gönderilmiş, footer'ında "aboneliğinizden çıkın" linki vardır, kişiye özel hitap yoktur.
4. "transactional" — Fatura, sipariş onayı, kargo, ödeme, hesap doğrulama, şifre sıfırlama, randevu hatırlatma.
5. "system_notification" — LinkedIn/GitHub/Notion/Slack/YouTube gibi platformların otomatik bildirimleri.
6. "personal" — Arkadaş, aile, ekip içi yazışmalar; iş niteliği taşımayan kişisel mailler.
7. "newsletter" — Bülten, RSS digest, içerik dağıtım mailleri. İçinde sponsor reklamı geçse bile bu kişisel teklif değildir.
8. "unclear" — Hiçbirine net şekilde uymayan, eksik bilgi içeren mailler.

ÖNEMLİ KURALLAR:
- "is_personalized" = true SADECE şu durumda: mail personele bizzat hitap ediyor, ona/ekibine özel bir teklif/talep içeriyor. Toplu mail tonu ("Merhaba değerli üyemiz", isimsiz veya jenerik selamlama) → false.
- "brand_collab_offer" veya "brand_collab_followup" sadece is_personalized=true ise olabilir. Toplu kampanya maili ne kadar "işbirliği" kelimesi geçirse de promotional_marketing'tir.
- "confidence": 0.0–1.0 arası, kategori kararındaki güvenin. Şüphe varsa düşük (≤ 0.5) ver, "unclear" da seçebilirsin.

ÖRNEKLER:

Örnek 1 (POZİTİF):
Konu: "Eğitim Kampanyamız Hakkında"
İçerik: "Merhaba, sizinle bir reklam kampanyası planlıyoruz. Kasım ayında 2 içerik karşılığı bir teklif sunmak istiyoruz. Brief'i ekte paylaşıyorum."
Beklenen:
{"category":"brand_collab_offer","confidence":0.95,"is_personalized":true,"brand_name":"Örnek Şirket",...}

Örnek 2 (NEGATİF — toplu):
Konu: "🎯 Yeni Fırsatlar Aboneler İçin"
İçerik: "Sevgili abonemiz, bu hafta platformumuza 5 yeni ortak katıldı. Başvuru için butona tıklayın. [Aboneliğinizden çıkın]"
Beklenen:
{"category":"promotional_marketing","confidence":0.93,"is_personalized":false,"brand_name":null,...}

Örnek 3 (NEGATİF — transactional):
Konu: "Fatura #INV-2024-9821 hazır"
İçerik: "Sayın müşterimiz, Ekim ayı faturanız hazırdır. Tutar: 1.250 TL."
Beklenen:
{"category":"transactional","confidence":0.99,"is_personalized":false,"brand_name":null,...}

Şimdi sana verilen thread için SADECE şu JSON'u döndür, başka bir şey yazma:

{
  "category": "brand_collab_offer" | "brand_collab_followup" | "promotional_marketing" | "transactional" | "system_notification" | "personal" | "newsletter" | "unclear",
  "confidence": 0.0,
  "is_personalized": true/false,
  "brand_name": "Karşı taraf adı veya null",
  "last_sender": "brand" | "staff" | "other",
  "action_needed_by_staff": true/false,
  "thread_status": "active" | "closed" | "waiting_for_brand" | "responded_by_staff",
  "reason": "Kısa Türkçe açıklama (max 120 karakter)"
}

Kurallar:
- "last_sender": Thread'deki SON mesajı kim attı? "staff" = izlenen personel, "brand" = dış taraf, "other" = bilinmeyen.
- "action_needed_by_staff": true SADECE last_sender=brand ve dış tarafın net bir cevap/aksiyon beklediği durumda.
- "thread_status":
  - "responded_by_staff" = Son mesajı personel attı, karşı tarafın cevabı bekleniyor.
  - "waiting_for_brand" = Personel bir şey istedi/teklif etti, karşı taraf cevap vermedi.
  - "active" = Devam eden aktif konuşma, personelin cevap vermesi bekleniyor.
  - "closed" = İş reddedildi, iptal, tamamlandı.
"""


def analyze(thread_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Tek thread'i LLM ile analiz et. Sonuca thread meta'sını ekleyip döner.
    """
    snippets = thread_data.get("message_snippets", [])
    if not snippets:
        logger.debug(f"Thread {thread_data['thread_id']}: snippet yok, atlanıyor")
        return None

    thread_text = f"Konu: {thread_data['subject']}\n"
    thread_text += f"Katılımcılar: {', '.join(thread_data['participants'])}\n"
    thread_text += f"Mesaj sayısı: {thread_data['message_count']}\n"
    thread_text += "\n---\n\n"
    thread_text += "\n\n---\n\n".join(snippets)

    result = analyze_thread(thread_text, SYSTEM_PROMPT)
    if result is None:
        logger.warning(f"Thread {thread_data['thread_id']} LLM analizi başarısız")
        return None

    # Thread meta bilgisini sonuca ekle
    result["thread_id"] = thread_data["thread_id"]
    result["subject"] = thread_data["subject"]
    result["gmail_link"] = thread_data["gmail_link"]
    result["last_message_date"] = thread_data["last_message_date"]
    result["last_sender_email"] = thread_data["last_sender_email"]
    result["message_count"] = thread_data["message_count"]

    logger.info(
        f"LLM: '{thread_data['subject'][:50]}' → "
        f"{result.get('category')} (conf={result.get('confidence')}, "
        f"personal={result.get('is_personalized')}, sender={result.get('last_sender')})"
    )
    return result
