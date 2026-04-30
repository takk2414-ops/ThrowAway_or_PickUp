# SPEC

## MVPの目的

日本人エンジニア向けに、arXivの最新論文を高速にスキャンし、
読む / 保存 / スキップを判断できるWebアプリを作る。

## MVPで実装する機能

1. arXiv APIから論文を取得する
2. 論文カードを1件ずつ表示する
3. JでSkip、KでPickUp、SpaceでSaveする
4. 操作履歴をSupabaseに保存する
5. Gemini APIでDeltaを1文生成する
6. DeltaにはGroundingとConfidenceを表示する
7. Keyboard shortcutはevent.keyではなくevent.codeで実装する

## MVPで実装しない機能

- PDF全文表示
- 長文要約
- Zenn / Qiita / X連携
- Anchor Paper比較
- Personalized Score
- Papers with Code連携

## UI方針

- 日本語UI
- CS専門用語は無理に訳さない
- 黒基調
- 1画面1論文
- 情報量を増やしすぎない

## ショートカット

- KeyJ: Skip
- KeyK: PickUp
- Space: Save

入力フォームにfocusがある場合はショートカットを無効にする。
