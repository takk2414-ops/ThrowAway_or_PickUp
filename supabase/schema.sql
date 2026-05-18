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

create index if not exists idx_user_paper_actions_paper_id
  on user_paper_actions (paper_id);

create index if not exists idx_user_paper_actions_user_id
  on user_paper_actions (user_id);

create index if not exists idx_user_paper_actions_created_at
  on user_paper_actions (created_at desc);
