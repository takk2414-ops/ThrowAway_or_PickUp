# Supabase Migrations

`schema.sql` は現在のDB全体像です。`migrations/` は、Supabase本体へどの変更を適用したか追いやすくするための履歴です。

既存環境で未反映のテーブルだけ足す場合は、必要なmigrationをSupabase SQL Editorで実行してください。

特に最近追加したもの:

- `002_daily_import_runs.sql`
- `003_paper_ai_analyses.sql`

新規環境を作る場合は、`schema.sql` 全体を適用するか、`001_current_schema.sql` 相当の内容を適用します。
