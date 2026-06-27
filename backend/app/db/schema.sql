-- FINCON Database Schema for Supabase
-- Copy and run this in the Supabase SQL Editor

-- Enable pgvector extension for AI Memory
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. USERS TABLE (Optional, you can also use Supabase Auth's auth.users directly, 
-- but having a public profile table is good practice)
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. PORTFOLIOS TABLE
CREATE TABLE public.portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    holdings JSONB NOT NULL DEFAULT '{}', -- Example: {"AAPL": 10, "TSLA": 5}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. CHAT HISTORY TABLE (For frontend user interacting with the Manager Agent)
CREATE TABLE public.chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. AGENT REASONING LOGS (To store debate and reasoning trails for UI)
CREATE TABLE public.agent_reasoning_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL, -- Ties to a specific chat request/analysis session
    agent_name TEXT NOT NULL, -- e.g., 'Risk Agent', 'News Agent'
    input_data TEXT,
    output_data TEXT NOT NULL,
    confidence_score NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. AI MEMORY EMBEDDINGS (For long-term context using pgvector)
CREATE TABLE public.memory_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL, -- The text being remembered
    embedding vector(768), -- Google Gemini embeddings are usually 768 dimensions
    metadata JSONB DEFAULT '{}', -- Store source, timestamp, agent name etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_portfolios_user_id ON public.portfolios(user_id);
CREATE INDEX idx_chat_history_user_id ON public.chat_history(user_id);
CREATE INDEX idx_reasoning_session_id ON public.agent_reasoning_logs(session_id);

-- Create HNSW index for fast vector similarity search
CREATE INDEX idx_memory_embeddings ON public.memory_embeddings USING hnsw (embedding vector_cosine_ops);

-- Set Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_reasoning_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memory_embeddings ENABLE ROW LEVEL SECURITY;

-- Note: You will need to set up RLS policies in Supabase if frontend calls these directly, 
-- but since we use a backend, we can bypass RLS via Service Role Key for now.

-- 6. MATCH MEMORIES FUNCTION (For pgvector similarity search via RPC)
CREATE OR REPLACE FUNCTION match_memories(
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  p_user_id uuid
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    me.id,
    me.content,
    me.metadata,
    1 - (me.embedding <=> query_embedding) AS similarity
  FROM public.memory_embeddings me
  WHERE me.user_id = p_user_id
    AND 1 - (me.embedding <=> query_embedding) > match_threshold
  ORDER BY me.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
