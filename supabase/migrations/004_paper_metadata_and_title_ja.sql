alter table papers
  add column if not exists institutions text[] not null default '{}';

alter table papers
  add column if not exists location text;

alter table paper_ai_analyses
  add column if not exists title_ja text;

alter table paper_ai_analyses
  add column if not exists what_is_it_ja text;

alter table paper_ai_analyses
  add column if not exists novelty_ja text;

alter table paper_ai_analyses
  add column if not exists why_it_matters_ja text;

alter table paper_ai_analyses
  add column if not exists recommended_for_ja text;
