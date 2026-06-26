# RUNBOOK - Gelen Teklif Yanıtlayıcı

> Production'da bozulduğunda nereye bakılacağını anlatır. Geliştirme dokümanı: `README.md`.

## Ne yapar

Markalardan gelen iş birliği tekliflerini yakalar. İki gelen kutu (iş + kişisel) taranır.
LLM ile niteler; emin olunca gönderenin ağzından tanıştırma mailini otomatik gönderir
(yönetici CC). Şüpheli durumda taslak bırakır. Yöneticinin ağzından teklif taslakları
hazırlar; teklif ASLA otomatik gönderilmez.

## Servis kimliği

İki cron servisi (aynı projede önerilir):

- **yanıt cron'u** — Asıl otomasyon. Start: `python main.py`. Cron: periyodik (ör. birkaç saatte bir gündüz). Git push otomatik deploy eder (watchPattern açıksa).
- **denetim cron'u** — Bağımsız output audit (`review.py`). Cron: günlük. Start command servis ayarında `python review.py` olarak override edilir. Temizse sessiz; sorun bulursa tek uyarı maili (opsiyonel, Resend).
- **Komşular:** Gmail (3 hesap, OAuth), OpenAI direkt (gpt-4.1-mini), opsiyonel Notion portföyü, opsiyonel Firecrawl (site grounding), opsiyonel Resend (uyarı).

## Health check

- Yanıt cron log'unda her turda `=== Inbound Teklif Yanıt | DRY_RUN=...` başlık satırı görünür.
- İşlenen thread'ler Gmail'de `<LABEL_PREFIX>/*` etiketi alır (Islendi / OtoTanistirildi / TanistirmaTaslagi / TeklifHazir / IsbirligiDegil).
- Denetim cron log'unda `denetim: auto_kontrol=N missed_kontrol=N sorun=N` satırı + temizse `temiz — bildirim yok`.
- Cron platformunda iki servisin son çalışması SUCCESS.

## Hızlı triage (5 dakika)

1. Yanıt cron log'unda `[S1] HATA` / `[S2] HATA` / `Traceback` ara.
2. Hiç thread işlenmiyor → Gmail OAuth token'larından biri dolmuş olabilir. Log'da `token geçersiz, yenilenemiyor` ara; ilgili `GOOGLE_*_TOKEN_JSON`'u yenile.
3. Niteleme/yazım patlıyor → `OPENAI_API_KEY_DATA_SHARED` geçersiz veya günlük bedava kota bitti. Geçici olarak `OPENAI_API_KEY`'e (ücretli) düşer; o da yoksa LLM çağrıları hata verir.
4. Denetim maili gelmiyor ama sorun var şüphesi → review log'unda `ALERT_EMAIL_TO / ALERT_EMAIL_FROM / RESEND_API_KEY eksik` veya `Resend hata` ara.
5. Yanlış markaya otomatik tanıştırma gitti → acil fren: `AUTO_SEND_INTRO=0` (her şey taslak kalır) veya tam durdurma `DRY_RUN=1`. Israrcı ajansları `SENDER_BLOCKLIST`'e ekle.

## Sık karşılaşılan hatalar

### Gmail token süresi dolmuş
- **Belirti:** `token geçersiz, yenilenemiyor` veya `FileNotFoundError: ... token ne env ne dosya`.
- **Çözüm:** İlgili hesabın OAuth token'ını yenile (`oauth/` klasörü), production'da `GOOGLE_PRIMARY_TOKEN_JSON` / `GOOGLE_MANAGER_TOKEN_JSON` / `GOOGLE_PERSONAL_TOKEN_JSON` güncelle.

### Teklif taslağı referanssız çıkıyor
- **Sebep:** `NOTION_PORTFOLIO_DB_ID` boş ya da token DB'yi okuyamıyor.
- **Çözüm:** Portföy kullanmak istiyorsan DB ID + `NOTION_TOKEN`'ı kontrol et. Boşsa kasıtlıdır (referanssız teklif normaldir).

### Site grounding zayıf, niteleme genel kalıyor
- **Sebep:** `FIRECRAWL_API_KEY` yok veya kota bitti. Bot çalışmaya devam eder, ham title/meta'ya düşer.
- **Çözüm:** Anahtarı kontrol et. Acil değil; `vertical_confident=false` durumunda yanlış iddia riski zaten sıfırlanır.

