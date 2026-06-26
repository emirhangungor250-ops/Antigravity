# Paylasim Notu — fatura-olusturucu

**Mod:** A (+ hassas veri sablonlamasi)

## Ne yapildi
- `result.json` — gercek Gmail yazismasi (isim, eposta, surukleyici icerik) iceriyordu; jenerik ornek sablona indirildi.
- `fatura_rehberi.json` — gercek musteri/marka kayitlari (sirket, adres, eposta, tutar) iceriyordu; tek jenerik ornek satira indirildi.
- `fatura-ornekler/` ve `uretilen-faturalar/` — sahibin gercek fatura PDF'leri (isim, adres, banka bilgisi) iceriyordu; klasorler bos birakildi, aciklayici placeholder dosya kondu.
- `parse_pdf.py` — hardcoded mutlak dosya yolu kaldirildi, arguman tabanli hale getirildi.
- `SKILL.md` — kisiye ozel sosyal medya handle'i `<INVOICE_HANDLE>` env referansina, hardcoded mutlak yol relative yola cevrildi.
- `faturalastir.py` ve `eposta_fatura_oku.py` zaten env-driven; degisiklik gerekmedi.

## Ogrenci ne yapmali
- `.env` dosyasi olusturup `.env.example`'daki `INVOICE_*` degiskenlerini kendi bilgilerinizle doldurun.
- `fatura_rehberi.json` icindeki ornek satiri silip kendi kayitlarinizla doldurun (otomatik da dolar).
- E-posta modu icin merkezi Google OAuth token kurulumu gerekir (`_knowledge/credentials/oauth/`).
