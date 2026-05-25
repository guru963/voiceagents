-- VoiceAgent Studio — Supabase schema
-- Run this in your Supabase SQL editor

-- Enable pgvector extension for RAG
create extension if not exists vector;

-- Agents table
create table if not exists agents (
  id            uuid primary key default gen_random_uuid(),
  agent_id      text unique not null,
  name          text not null,
  role          text not null,
  industry      text not null check (industry in ('healthcare','hospitality','hr','edtech','custom')),
  language      text not null default 'en' check (language in ('en','hi','ta')),
  system_prompt text not null,
  tts_provider  text not null default 'edge_tts',
  tools_enabled text[] default '{}',
  kb_enabled    boolean default false,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

-- Knowledge base chunks with vector embeddings
create table if not exists knowledge_chunks (
  id          uuid primary key default gen_random_uuid(),
  agent_id    text not null references agents(agent_id) on delete cascade,
  content     text not null,
  embedding   vector(384),        -- all-MiniLM-L6-v2 dimension
  chunk_index integer not null,
  created_at  timestamptz default now()
);

-- Index for fast vector similarity search
create index if not exists knowledge_chunks_embedding_idx
  on knowledge_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Call logs with latency metrics
create table if not exists call_logs (
  id          uuid primary key default gen_random_uuid(),
  call_id     text not null,
  agent_id    text references agents(agent_id) on delete set null,
  language    text,
  stt_ms      float,
  llm_ms      float,
  tts_ms      float,
  tool_ms     float,
  total_ms    float,
  tool_called text,
  transcript  text,
  created_at  timestamptz default now()
);

-- Index for dashboard queries
create index if not exists call_logs_agent_idx on call_logs(agent_id);
create index if not exists call_logs_created_idx on call_logs(created_at desc);

-- Semantic search function used by RAG
create or replace function match_chunks(
  query_embedding vector(384),
  agent_id_filter text,
  match_count     int default 3
)
returns table (
  id      uuid,
  content text,
  similarity float
)
language sql stable
as $$
  select
    id,
    content,
    1 - (embedding <=> query_embedding) as similarity
  from knowledge_chunks
  where agent_id = agent_id_filter
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- Row Level Security (production hardening)
alter table agents         enable row level security;
alter table knowledge_chunks enable row level security;
alter table call_logs      enable row level security;

-- Allow service role full access (your API uses service key)
create policy "service_full_access_agents" on agents
  for all using (true) with check (true);
create policy "service_full_access_chunks" on knowledge_chunks
  for all using (true) with check (true);
create policy "service_full_access_logs" on call_logs
  for all using (true) with check (true);