### Denetim "kaçırılmış olabilir" diyor
- **Sebep:** Ya yanıt cron'u ölmüş (mailler birikmiş) ya da niteleme o thread'i atlamış.
- **Çözüm:** Önce yanıt cron'un son çalışmalarına bak. Cron sağlamsa thread'i elle değerlendir.

## Manuel çalıştırma

```bash
pip install -r requirements.txt
DRY_RUN=1 python main.py   # hiç göndermez/taslak yazmaz, sadece loglar
python review.py           # bağımsız denetim, tek tur
python tests/test_e2e.py   # deterministik testler + niteleme/yazım
```

Lokalde değerler `.env`'den (config.load_env) + `oauth/*.json`'dan okunur.

## Rollback

1. Git log'dan son SUCCESS commit'i bul.
2. `git revert <bozuk-commit>` → push (cron'lar otomatik deploy olur).
3. Kod rollback'i yetmezse acil fren env'leri: `DRY_RUN=1` veya `AUTO_SEND_INTRO=0`.

## Env var sözlüğü

| Env var | Ne işe yarar | Süresi dolar mı? |
|---|---|---|
| `SENDER_NAME` / `MANAGER_NAME` | Gönderen + yönetici görünen adı (imza) | Hayır |
| `SENDER_PRIMARY_EMAIL` / `SENDER_PERSONAL_EMAIL` / `MANAGER_EMAIL` | Üç Gmail hesabının adresi | Hayır |
| `GOOGLE_PRIMARY_TOKEN_JSON` | Gmail OAuth (iş kutusu) | Evet, yenilenir |
| `GOOGLE_PERSONAL_TOKEN_JSON` | Gmail OAuth (kişisel kutu) | Evet, yenilenir |
| `GOOGLE_MANAGER_TOKEN_JSON` | Gmail OAuth (yönetici, teklif taslağı) | Evet, yenilenir |
| `OPENAI_API_KEY_DATA_SHARED` | gpt-4.1-mini, data-shared anahtar | Hayır |
| `OPENAI_API_KEY` | Yedek OpenAI anahtarı (ücretli) | Hayır |
| `OPENROUTER_API_KEY` | Opsiyonel; sadece "/"-li model verilirse | Hayır |
| `FIRECRAWL_API_KEY` | Marka sitesini rendered okuma (grounding) | Hayır |
| `NOTION_TOKEN` / `NOTION_PORTFOLIO_DB_ID` | Portföy DB erişimi (opsiyonel) | Hayır |
| `RESEND_API_KEY` / `ALERT_EMAIL_TO` / `ALERT_EMAIL_FROM` | Denetim uyarı maili (opsiyonel) | Hayır |
| `PRICE_SHORT` / `PRICE_LONG` / `PRICE_BUNDLE` | Rate card fiyatları | - |
| `DRY_RUN` | 1 = hiç gönderme/taslak yok, sadece log | - |
| `AUTO_SEND_INTRO` | 0 = tanıştırma asla otomatik gitmez | - |
| `SCAN_DAYS` / `MAX_THREADS` | Tarama penceresi / tur başına limit | - |
| `OFFER_VARIANTS` | Teklif draft sayısı (1-3) | - |
| `QUALIFY_MODEL` / `WRITER_MODEL` / `INTRO_MODEL` | Model override | - |
| `SENDER_BLOCKLIST` | Ek kara liste (virgüllü domain/kelime) | - |

## Loglar nerede

- Cron platformunda ilgili servis → son çalışmanın deploy log'u. Yanıt cron'u her thread için `[S1]` / `[S2]` satırı yazar; denetim `denetim: ...` özet satırı yazar.
- Kalıcı log dosyası yok; Gmail etiketleri (`<LABEL_PREFIX>/*`) fiili durum kaydıdır.

## Maliyet notları

- İki hafif cron servisi.
- LLM: gpt-4.1-mini @ OpenAI direkt; data-shared anahtarla günlük kotaya kadar ücretsiz olabilir.
- Gmail etiketleri sayesinde her thread bir kez işlenir; tur başına az LLM çağrısı.
