# Paylaşım Notu — YT Kopya Sayfası

**Mod:** A (jenerikleştirme + kişisel referans temizliği)

Bu, **YouTube Yorum Cevaplayıcı** otomasyonuyla eşli çalışan bir "cevabı kopyala" sayfasıdır. Yorum cevaplayıcı projesi günlük bir mail atar; o maildeki butonun açtığı tek statik HTML sayfasını bu minik servis barındırır. Sayfa, önerilen yorum cevabını gösterir ve panoya kopyalar. Tek başına da anlamlıdır ama asıl değeri eşli cevaplayıcı projesiyle birlikte ortaya çıkar.

## Ne yapıldı

- **Temizlenen sırlar:** YOK. Bu projede hiçbir API anahtarı, token, e-posta, telefon, IBAN veya hardcoded ID yok. Kod tamamen Python stdlib (`http.server`) + tek statik HTML; sunucusuz (veri mail linkinin `#d=` hash'inde gelir, sunucuya hiç ulaşmaz).
- **Mutlak yol:** YOK. Kod `__file__`'a göre dinamik yol kullanıyor (`os.path.dirname(os.path.abspath(__file__))`); `Desktop/Antigravity` referansı bulunmadı.
- **Scrub edilen kişisel/sahibe-özel referanslar:**
  - `cevap_kopyala.html` — HTML yorumundaki sahibin canlı barındırma detayı (Supabase public bucket dosya yolu) kaldırıldı; mimari açıklaması kaldı.
  - `README.md` — sahibin iç repo yolu + fonksiyon adı (`Projeler/YT_Yorum_Cevaplayici/core/mail_report.py → make_copy_url()`) kaldırıldı; yerine eşli projenin sayfayı nasıl çağırdığı jenerik dille anlatıldı. Belirli host markası (Supabase) genel bir "bazı statik host'lar" ifadesine çevrildi.
- **`.env.example`:** Olduğu gibi bırakıldı — zaten gerçek değer içermiyor, sadece "bu servisin env var'ına ihtiyacı yoktur" açıklaması var. Bu servis çalışmak için hiçbir env var'ı istemez.

## Öğrenci ne yapmalı

1. **Doldurulacak `.env` YOK.** Servis env var'sız çalışır; `PORT`'u host sağlar (lokalde 8080). İstersen elle de çalıştırabilirsin: `python server.py` → tarayıcıda `http://localhost:8080`.
2. **Değiştirilecek dosya:** Sayfanın görünümünü/metnini değiştirmek istersen sadece `cevap_kopyala.html`'i düzenle. Sunucu mantığı sabit kalabilir.
3. **Eşli proje:** Bu sayfa tek başına boş açılır (veri mail linkinden gelir). Anlamlı çalışması için bir "YouTube Yorum Cevaplayıcı" tarafının bu sayfaya `#d=<base64 JSON>` hash'li link üretmesi gerekir. Eşli projeye bu servisin adresini tek bir ortam değişkeniyle (örn. `YT_COPY_PAGE_URL`) tanıt.
4. **Deploy (opsiyonel):** `railway.json` hazır (web servisi + `sleepApplication: true`, boştayken ≈$0). Kendi host hesabınla deploy edebilir veya lokalde çalıştırabilirsin.
