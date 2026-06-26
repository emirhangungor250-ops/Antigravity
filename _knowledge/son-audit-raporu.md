# 🔍 Antigravity Proje Audit Raporu

**Tarih:** 26 June 2026, 14:45  
**Taranan proje:** 36  
**Taranan dosya:** 532 (92,249 satır)  
**Toplam bulgu:** 170 (0 kritik, 133 uyarı, 37 bilgi)

> [!WARNING]
> 🟡 **133 uyarı** var — planlı düzeltme önerilir.

---

## 📊 Özet Tablo

| Proje | Tip | Dosya | Satır | Kritik | Uyarı | Bilgi | Durum |
|-------|-----|-------|-------|--------|-------|-------|-------|
| eCom_Reklam_Otomasyonu | python | 51 | 15,622 | 0 | 41 | 8 | 🟡 |
| Sesli_Asistan_Jarvis | python | 39 | 11,752 | 0 | 40 | 3 | 🟡 |
| LinkedIn_Video_Paylasim | python | 12 | 1,311 | 0 | 6 | 0 | 🟡 |
| Twitter_Video_Paylasim | python | 11 | 1,293 | 0 | 6 | 0 | 🟡 |
| LinkedIn_Text_Paylasim | python | 14 | 1,242 | 0 | 5 | 0 | 🟡 |
| Instagram_Carousel_Cron | python | 21 | 2,726 | 0 | 4 | 1 | 🟡 |
| Akilli_Watchdog | python | 9 | 2,760 | 0 | 3 | 2 | 🟡 |
| Personel_Mail_Hatirlatici | python | 17 | 2,249 | 0 | 3 | 1 | 🟡 |
| Sosyal_Performans_Bildirici | python | 12 | 1,242 | 0 | 3 | 0 | 🟡 |
| Twitter_Text_Paylasim | python | 19 | 3,236 | 0 | 3 | 0 | 🟡 |
| YouTube_Otomasyonu | python | 14 | 2,824 | 0 | 3 | 0 | 🟡 |
| Otonom_Kapak_Uretici | python | 13 | 2,667 | 0 | 2 | 3 | 🟡 |
| Proje_Dashboard | python | 21 | 3,831 | 0 | 2 | 2 | 🟡 |
| Sosyal_Video_ManyChat_Yazici | python | 9 | 1,474 | 0 | 2 | 1 | 🟡 |
| Tahsilat_Takip_Otomasyonu | python | 6 | 778 | 0 | 2 | 0 | 🟡 |
| AI_Website_Sablonu | other | 0 | 0 | 0 | 1 | 0 | 🟡 |
| Gelen_Teklif_Yanitlayici | python | 12 | 2,680 | 0 | 1 | 1 | 🟡 |
| Marka_Is_Birligi | python | 31 | 5,819 | 0 | 1 | 3 | 🟡 |
| Reklam_Fabrikasi | mixed | 5 | 915 | 0 | 1 | 2 | 🟡 |
| Shorts_Dizi_Fabrikasi | python | 26 | 3,671 | 0 | 1 | 2 | 🟡 |
| Web_Site_Satis_Otomasyonu | python | 4 | 655 | 0 | 1 | 1 | 🟡 |
| YouTube_Yorum_Otomasyonu | python | 19 | 1,894 | 0 | 1 | 0 | 🟡 |
| Youtube_Aciklama_Otomasyonu | python | 8 | 1,179 | 0 | 1 | 1 | 🟡 |
| Egitim_Gorsellestirme | other | 3 | 505 | 0 | 0 | 0 | 🟢 |
| Gizli_Video_Otomasyonu | python | 12 | 821 | 0 | 0 | 2 | 🟢 |
| Icerik_Yazari_Agent | python | 3 | 626 | 0 | 0 | 0 | 🟢 |
| Instagram_Asistan | node | 23 | 2,530 | 0 | 0 | 0 | 🟢 |
| Lead_Notifier_Bot | python | 5 | 926 | 0 | 0 | 0 | 🟢 |
| Otel_Danisma_Asistani | python | 13 | 2,249 | 0 | 0 | 1 | 🟢 |
| Reels_Script_Pipeline | python | 15 | 2,170 | 0 | 0 | 1 | 🟢 |
| Sheet_Tetikli_Mail_Yanitlayici | python | 6 | 445 | 0 | 0 | 1 | 🟢 |
| Teleprompter_Senkron | python | 7 | 485 | 0 | 0 | 1 | 🟢 |
| Whatsapp_Asistan | node | 19 | 3,076 | 0 | 0 | 0 | 🟢 |
| Whatsapp_Asistan_Isletme | node | 13 | 1,765 | 0 | 0 | 0 | 🟢 |
| Whatsapp_Onboarding | node | 38 | 4,656 | 0 | 0 | 0 | 🟢 |
| YT_Kopya_Sayfa | python | 2 | 175 | 0 | 0 | 0 | 🟢 |

