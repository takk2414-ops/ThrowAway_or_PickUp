-- 論文そのものの情報を保存する基本テーブルです。
-- 「今日表示するかどうか」はこのテーブルには持たせず、daily_paper_items で管理します。
create table if not exists papers (
  -- Supabase/PostgreSQL側で自動生成される一意なIDです。
  id uuid primary key default gen_random_uuid(),

  -- 論文タイトルです。論文として必須なので not null にしています。
  title text not null,

  -- 論文の要約です。取得できない場合もあるため null を許可しています。
  abstract text,

  -- arXivや論文ページなど、元データへのURLです。
  source_url text,

  -- arXiv IDです。存在する場合は重複登録を防ぎます。
  arxiv_id text unique,

  -- DOIです。存在する場合は重複登録を防ぎます。
  doi text unique,

  -- 著者一覧です。未取得の場合は空配列にします。
  authors text[] not null default '{}',

  -- 著者の所属機関です。複数機関を想定して配列で保存します。
  institutions text[] not null default '{}',

  -- 論文や発表に紐づく場所です。論文本体では未取得のことが多いためnullを許可します。
  location text,

  -- 論文の公開日時です。
  published_at timestamptz,

  -- このアプリのDBに登録された日時です。
  created_at timestamptz not null default now(),

  -- このアプリのDB上で最後に更新された日時です。
  updated_at timestamptz not null default now()
);

-- 毎日表示する論文リストを保存するテーブルです。
-- 1日20件という初期値はアプリ設定で管理し、DBでは件数を固定しません。
create table if not exists daily_paper_items (
  id uuid primary key default gen_random_uuid(),

  -- 表示対象になった論文です。論文が削除されたら表示記録も削除します。
  paper_id uuid not null references papers(id) on delete cascade,

  -- どの日の表示リストかを表します。
  target_date date not null,

  -- その日の表示順です。件数固定はせず、1以上だけ許可します。
  display_order integer not null check (display_order > 0),

  -- なぜその日に表示対象へ選んだかを将来保存できるようにします。
  selection_reason text,

  created_at timestamptz not null default now(),

  -- 同じ日の同じ順番に、複数の論文が入らないようにします。
  unique (target_date, display_order),

  -- 同じ日に同じ論文が重複して出ないようにします。
  unique (target_date, paper_id)
);

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

-- 論文に紐づく周辺情報を保存するテーブルです。
-- GitHub実装、Qiita記事、Hacker Newsの反応など、
-- 論文以外の技術シグナルを扱います。
create table if not exists related_signals (
  id uuid primary key default gen_random_uuid(),

  -- 関連先の論文です。論文が削除されたら周辺情報も削除します。
  paper_id uuid not null references papers(id) on delete cascade,

  -- 情報源の種類です。
  source_type text not null check (
    source_type in (
      'github',
      'qiita',
      'hacker_news',
      'reddit',
      'x',
      'hugging_face',
      'blog',
      'other'
    )
  ),

  -- 周辺情報のタイトルです。
  title text not null,

  -- GitHub repository、記事、投稿などのURLです。
  source_url text not null,

  -- 判断材料として画面に出せる短い説明です。
  summary text,

  -- 情報源側で公開された日時です。
  published_at timestamptz,

  -- APIレスポンスなど、今後必要になる生メタデータを保存できます。
  raw_metadata jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  -- 同じ論文に対して同じURLを重複保存しないようにします。
  unique (paper_id, source_url)
);

-- Zennは公式APIとして扱いにくいため、自動探索対象から外します。
-- 既存DBに古いZenn行や古いcheck制約がある場合に備えて更新します。
delete from related_signals
  where source_type = 'zenn';

alter table related_signals
  drop constraint if exists related_signals_source_type_check;

alter table related_signals
  add constraint related_signals_source_type_check
  check (
    source_type in (
      'github',
      'qiita',
      'hacker_news',
      'reddit',
      'x',
      'hugging_face',
      'blog',
      'other'
    )
  );

-- OpenAI/Geminiなどで生成した論文分析結果を保存するテーブルです。
-- 画面表示時に毎回AI APIを呼ばず、事前生成した分析を再利用します。
create table if not exists paper_ai_analyses (
  id uuid primary key default gen_random_uuid(),

  -- 分析対象の論文です。論文が削除されたら分析結果も削除します。
  paper_id uuid not null references papers(id) on delete cascade,

  -- 分析に使ったAI providerとmodelです。
  provider text not null,
  model text not null,

  -- 原題の下に補助表示する日本語タイトルです。
  title_ja text,

  -- 画面で見出し付き表示する構造化AI分析です。
  what_is_it_ja text,
  novelty_ja text,
  why_it_matters_ja text,
  recommended_for_ja text,

  -- Abstractをもとにした日本語要約です。
  summary_ja text not null,

  -- 実装する難しさです。1が易しく、5が難しい目安です。
  implementation_difficulty integer not null check (
    implementation_difficulty between 1 and 5
  ),
  implementation_reason text not null,

  -- 論文文章を読む難しさです。1が易しく、5が難しい目安です。
  reading_difficulty integer not null check (
    reading_difficulty between 1 and 5
  ),
  reading_reason text not null,

  -- 数学的な難しさです。1が易しく、5が難しい目安です。
  math_difficulty integer not null check (
    math_difficulty between 1 and 5
  ),
  math_reason text not null,

  -- APIレスポンスや将来の追加メタデータを保存します。
  raw_response jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  -- 同じ論文を同じprovider/modelで重複分析しないようにします。
  unique (paper_id, provider, model)
);

-- ユーザーが論文に対して行った操作履歴を保存するテーブルです。
-- pickup / save / skip を履歴として残します。
create table if not exists user_paper_actions (
  id uuid primary key default gen_random_uuid(),

  -- 操作対象の論文です。
  paper_id uuid not null references papers(id) on delete cascade,

  -- 将来Supabase Authと接続するためのユーザーIDです。
  -- 認証実装前でも開発できるよう、今はnullを許可します。
  user_id uuid,

  -- ユーザーの判断です。指定した3種類以外は保存できません。
  action text not null check (action in ('pickup', 'save', 'skip')),

  -- 判断理由やメモを保存します。
  reason text,

  created_at timestamptz not null default now()
);

create index if not exists idx_papers_published_at
  on papers (published_at desc);

create index if not exists idx_papers_created_at
  on papers (created_at desc);

create index if not exists idx_daily_paper_items_target_date
  on daily_paper_items (target_date desc, display_order asc);

create index if not exists idx_daily_paper_items_paper_id
  on daily_paper_items (paper_id);

create index if not exists idx_daily_import_runs_import_date
  on daily_import_runs (import_date desc, source);

create index if not exists idx_related_signals_paper_id
  on related_signals (paper_id);

create index if not exists idx_related_signals_source_type
  on related_signals (source_type);

create index if not exists idx_related_signals_published_at
  on related_signals (published_at desc);

create index if not exists idx_paper_ai_analyses_paper_id
  on paper_ai_analyses (paper_id);

create index if not exists idx_paper_ai_analyses_provider_model
  on paper_ai_analyses (provider, model);

create index if not exists idx_user_paper_actions_paper_id
  on user_paper_actions (paper_id);

create index if not exists idx_user_paper_actions_user_id
  on user_paper_actions (user_id);

create index if not exists idx_user_paper_actions_created_at
  on user_paper_actions (created_at desc);
