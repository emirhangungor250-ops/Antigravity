-- Instagram Asistan — Supabase migration
-- WhatsApp Asistan ile aynı Supabase projesini paylaşır; namespace ig_ prefix'i.

-- ============================================================
-- 0. Extension (idempotent — WA migration zaten kurmuş olabilir)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. ig_subscribers
-- ============================================================
CREATE TABLE IF NOT EXISTS ig_subscribers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  subscriber_id TEXT UNIQUE NOT NULL,
  ig_username TEXT,
  language TEXT DEFAULT 'tr',
  profile_json JSONB DEFAULT '{}',
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ig_subscribers_sid ON ig_subscribers(subscriber_id);

-- ============================================================
-- 2. ig_conversations
-- ============================================================
CREATE TABLE IF NOT EXISTS ig_conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  subscriber_id TEXT NOT NULL REFERENCES ig_subscribers(subscriber_id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  intent TEXT,
  model_used TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ig_conv_subscriber ON ig_conversations(subscriber_id, created_at DESC);

-- ============================================================
-- 3. ig_rate_limits — F1 (24h / 10 mesaj)
-- ============================================================
CREATE TABLE IF NOT EXISTS ig_rate_limits (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  subscriber_id TEXT NOT NULL,
  event_type TEXT NOT NULL DEFAULT 'user_msg',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ig_rate_subscriber_created
  ON ig_rate_limits(subscriber_id, created_at DESC);

-- ============================================================
-- 4. RAG-A — knowledge_chunks (WA ile paylaşılan; source kolonu eklenir)
-- ============================================================
ALTER TABLE knowledge_chunks
  ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'main';
CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_chunks(source);

-- ============================================================
-- 5. RAG-B — ig_video_chunks (Notion video transcript chunks)
-- ============================================================
CREATE TABLE IF NOT EXISTS ig_video_chunks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  notion_page_id TEXT NOT NULL,
  video_title TEXT,
  video_url TEXT,
  drive_url TEXT,
  publish_date DATE,
  trigger_keyword TEXT,
  content TEXT NOT NULL,
  chunk_index INT NOT NULL DEFAULT 0,
  embedding VECTOR(1536) NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (notion_page_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_ig_video_embedding ON ig_video_chunks
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 30);
CREATE INDEX IF NOT EXISTS idx_ig_video_keyword ON ig_video_chunks(trigger_keyword);
CREATE INDEX IF NOT EXISTS idx_ig_video_page ON ig_video_chunks(notion_page_id);

-- ============================================================
-- 6. RPC: match_video_chunks — RAG-B retrieval
-- ============================================================
CREATE OR REPLACE FUNCTION match_video_chunks(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.35,
  match_count INT DEFAULT 6
)
RETURNS TABLE (
  id UUID,
  notion_page_id TEXT,
  video_title TEXT,
  video_url TEXT,
  drive_url TEXT,
  content TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT vc.id, vc.notion_page_id, vc.video_title, vc.video_url, vc.drive_url, vc.content,
         1 - (vc.embedding <=> query_embedding) AS similarity
  FROM ig_video_chunks vc
  WHERE 1 - (vc.embedding <=> query_embedding) > match_threshold
  ORDER BY vc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ============================================================
-- 7. RPC: match_knowledge_chunks_filtered — RAG-A source filter
-- ============================================================
CREATE OR REPLACE FUNCTION match_knowledge_chunks_filtered(
  query_embedding VECTOR(1536),
  source_filter TEXT DEFAULT 'main',
  match_threshold FLOAT DEFAULT 0.35,
  match_count INT DEFAULT 8
)
RETURNS TABLE (
  id UUID,
  section TEXT,
  section_title TEXT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT kc.id, kc.section, kc.section_title, kc.content, kc.metadata,
         1 - (kc.embedding <=> query_embedding) AS similarity
  FROM knowledge_chunks kc
  WHERE COALESCE(kc.source, 'main') = source_filter
    AND 1 - (kc.embedding <=> query_embedding) > match_threshold
  ORDER BY kc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ============================================================
-- 8. RPC: ig_check_rate_limit
-- ============================================================
CREATE OR REPLACE FUNCTION ig_check_rate_limit(
  p_subscriber_id TEXT,
  p_max INT DEFAULT 10,
  p_window_hours INT DEFAULT 24
)
RETURNS TABLE (allowed BOOLEAN, current_count INT)
LANGUAGE plpgsql
AS $$
DECLARE
  c INT;
BEGIN
  SELECT COUNT(*)::INT INTO c
  FROM ig_rate_limits
  WHERE subscriber_id = p_subscriber_id
    AND created_at > NOW() - (p_window_hours || ' hours')::INTERVAL;
  RETURN QUERY SELECT (c < p_max), c;
END;
$$;