---

## 🔎 Detaylı Bulgular

### 🟡 eCom_Reklam_Otomasyonu

*python projesi — 51 dosya, 15,622 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 144
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 685
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 752
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 782
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 811
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 826
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 850
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 912
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 977
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 984
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1015
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1028
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1055
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1062
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1071
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1084
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1153
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1291
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1331
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1372
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1379
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1395
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1437
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1793
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1800
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 1816
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ bare except: — tüm hataları yakalar, spesifik exception kullan — `railway_schema.py` satır 11
  - 💡 *logging.error('...', exc_info=True) kullan*
- ⚠️ except...pass — hata sessizce yutuldu — `railway_schema.py` satır 11
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `test_e2e_live.py` satır 31
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `test_e2e_live.py` satır 130
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `test_e2e_live.py` satır 135
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\production_pipeline.py` satır 145
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\production_pipeline.py` satır 212
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\production_pipeline.py` satır 233
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\production_pipeline.py` satır 1661
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\run_state.py` satır 50
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\run_state.py` satır 155
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\scenario_engine.py` satır 686
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\scenario_engine.py` satır 1012
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\scenario_engine.py` satır 1099
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `services\elevenlabs_service.py` satır 141
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ Büyük dosya: 2051 satır (bakım riski) — `main.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 547 satır (bakım riski) — `core\caption_generator.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 771 satır (bakım riski) — `core\conversation_manager.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 1769 satır (bakım riski) — `core\production_pipeline.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 1425 satır (bakım riski) — `core\scenario_engine.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 556 satır (bakım riski) — `core\url_data_extractor.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 1018 satır (bakım riski) — `services\kie_api.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 666 satır (bakım riski) — `services\upload_post_service.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Sesli_Asistan_Jarvis

*python projesi — 39 dosya, 11,752 satır*

**📦 Dependency**

- ⚠️ 11 paket versiyonsuz: `anthropic`, `openai`, `python-dotenv`, `httpx`, `fastapi`, `uvicorn`, `pydantic`, `websockets` (+3 daha) — `requirements.txt`
  - 💡 *Her paketin ardına ==X.Y.Z ekle (pip freeze ile versiyonları al)*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ab_testing.py` satır 288
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `actions.py` satır 62
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `actions.py` satır 81
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `calendar_access.py` satır 116
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `calendar_access.py` satır 222
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `evolution.py` satır 267
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `learning.py` satır 192
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `mail_access.py` satır 37
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `mail_access.py` satır 123
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `planner.py` satır 345
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `planner.py` satır 363
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `planner.py` satır 378
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `screen.py` satır 152
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `screen.py` satır 177
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `screen.py` satır 188
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `screen.py` satır 192
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `screen.py` satır 271
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ bare except: — tüm hataları yakalar, spesifik exception kullan — `server.py` satır 524
  - 💡 *logging.error('...', exc_info=True) kullan*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 524
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 615
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 670
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 678
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1079
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1106
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1150
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1244
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1274
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1433
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1455
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1557
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 1686
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 2556
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 2584
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `server.py` satır 2640
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `suggestions.py` satır 155
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `tracking.py` satır 184
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `work_mode.py` satır 143
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `helpers\get_events.py` satır 64
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `helpers\get_events.py` satır 83
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 764 satır (bakım riski) — `planner.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 2900 satır (bakım riski) — `server.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 LinkedIn_Video_Paylasim

