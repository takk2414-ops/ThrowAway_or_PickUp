# CODEX_TASKS

Codex に依頼するタスクを管理するメモです。

## Next

-1. バックエンド基盤を固める
    - FastAPI の起動確認
    - /health の疎通確認
    - .env 読み込み設定
    - pytest の導入
    - APIテストの最小セット追加
2. DB設計を決める
    - papers テーブルを整理
    - user_paper_actions テーブルを追加
    - pickup / save / skip の履歴を保存できるようにする
    - Supabase の schema.sql を更新
3. 論文APIを作る
    - GET /papers 論文一覧取得
    - GET /papers/{paper_id} 論文詳細取得
    - POST /papers 論文登録
    - 入力値検証用の Pydantic schema を追加
4. 判定アクションAPIを作る
    - POST /papers/{paper_id}/actions
    - action は pickup, save, skip
    - 不正な action を弾く
    - 同じ論文への操作履歴を保存する
5. サービス層を分ける
    - router にDB処理を直接書かない
    - services/paper_service.py
6. Supabase接続を追加
    - まずは環境変数から接続情報を読む
    - Supabase client を lib または services にまとめる
    - 秘密情報は .env.example に値を書かない
7. フロントエンド最小画面
    - 論文一覧を表示
    - 各論文に PickUp / Save / Skip ボタン
    - まず見た目は最低限
    - バックエンドAPIの確認用画面として使う
8. AI要約・Delta Highlightは後回し
    - 最初からAIを入れると設計が膨らむ
    - まず論文データ、ユーザー判断、根拠保存の土台を作る
    - その後 delta, pickup_reason, grounding を追加する

[1. バックエンド基盤を固める](https://www.notion.so/1-352ec29b13f3807787b9de87f1c8e1d0?pvs=21)
