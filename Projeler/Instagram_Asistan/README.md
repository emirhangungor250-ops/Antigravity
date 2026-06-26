# Instagram DM Asistanı

Instagram DM'leri karşılayıp ManyChat Instagram channel üzerinden cevap üreten asistan şablonu. RAG (knowledge base + video transcript) + LLM router + burst coalescing pattern'lerini içerir.

## Yapı

- **F1**: 24h / 10 mesaj per-subscriber rate limit (Supabase `ig_rate_limits`).
- **F2**: Burst coalesce (per-subscriber lock + debounce, WhatsApp Asistan paraleli).
- **F3**: Dinamik LLM router — Haiku intent classifier → quick_response veya Sonnet deep.
- **F4**: Sabit refuse mesajları + alternatif yönlendirme (CTA).
- **RAG-A**: Markdown KB (`knowledge_chunks` tablosu).
- **RAG-B**: Notion video transcript RAG (`ig_video_chunks`).

## Stack

Node 20 · Express · Anthropic SDK (Haiku + Sonnet) · OpenAI embeddings · Supabase pgvector · Resend (eskalasyon mail).

## Klasör

```
config/env.js          # required env'ler + defaults
utils/logger.js
utils/sanitize.js      # banned phrases + hard fallback
services/
  ai_engine.js         # orchestrator (rate→intent→RAG→Sonnet→sanitize)
  intent_router.js     # cheap Haiku classifier
  ai_cheap.js
  ai_expensive.js
  kb_factory.js        # RAG-A
  kb_videos.js         # RAG-B
  notion_videos.js     # Notion DB scan + page body parse
  rate_limiter.js
  manychat.js
  memory.js
  escalation.js
  language_detector.js
scripts/
  sync_notion_videos.js
  test_intent_router.js
  test_rate_limit.js
  test_burst_coalesce.js
supabase/migrations/20260517000000_init_instagram_asistan.sql
```

## Setup

1. `.env` doldur (`.env.example` referans):
   - `MANYCHAT_TOKEN`, `MANYCHAT_FIELD_ID`, `MANYCHAT_FLOW_ID`
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY` (embedding)
   - `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
   - `NOTION_TOKEN` + `NOTION_VIDEO_DB_ID`
   - `RESEND_API_KEY` + `ADMIN_EMAIL`
   - `INSTAGRAM_WEBHOOK_SECRET` + `ADMIN_SECRET`
2. `npm install`
3. Supabase migration: `supabase/migrations/20260517000000_init_instagram_asistan.sql` uygulanmış olmalı.
4. RAG-A seed: `curl -X POST $URL/admin/seed-kb-factory -H "x-admin-key: $ADMIN_SECRET"` (KB markdown'ı kendi içeriğinden gönder).
5. RAG-B initial sync: `npm run sync:videos:full`
6. `npm start`

## ManyChat Flow

Instagram channel'da yeni flow:
- Trigger: "Default Reply" + "Conversation Started"
- Action: External Request
  - URL: `{RAILWAY_URL}/webhook/instagram`
  - Method: POST
  - Body: `{ "kullanici_id": "{{user_id}}", "last_text_input": "{{last_input_text}}", "ig_username": "{{username}}" }`
  - Header: `x-webhook-secret: $INSTAGRAM_WEBHOOK_SECRET`

Kod `setCustomField` + `sendFlow` ile cevabı ManyChat'e geri yazar.

## Deploy (Railway)

- `rootDirectory: Projeler/IG_Asistan` (Railway dashboard'da zorunlu — boşsa sessizce FAILED).
- Builder: NIXPACKS.
- Auto-deploy: GitHub push tetikler.

## Test

```bash
npm run test:intent    # Haiku classifier senaryoları
npm run test:rate      # rate limit testi
npm run test:burst     # paralel POST → tek cevap
```

## _PAYLASIM_NOTU

Mod C — şablona indirilmiş Whatsapp_Asistan paraleli (Instagram kanalı). Orijinal projedeki marka-spesifik refuse mesajları, Notion DB ID, KB içerikleri jenerikleşti; pattern korundu. Öğrenci kendi KB markdown'ını, kendi Notion video DB ID'sini ve kendi refuse politikasını koyar.