*python projesi — 12 dosya, 1,311 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `env_loader.py` satır 68
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 112
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 173
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\typefully_publisher.py` satır 77
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Twitter_Video_Paylasim

*python projesi — 11 dosya, 1,293 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `env_loader.py` satır 68
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 112
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 173
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\typefully_publisher.py` satır 74
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 LinkedIn_Text_Paylasim

*python projesi — 14 dosya, 1,242 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 107
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 114
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\typefully_publisher.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Instagram_Carousel_Cron

*python projesi — 21 dosya, 2,726 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 138
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 23
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 56
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\slide_composer.py` satır 54
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ Büyük dosya: 526 satır (bakım riski) — `core\slide_composer.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Akilli_Watchdog

*python projesi — 9 dosya, 2,760 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `main.py` satır 174
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 71
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ Büyük dosya: 564 satır (bakım riski) — `alerter.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 553 satır (bakım riski) — `main.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Personel_Mail_Hatirlatici

*python projesi — 17 dosya, 2,249 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `services\groq_client.py` satır 46
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `services\groq_client.py` satır 54
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `services\groq_client.py` satır 92
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*

---

### 🟡 Sosyal_Performans_Bildirici

*python projesi — 12 dosya, 1,242 satır*

**📦 Dependency**

- ⚠️ 1 paket versiyonsuz: `apify-shared` — `requirements.txt`
  - 💡 *Her paketin ardına ==X.Y.Z ekle (pip freeze ile versiyonları al)*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 34
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 69
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Twitter_Text_Paylasim

*python projesi — 19 dosya, 3,236 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\typefully_publisher.py` satır 73
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 YouTube_Otomasyonu

*python projesi — 14 dosya, 2,824 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core\prompt_sanitizer.py` satır 362
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `infrastructure\replicate_merger.py` satır 174
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `infrastructure\video_downloader.py` satır 92
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Otonom_Kapak_Uretici

*python projesi — 13 dosya, 2,667 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core\ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\ops_logger.py` satır 70
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 710 satır (bakım riski) — `agents\reels_agent.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 581 satır (bakım riski) — `agents\youtube_agent.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Proje_Dashboard

*python projesi — 21 dosya, 3,831 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `run.py` satır 577
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `collectors\routines.py` satır 49
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 675 satır (bakım riski) — `run.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Sosyal_Video_ManyChat_Yazici

*python projesi — 9 dosya, 1,474 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core\notion_service.py` satır 247
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `core\notion_service.py` satır 256
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*

---

### 🟡 Tahsilat_Takip_Otomasyonu

*python projesi — 6 dosya, 778 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 35
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*
- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 71
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 AI_Website_Sablonu

*other projesi — 0 dosya, 0 satır*

**📄 README**

- ⚠️ README.md dosyası yok
  - 💡 *Projenin ne yaptığını, nasıl çalıştırıldığını anlatan bir README ekle*

---

### 🟡 Gelen_Teklif_Yanitlayici

*python projesi — 12 dosya, 2,680 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core\pipeline.py` satır 195
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py env okuyor ama fail-fast doğrulama yok — `config.py`
  - 💡 *Zorunlu env var'lar eksikse EnvironmentError fırlat*

---

### 🟡 Marka_Is_Birligi

*python projesi — 31 dosya, 5,819 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `ops_logger.py` satır 212
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 778 satır (bakım riski) — `src\contact_finder.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*
- ℹ️ Büyük dosya: 552 satır (bakım riski) — `src\notion_service.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Reklam_Fabrikasi

*mixed projesi — 5 dosya, 915 satır*

**📦 Dependency**

- ⚠️ Python projesi ama requirements.txt yok
  - 💡 *pip freeze > requirements.txt ile oluştur*

**🚫 .gitignore**

