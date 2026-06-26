-- YouTube Yorum Otomasyonu — Supabase şeması
-- Kendi Supabase projende çalıştır (SQL Editor). Voyage voyage-3 = 1024 boyut.

create extension if not exists vector;

-- ── Yorum durumu (idempotency + Faz 2 karar takibi) ──────────────────
create table if not exists yt_comments (
    comment_id     text primary key,          -- YouTube topLevelComment id
    video_id       text not null,
    video_title    text,
    author         text,
    author_channel text,
    text           text not null,
    lang           text,                       -- 'tr' | 'en' | ...
    like_count     int default 0,
    published_at   timestamptz,
    -- akıllı sıralama sinyali (LLM): question | substantive | praise | emoji_only | spam
    worth_kind     text,
    worth_score    int default 0,              -- 0-100, cevaplanmaya değerlik
    -- yaşam döngüsü: reported(rapor edildi) auto_replied drafted approved skipped
    status         text not null default 'reported',
    ai_draft       text,                       -- Faz 2 üretilen taslak (varsa)
    ai_confidence  text,                       -- high | medium | low
    posted_reply   text,                       -- gerçekten yayınlanan cevap (varsa)
    reported_at    timestamptz default now(),
    updated_at     timestamptz default now()
);

create index if not exists yt_comments_status_idx on yt_comments (status);
create index if not exists yt_comments_published_idx on yt_comments (published_at desc);

-- ── Öğrenme corpus'u (yorum -> kanal sahibinin cevabı çiftleri) ──────
create table if not exists yt_reply_corpus (
    id            bigint generated always as identity primary key,
    comment_id    text unique,                 -- kaynak yorum (varsa) — tekrar yüklemeyi önler
    comment_text  text not null,
    reply_text    text not null,               -- kanal sahibinin gerçek cevabı
    video_id      text,
    video_title   text,
    lang          text,
    -- nereden öğrenildi: native(YouTube'da elle), approved(taslak onaylandı), manual(elle eklendi)
    source        text default 'native',
    ai_draft      text,                        -- AI taslağı (kullanıcı düzenlediyse düzeltme sinyali)
    embedding     vector(1024),
    created_at    timestamptz default now()
);

-- cosine similarity ANN indeksi
create index if not exists yt_reply_corpus_embedding_idx
    on yt_reply_corpus using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- ── Benzer geçmiş cevapları çek (Faz 2 few-shot retrieval) ───────────
create or replace function match_reply_corpus(
    query_embedding vector(1024),
    match_count int default 5,
    filter_lang text default null
)
returns table (
    comment_text text,
    reply_text text,
    video_title text,
    lang text,
    similarity float
)
language sql stable
as $$
    select
        c.comment_text,
        c.reply_text,
        c.video_title,
        c.lang,
        1 - (c.embedding <=> query_embedding) as similarity
    from yt_reply_corpus c
    where c.embedding is not null
      and (filter_lang is null or c.lang = filter_lang)
    order by c.embedding <=> query_embedding
    limit match_count;
$$;
