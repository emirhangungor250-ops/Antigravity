# Web_Site_Satis_Otomasyonu

Web sitesi olmayan lokal işletmeleri Apify Google Maps scraper ile bulup, Notion onay kokpitine düşüren ve onaylanan adaylara demo subdomain üzerinden web sitesi üretmeyi hedefleyen otomasyon. Şu an MVP aşamasında: lead toplama + Notion'a yazma çalışıyor; demo üretim + Netlify deploy adımı planlama aşamasında.

## Stack
Python 3, Apify (Google Maps scraper), Notion API, (planlanan) Netlify API, Gemini/Groq LLM (skorlama).

## Çalışma Şekli
Manuel tetik (henüz cron değil): `python3 src/lead_generator.py` çalıştırılır.
1. Apify üzerinden hedef sektör + bölge için Google Maps verisi çekilir (`APIFY_ACTOR_ID = nwua9Gu5YrADL7ZDj`).
2. Web sitesi olmayan veya zayıf siteleri olan adaylar filtrelenir, skorlanır.
3. Eşik üstü adaylar (`SCORE_THRESHOLD_MIN=50`) Notion Lead Onay DB'ye yazılır.
4. Notion'da kullanıcı "Üret" tikini atınca demo üretim akışı tetiklenecek (henüz devrede değil).

Detaylı plan: `IMPLEMENTATION_PLAN_v2.md`.

## Environment Setup
Ortam değişkenleri için `.env.example`'a bak. Doldurman gerekenler:
- `APIFY_API_KEY_1` — Birincil Apify token (zorunlu)
- `APIFY_API_KEY_2` — Quota fail-over için ikincil token
- `NOTION_API_TOKEN` — Notion Internal Integration token (Lead Onay DB'ye yazılı erişim)
- `NOTION_LEAD_DB_ID` — Lead Onay DB ID (ilk çalıştırmada üretilip set edilir)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — Opsiyonel ANA logger; yoksa sessiz disabled

## Deploy
Şu an deploy yok — lokal çalışıyor. Notion onay akışı stabilleşince Railway cron'a alınacak. Son güncelleme: 2026-05-07.
