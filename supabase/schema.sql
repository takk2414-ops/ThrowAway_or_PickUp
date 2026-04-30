create table if not exists papers (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  abstract text,
  source_url text,
  published_at timestamptz,
  created_at timestamptz not null default now()
);
