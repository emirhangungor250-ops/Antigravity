"""LLM ile kişiselleştirilmiş Türkçe mail üret.

NOT: Aşağıdaki SYSTEM_PROMPT ve fallback şablonu örnek bir senaryoyla yazıldı
("formda yanlış telefon bırakan kişiye doğru numarayı isteme maili").
Kendi senaryona göre serbestçe değiştir — örn. randevu onayı, teşekkür maili,
eksik bilgi talebi, takip maili. Mailin amacı ve tonu tamamen senin elinde.

Mail metni LLM ile üretilir; OPENAI_API_KEY yoksa deterministik şablona düşülür.
"""
from __future__ import annotations
import json
import os
import requests
from typing import Dict

from config import OPENAI_API_KEY, OPENAI_MODEL, SENDER_NAME, SENDER_EMAIL

# Mailin amacını tek cümleyle özetler — .env'den özelleştirilebilir.
MAIL_PURPOSE = os.environ.get(
    "MAIL_PURPOSE",
    "Formda bıraktığı telefon numarasına ulaşılamayan kişiye, doğru numarayı "
    "bu maile cevap olarak iletmesini nazikçe rica et.",
)

SYSTEM_PROMPT = f"""Sen bir ekibin adına yazan, samimi ama profesyonel bir asistansın.
Görevin: Bir Google Sheet satırından gelen kişi bilgilerine bakarak %100 doğal
Türkçe bir mail yazmak.

Mailin amacı:
{MAIL_PURPOSE}

Kurallar:
- 60-100 kelime arası, tek paragraf veya 2 kısa paragraf.
- Emoji yok, abartılı satış dili yok, "değerli müşterimiz" gibi klişe yok.
- Kişiye adıyla hitap et.
- Kişinin işletmesi/ihtiyacı hakkında elindeki bilgiye 1 cümlelik HAFİF
  referans verebilirsin (abartıya kaçma).
- İmza ÇIKTIDA YAZMA — sistem ekleyecek.
- Türkçe karakterleri doğru kullan.

Çıktı formatı: SADECE şu JSON, başka metin yok:
{{"subject": "...", "body_text": "..."}}
"""


def _build_user_prompt(lead: Dict) -> str:
    parts = [
        f"İsim: {lead.get('name','')} {lead.get('surname','')}".strip(),
        f"İşletme/Marka: {lead.get('brand','')}",
        f"Rolü: {lead.get('role','')}",
        f"Personel sayısı: {lead.get('employees','')}",
        f"Form'da yazdığı ihtiyaç: {lead.get('need','')}",
    ]
    if lead.get("notes"):
        parts.append(f"İç not (mailde geçirme, sadece bağlam): {lead['notes']}")
    return "Bu kişiye yukarıdaki kurallara göre mail yaz:\n\n" + "\n".join(parts)


def _signature_text() -> str:
    return f"\n\nSevgiler,\n{SENDER_NAME}\n{SENDER_EMAIL}"


def generate_mail(lead: Dict) -> Dict[str, str]:
    """Lead için subject + body_text üret. LLM hata verirse template fallback."""
    if not OPENAI_API_KEY:
        return _template_fallback(lead)

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(lead)},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.6,
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        subject = (data.get("subject") or "").strip() or "Kısa bir not"
        body = (data.get("body_text") or "").strip()
        if not body:
            return _template_fallback(lead)
        return {
            "subject": subject,
            "body_text": body + _signature_text(),
        }
    except Exception as e:
        print(f"[mail_writer] LLM hatası ({e}), fallback template kullanılıyor.")
        return _template_fallback(lead)


def _template_fallback(lead: Dict) -> Dict[str, str]:
    name = lead.get("name") or "Merhaba"
    brand = lead.get("brand") or "işletmeniz"
    body = (
        f"Merhaba {name},\n\n"
        f"Başvurunuz için teşekkürler. {brand} için aramaya çalıştık "
        f"fakat formda bıraktığınız telefona ulaşamadık — sanırım küçük bir "
        f"yazım hatası olmuş olabilir.\n\n"
        f"Doğru numaranızı bu maile cevap olarak iletebilir misiniz? "
        f"Sizi en kısa sürede arayıp ihtiyacınızı dinlemek isteriz."
    )
    return {
        "subject": "Telefonunuza ulaşamadık",
        "body_text": body + _signature_text(),
    }