- ℹ️ .gitignore'da eksik: __pycache__ — `.gitignore`
  - 💡 *Ekle: __pycache__*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*

---

### 🟡 Shorts_Dizi_Fabrikasi

*python projesi — 26 dosya, 3,671 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core\config.py` satır 12
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*
- ℹ️ Büyük dosya: 506 satır (bakım riski) — `services\kie_omni.py`
  - 💡 *Dosyayı daha küçük modüllere bölmeyi düşün*

---

### 🟡 Web_Site_Satis_Otomasyonu

*python projesi — 4 dosya, 655 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `src\lead_generator.py` satır 133
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*

---

### 🟡 YouTube_Yorum_Otomasyonu

*python projesi — 19 dosya, 1,894 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `web\app.py` satır 121
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

---

### 🟡 Youtube_Aciklama_Otomasyonu

*python projesi — 8 dosya, 1,179 satır*

**📝 Logging**

- ⚠️ except...pass — hata sessizce yutuldu — `core\google_auth.py` satır 60
  - 💡 *En azından logging.warning('Hata: ...', exc_info=True) ekle*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*

---

### ℹ️ Gizli_Video_Otomasyonu

*python projesi — 12 dosya, 821 satır*

**🚫 .gitignore**

- ℹ️ .gitignore'da eksik: .env — `.gitignore`
  - 💡 *Ekle: .env*

**🏗️ Proje Yapısı**

- ℹ️ config.py env okuyor ama fail-fast doğrulama yok — `config.py`
  - 💡 *Zorunlu env var'lar eksikse EnvironmentError fırlat*

---

### ℹ️ Otel_Danisma_Asistani

*python projesi — 13 dosya, 2,249 satır*

**🏗️ Proje Yapısı**

- ℹ️ config.py env okuyor ama fail-fast doğrulama yok — `config.py`
  - 💡 *Zorunlu env var'lar eksikse EnvironmentError fırlat*

---

### ℹ️ Reels_Script_Pipeline

*python projesi — 15 dosya, 2,170 satır*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*

---

### ℹ️ Sheet_Tetikli_Mail_Yanitlayici

*python projesi — 6 dosya, 445 satır*

**🏗️ Proje Yapısı**

- ℹ️ config.py env okuyor ama fail-fast doğrulama yok — `config.py`
  - 💡 *Zorunlu env var'lar eksikse EnvironmentError fırlat*

---

### ℹ️ Teleprompter_Senkron

*python projesi — 7 dosya, 485 satır*

**🏗️ Proje Yapısı**

- ℹ️ config.py yok — env variable'lar dağınık olabilir
  - 💡 *Merkezi config.py oluştur, tüm env okumalarını orada topla*

---

## ✅ Temiz Projeler

- 🟢 **Egitim_Gorsellestirme** — Sorun bulunamadı (3 dosya, 505 satır)
- 🟢 **Icerik_Yazari_Agent** — Sorun bulunamadı (3 dosya, 626 satır)
- 🟢 **Instagram_Asistan** — Sorun bulunamadı (23 dosya, 2,530 satır)
- 🟢 **Lead_Notifier_Bot** — Sorun bulunamadı (5 dosya, 926 satır)
- 🟢 **Whatsapp_Asistan** — Sorun bulunamadı (19 dosya, 3,076 satır)
- 🟢 **Whatsapp_Asistan_Isletme** — Sorun bulunamadı (13 dosya, 1,765 satır)
- 🟢 **Whatsapp_Onboarding** — Sorun bulunamadı (38 dosya, 4,656 satır)
- 🟢 **YT_Kopya_Sayfa** — Sorun bulunamadı (2 dosya, 175 satır)

---

## 📈 Kategori Özeti

| Kategori | Kritik | Uyarı | Bilgi |
|----------|--------|-------|-------|
| 📝 Logging | 0 | 129 | 0 |
| 🏗️ Proje Yapısı | 0 | 0 | 35 |
| 📦 Dependency | 0 | 3 | 0 |
| 📄 README | 0 | 1 | 0 |
| 🚫 .gitignore | 0 | 0 | 2 |
