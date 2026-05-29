-- Geminiなどで生成した論文分析結果を保存するテーブルです。
create table if not exists paper_ai_analyses (
  id uuid primary key default gen_random_uuid(),

  paper_id uuid not null references papers(id) on delete cascade,
  provider text not null,
  model text not null,

  summary_ja text not null,

  implementation_difficulty integer not null check (
    implementation_difficulty between 1 and 5
  ),
  implementation_reason text not null,

  reading_difficulty integer not null check (
    reading_difficulty between 1 and 5
  ),
  reading_reason text not null,

  math_difficulty integer not null check (
    math_difficulty between 1 and 5
  ),
  math_reason text not null,

  raw_response jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (paper_id, provider, model)
);

create index if not exists idx_paper_ai_analyses_paper_id
  on paper_ai_analyses (paper_id);

create index if not exists idx_paper_ai_analyses_provider_model
  on paper_ai_analyses (provider, model);
