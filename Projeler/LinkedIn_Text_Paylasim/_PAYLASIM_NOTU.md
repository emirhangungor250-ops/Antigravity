# Paylaşım Notu — LinkedIn_Text_Paylasim

**Mod:** A (doğrudan ver)

## Ne yapıldı
- **Temizlenen sırlar:** Koda gömülü gerçek anahtar bulunmadı (config env-driven).
  - `ops_logger.py`, `scratch_notion_logs.py`, `scratch_notion_logs.js` — hardcoded Notion Ops Log DB ID defaultları kaldırıldı (artık boş, env'den okunur).
- **Scrub edilen kişisel veriler:**
  - `main.py` — docstring'deki kişi adı ("Dolunay mail'deki") → "yönetici mail'deki"
- **n8n workflows:** `n8n_workflows/*.json` içinde yalnızca n8n'in kendi node UUID'leri ve kimlik bilgisi *isimleri* var (gerçek değer yok) — temiz, olduğu gibi bırakıldı.
- **Yeni:** `.env.example` üretildi (proje önceden yoktu).

## Öğrenci ne yapmalı
1. `.env.example` → `.env` kopyala ve doldur:
   - `PERPLEXITY_API_KEY`, `OPENAI_API_KEY`, `KIE_API_KEY`
   - `TYPEFULLY_API_KEY`, `TYPEFULLY_SOCIAL_SET_ID` — LinkedIn yayını
   - `NOTION_SOCIAL_TOKEN`, `NOTION_X_DB_ID` — sosyal medya draft DB
   - `NOTION_DB_OPS_LOG` (opsiyonel) — merkezi log DB
2. `pip install -r requirements.txt` → `python main.py`.
3. n8n alternatifi isteniyorsa `n8n_workflows/` altındaki JSON'ları n8n'e import et ve kendi credential'larını bağla (`n8n_workflows/BURAYA_YUKLE.md` rehberi).
