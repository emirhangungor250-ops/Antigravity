# HappyScribe Glossary — AI/Claude Code Terim Listesi

HappyScribe v1 public API'sinde glossary CRUD (create/update/entries) endpoint'i bulunmuyor. Glossary UI üzerinden manuel oluşturulduktan sonra `glossary_ids` parametresi ile transcription order'larına iliştirilebiliyor. Bu dosyadaki terim listesi tek seferlik manuel upload içindir.

## Manuel kurulum (1 kez, ~2 dakika)

1. https://www.happyscribe.com/account/glossary → "New Glossary"
2. Name: `Reels Otomasyonu — Claude Code / AI`
3. Source language: `English (US)`
4. Aşağıdaki terim listesini "Add term" ile (veya CSV import varsa `glossary_terms.csv` ile) ekle
5. Oluşan glossary ID'sini bana ilet → `.env`'e `HAPPYSCRIBE_ORG_GLOSSARY_ID` olarak yazılır
6. Pipeline her transcription order'unda `glossary_ids: [<ID>]` parametresi geçer

## Terim listesi

Bu terimler, kaynak reels transkripsiyonlarında en sık yanlış yazılan ve sonraki LLM correction katmanını kirleten teknik terimlerdir. Brief'in 5.2 ve "HappyScribe spesifik tavsiyeler" bölümlerinden derlendi.

### Ürün adları (özel isimler)

- Claude
- Claude Code
- Claude Opus
- Claude Sonnet
- Claude Haiku
- Anthropic
- Antigravity
- MCP
- Model Context Protocol

### Pipeline terimleri

- agent
- subagent
- multi-agent
- agentic
- tool use
- tool calling
- function calling
- system prompt
- prompt engineering
- few-shot
- chain of thought
- context window
- token
- inference

### Yan ürünler (sık geçer)

- LangChain
- LlamaIndex
- OpenAI
- GPT-4
- GPT-5
- ChatGPT
- Cursor
- Windsurf
- Replit
- v0
- Lovable
- Bolt
- Vercel
- Supabase
- Pinecone
- Voyage AI
- Hugging Face

### Komut/CLI

- npm install
- pip install
- git push
- API key
- env var
- localhost
- webhook
- endpoint

> Bu listeyi Sprint 1 ilerleyişine göre genişleteceğim — gerçek transkriptlerde yanlış geçen terimler `transcript_corrections` tablosundan pattern olarak çıkarılıp glossary'ye eklenecek.
