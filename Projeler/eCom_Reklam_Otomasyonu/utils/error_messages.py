"""
Error Messages — Production hatalarını kullanıcı diline çeviren helper.
======================================================================
Ham log mesajı ("KieAI returned 503...", "ConnectionError: HTTPSConnectionPool...")
yerine kullanıcının ne yapacağını bilebileceği Türkçe aksiyon mesajları döner.

Kullanım:
    from utils.error_messages import categorize_production_error
    user_msg = categorize_production_error(result.get("error", ""))
"""
from __future__ import annotations


def categorize_production_error(error_raw: str) -> str:
    """Production failure'ı kullanıcı diline çevirir.

    Args:
        error_raw: Pipeline'dan gelen ham hata mesajı (log content, exception text).

    Returns:
        Türkçe, aksiyon önerili kısa kullanıcı mesajı.
    """
    if not error_raw:
        return "Beklenmedik bir sorun oldu. Linki kontrol edip tekrar dener misin?"

    err = str(error_raw).lower()

    # Network / servis
    if any(k in err for k in ["503", "504", "timeout", "timed out", "connection"]):
        return "Hizmetler şu an yoğun. Birkaç dakika sonra tekrar dener misin?"

    # Rate limit
    if any(k in err for k in ["429", "rate limit", "quota"]):
        return "API kotası geçici doldu. 5 dakika sonra tekrar dene."

    # Kredi / faturalama
    if any(k in err for k in ["credit", "insufficient", "kredi"]):
        return "Hizmet kredisi yetersiz. Yöneticiye haber verdim, kontrol edilecek."

    # Content policy / moderation
    if any(k in err for k in ["safety", "content policy", "moderation", "nsfw"]):
        return "Video içeriği platform kurallarına uymadı. Farklı ürün veya tarz dener misin?"

    # Auth / token
    if any(k in err for k in ["401", "403", "unauthorized", "invalid token", "voice_not_found"]):
        return "Servis kimlik doğrulaması başarısız. Yöneticiye haber verdim, kontrol edilecek."

    # 422 / validation
    if any(k in err for k in ["422", "validation"]):
        return (
            "Üretim parametreleri geçersiz görünüyor. Linki ve tarzı kontrol edip "
            "tekrar dener misin?"
        )

    # Default
    return "Üretim başarısız. Linki kontrol edip tekrar dener misin?"
