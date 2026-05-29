-- 日次取り込みの実行履歴です。
-- 4:00 JSTの定期処理が成功/失敗したかを記録します。
create table if not exists daily_import_runs (
  id uuid primary key default gen_random_uuid(),

  import_date date not null,
  source text not null,
  status text not null check (status in ('success', 'failed')),
  imported_count integer not null default 0 check (imported_count >= 0),
  error_message text,

  started_at timestamptz not null default now(),
  finished_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (import_date, source)
);

create index if not exists idx_daily_import_runs_import_date
  on daily_import_runs (import_date desc, source);
