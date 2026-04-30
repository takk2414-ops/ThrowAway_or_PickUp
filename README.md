# ThrowAway_or_PickUp

**ThrowAway_or_PickUp** は、日本人エンジニア・情報系学生向けの論文スクリーニングWebアプリです。

情報過多な arXiv / 論文探索の中から、読むべき可能性の高い論文を、
**日本語で、根拠つきで、最小限の情報量に圧縮して提示**します。

大量の論文をすべて読むのではなく、
「今読むべきか」「後で読むか」「一旦スキップするか」を高速に判断するためのミニマル・スキャナーです。

---

## Concept

> 99%を流し、1%を拾う。
> ただし、捨てるのではなく、根拠を見て優先度を下げる。

現代のエンジニアや学生は、毎日のように増え続ける論文・技術記事・研究成果にさらされています。

しかし、本当に必要なのは「大量の要約」ではなく、
**読む価値があるかを判断するための材料**です。

ThrowAway_or_PickUp は、AIに論文の価値判断を丸投げするツールではありません。

AI、論文内の記述、外部メタデータ、既存研究との比較、日本語圏での反応を使って、
ユーザーの判断を速く、正確にするための支援ツールです。

---

## Mission

このプロジェクトの目的は、情報収集における「決定疲労」を減らすことです。

特に以下を重視します。

- 論文を読む前の判断時間を短縮する
- AIの判断根拠を表示し、信頼性を高める
- 日本人エンジニアが読みやすい技術日本語で表示する
- 最新論文と著名論文を比較し、研究上の差分を把握しやすくする
- 「読む / 保存 / スキップ」の操作をキーボードだけで高速に行う
- Zenn / Qiita / X など、日本語圏での言及も参考情報として扱う

---

## Core Idea

このアプリでは、論文を以下の3種類に分けて扱います。

---

### 1. Hot Papers

直近に投稿された最新論文です。

例：

- 今日投稿された論文
- 今週注目されている論文
- arXiv に新しく出た論文

ただし、最新論文はまだ引用数や外部評価が少ないため、
アプリ上では「価値が確定した論文」ではなく、**読む候補**として扱います。

---

### 2. Rising Papers

投稿から数か月〜数年以内で、すでに注目され始めている論文です。

例：

- 引用数が伸び始めている論文
- GitHub 実装が存在する論文
- Papers with Code などで参照されている論文
- 有名な研究者・研究機関が関わっている論文
- 日本語圏のZenn / Qiita / X などで言及され始めている論文

ThrowAway_or_PickUp では、この層を特に重要視します。

最新すぎず、古すぎず、
**今読んでおく価値が高い可能性のある論文**を発見することが目的です。

---

### 3. Anchor Papers

分野の基準となる著名論文・古典的論文です。

Anchor Papers は、主に比較対象として使います。

新しい論文に対して、

- どの既存研究と関係しているのか
- 何を改善しているのか
- 技術的な差分はどこにあるのか

を説明するために利用します。

---

## Japanese-first, English-friendly

ThrowAway_or_PickUp は、日本人向けのサイトですが、
専門用語をすべて無理に日本語へ翻訳することはしません。

技術分野では、不自然な翻訳によって読み取り速度が落ちることがあります。

例：

| Original | 不自然な訳 | 推奨表示 |
|---|---|---|
| Prompt Engineering | 指示文工学 | Prompt Engineering |
| Backpropagation | 誤差逆伝播法 | Backpropagation / 誤差逆伝播法 |
| Retrieval-Augmented Generation | 検索拡張生成 | RAG（検索拡張生成） |
| Latency | 待ち時間 | Latency（遅延） |
| Fine-tuning | 微調整 | Fine-tuning（微調整） |

---

## Hybrid Keyword Policy

本アプリでは、専門用語について以下の方針を採用します。

```text
日本語の骨組み + 英語のキーワード

例：

この論文は RAG（検索拡張生成）における Latency（遅延）を削減するため、
軽量な Re-ranking 手法を提案しています。
Translation Rules
CS専門用語は無理に日本語化しない
一般的に英語で使われる語は英語のまま残す
必要に応じて日本語をカッコ書きで補足する
不自然な直訳を避ける
数式、アルゴリズム名、モデル名、データセット名は原則として英語表記を維持する
日本語訳よりも、エンジニアが素早く読めることを優先する
Main Features
Delta Highlight

論文全文を読む前に、AI が推定した「既存研究との差分候補」を1文で表示します。

Delta:
この論文は、RAG（検索拡張生成）における Re-ranking の計算コストを削減する可能性がある手法を提案しています。

Delta は断定ではなく、Abstract や本文、メタデータに基づいた推定として扱います。

Evidence-based PickUp

PickUp する理由を必ず表示します。

PickUp Reason:
- 既存研究との差分が明確
- GitHub 実装リンクが存在する
- Citation が伸び始めている
- ユーザーの関心タグ「Database」「Retrieval」と一致

これにより、AIの出力をそのまま信じるのではなく、
ユーザーが根拠を確認して判断できます。

Grounding: Evidence-based AI Output

ThrowAway_or_PickUp では、AIの出力をそのまま信頼しません。

Delta Highlight や PickUp Reason は、必ず論文内の記述や外部メタデータに基づいて表示します。

AIが生成した判断には、可能な限り
「どの情報を根拠にしたのか」
を示します。

Grounded Output Example
Delta:
この論文は、RAG における Re-ranking 処理の Latency を削減する可能性があります。

Grounding:
- Abstract: "we reduce the computational cost of reranking..." に基づく
- Metadata: GitHub 実装リンクあり
- OpenAlex: 関連論文からの引用あり

AIの役割は、論文の価値を勝手に決めることではありません。

論文内の主張やメタデータを圧縮し、
ユーザーが判断できる形に変換することです。

そのため、AIが根拠を示せない場合は、断定的な表示を避けます。

Low Confidence:
この論文の差分は Abstract からは明確に判断できません。
Japanese Social Evidence

日本人エンジニア向けの論文探索では、英語圏の評価だけでは不十分です。

日本では、論文そのものよりも、

Zenn
Qiita
X（旧Twitter）
個人ブログ
勉強会資料
GitHub Issue / Discussion

などを通じて論文を知るケースが多くあります。

そのため、ThrowAway_or_PickUp では、論文の arXiv ID、タイトル、著者名などをもとに、
日本語圏での言及を参考情報として表示します。

Social Evidence Example
Japanese Mentions:
- Zenn: 2件の解説記事あり
- Qiita: 1件の実装メモあり
- X Search: arXiv ID で検索

これは論文の価値を直接決めるものではありません。

ただし、

英語圏では Rising
日本語圏でも話題になり始めている

という状態は、日本人エンジニアにとって重要な判断材料になります。

Vim-like Binary Scan

キーボード操作で論文を高速に仕分けできます。

J: Skip
K: PickUp
Space: Save
J: Skip

その場では読まない論文として優先度を下げます。

完全に削除するのではなく、後から確認できるように履歴に残します。

K: PickUp

読む価値があると判断した論文の詳細を展開します。

表示される情報：

技術タグ
著者情報
関連する著名論文
PDFリンク
GitHubリンク
PickUp理由
Grounding
Confidence
日本語圏での言及
Space: Save

後でじっくり読む論文として保存します。

IME-safe Keyboard Design

日本語サイトでは、日本語入力IMEとキーボードショートカットの衝突が問題になります。

たとえば、J / K / Space をショートカットとして使う場合、
IMEがオンになっているとキー入力がIMEに吸収され、ショートカットが反応しないことがあります。

ThrowAway_or_PickUp では、この問題を避けるため、
event.key ではなく event.code を用いて物理キーの位置で判定します。

Implementation Policy
window.addEventListener("keydown", (event) => {
  if (isTypingTarget(event.target)) return;

  switch (event.code) {
    case "KeyJ":
      skipPaper();
      break;
    case "KeyK":
      pickupPaper();
      break;
    case "Space":
      savePaper();
      break;
  }
});
Command Mode

検索窓やメモ欄などの入力フォーム以外では、
デフォルトで Command Mode として動作します。

Command Mode では、IMEの状態に依存せず、物理キー入力として操作を受け取ります。

KeyJ  -> Skip
KeyK  -> PickUp
Space -> Save

これにより、日本語入力中でもスキャン体験を崩さないUIを目指します。

Tiered Processing

arXiv の新着論文は毎日大量に投稿されます。

すべての論文を事前に日本語化・要約・比較しようとすると、

APIコストが増える
処理時間が伸びる
表示が遅くなる
使われない論文にコストをかけてしまう

という問題が発生します。

そのため、ThrowAway_or_PickUp では、
オンデマンド・段階的処理 を採用します。

Tier 1: List View

一覧表示では、低コストな情報のみを表示します。

表示内容：

Title
Authors
Published Date
arXiv Category
Citation Count
キャッシュ済みの短文があれば表示

この段階では、すべての論文に対してAI処理を行いません。

Tier 2: Delta View

ユーザーが論文を選択、またはホバーしたタイミングで、
Abstract を対象に高速なAI解析を行います。

表示内容：

Delta
One-line Japanese Summary
Technical Tags
Confidence
Grounding

この段階では、主に Abstract と Metadata を利用します。

Tier 3: Detail View

ユーザーが「読む」と判断した論文のみ、より重い処理を行います。

表示内容：

Anchor Paper Comparison
PickUp Reason
より詳しい Grounding
GitHub / Papers with Code 情報
日本語圏での言及
保存用メモ

この設計により、
見ていない論文にお金と時間をかけない
という方針を徹底します。

Technical Tags

論文の技術的な特徴をタグとして表示します。

#Database
#InformationRetrieval
#SignalProcessing
#O(n log n)
#Transformer
#Indexing
#SQLOptimization
#GraphAlgorithm
#RAG
#Re-ranking

情報系学生・エンジニアが、論文の技術的な位置づけを直感的に理解できるようにします。

Scoring Logic

論文の優先度は、単純な引用数だけでは決めません。

従来の単純な式：

Score = log(Citations + 1) / Δt

だけでは、分野差・新しさ・ユーザーの関心を十分に反映できません。

そのため、本プロジェクトでは以下のような複数要素を用いてスコアリングします。

Score =
  w1 * Recency
+ w2 * CitationSignal
+ w3 * AuthorTrust
+ w4 * ImplementationSignal
+ w5 * DeltaClarity
+ w6 * UserInterestMatch
+ w7 * JapaneseSocialSignal
Evaluation Factors
Factor	Description
Recency	論文の新しさ
CitationSignal	引用数や引用の増加傾向
AuthorTrust	著者や所属機関の信頼性
ImplementationSignal	GitHub実装や再現性の有無
DeltaClarity	既存研究との差分の明確さ
UserInterestMatch	ユーザーの関心タグとの一致度
JapaneseSocialSignal	Zenn / Qiita / X など日本語圏での言及
Reliability Design

ThrowAway_or_PickUp は、AIの出力をそのまま正解として扱いません。

信頼性を高めるために、以下の設計を採用します。

1. Skip is not Delete

Skip は完全な削除ではありません。

一時的に優先度を下げるだけです。

これにより、AIやユーザーの初期判断による見落としを減らします。

2. Show Evidence

Delta や PickUp 判定には、可能な限り根拠を表示します。

Evidence:
- Abstract 内で Re-ranking の計算コスト削減を主張
- GitHub リンクあり
- OpenAlex 上で関連論文からの参照あり
- Zenn で日本語解説記事あり
3. Compare with Anchor Papers

最新論文を単独で評価するのではなく、
著名論文・基礎論文との関係を表示します。

Related Anchor Papers:
- Attention Is All You Need
- FlashAttention
- Mamba

これにより、ユーザーは「何と比べて新しいのか」を理解できます。

4. Avoid Overclaiming

AIの出力は断定しすぎない表現にします。

Bad:

この論文は歴史を変える革新的な研究です。

Good:

Abstract 上では、既存の Transformer 系手法に対して推論時の計算量削減を主張している可能性があります。
Anti-Hallucination Policy

ハルシネーションを防ぐため、以下の方針を採用します。

Delta は Title / Abstract / Paper Body / Metadata の記述に基づいて生成する
AI が根拠を示せない主張は表示しない
根拠文と生成文をセットで保存する
Citation、著者情報、実装リンクは外部APIの値を優先する
AIによる推測には 可能性があります などの非断定表現を使う
不明な情報は Unknown として表示する
Grounding が弱い場合は Confidence を下げる
AIが生成した内容と、論文本文から抽出した根拠をUI上で分離して表示する
日本語訳によって意味が変わる場合は、英語原文を優先して表示する
Bad Example
この論文は Transformer を完全に置き換える革新的手法です。
Good Example
Abstract 上では、既存の Transformer 系手法に対して推論コスト削減を主張している可能性があります。

Grounding:
Abstract 内の "reduce inference cost" という記述に基づく
Confidence Level

AIの出力には信頼度を付与します。

Confidence: High / Medium / Low
High

論文内の記述、外部メタデータ、既存研究との比較が一致している状態。

例：

Abstract に明確な主張がある
GitHubリンクが存在する
関連する Anchor Paper が特定できる
Citation やメタデータに矛盾がない
日本語圏の言及も確認できる
Medium

判断材料はあるが、一部が推測に依存している状態。

例：

Abstract から差分は読み取れる
ただし本文確認が必要
実装や引用情報はまだ不足している
Low

差分や価値判断の根拠が弱い状態。

例：

Abstract が抽象的すぎる
既存研究との差分が不明確
外部メタデータが不足している
AI が十分な根拠を示せない
Minimal Output Policy

1つの論文に対して表示する情報は、原則として以下に限定します。

Title
Delta
Grounding
PickUp Reason
Technical Tags
Confidence
Links
Japanese Mentions

この制約により、ユーザーが読むべき情報量を増やさず、
「読む / 保存 / スキップ」の判断に集中できるようにします。

Non-Goals: What This App Does Not Build

ThrowAway_or_PickUp は、論文を読むための万能アプリではありません。

このアプリは、読む前の判断を高速化するためのミニマル・スキャナーです。

そのため、あえて以下の機能は持ちません。

1. Full Paper Reader

全文を読むための PDF ビューアや論文リーダーは実装しません。

論文を深く読む段階では、公式PDF、arXiv、Zotero、Notion、NotebookLM など、既存の読書・管理ツールに移動することを前提とします。

このアプリの役割は、読む前の選別です。

2. Long Summary Generator

長い要約は生成しません。

要約を大量に読むこと自体が、新しい情報過多になります。

そのため、このアプリでは以下のような短い判断材料に絞ります。

Delta: 1文
One-line Japanese Summary: 1文
PickUp Reason: 最大3〜5個
Technical Tags: 最大5〜8個
Confidence: High / Medium / Low
Grounding: 最小限の根拠
3. Full Translation Tool

全文翻訳機能は持ちません。

翻訳は、論文の判断に必要な最小限に限定します。

One-line Japanese Translation:
この論文は、RAG の Re-ranking を軽量化することで Latency 削減を狙っています。
4. AI-based Final Judgment

AIが「読むべき / 読むべきではない」を最終決定する機能は持ちません。

AIは判断材料を提示するだけです。

最終判断はユーザーが行います。

5. Social Feed

いいね数、ランキング、コメント欄のようなSNS的機能は持ちません。

目的はバズっている論文を眺めることではなく、
ユーザー自身にとって読む価値がある論文を見つけることです。

ただし、日本語圏での言及数は、あくまで判断材料の1つとして表示します。

6. General-purpose Research Assistant

研究テーマの相談、論文執筆、実験計画、網羅的な文献調査を行う汎用研究アシスタントではありません。

ThrowAway_or_PickUp の責務は、あくまで
読む前のスクリーニング
に限定します。

Tech Stack
Frontend
Next.js App Router
TypeScript
Tailwind CSS

高速なスキャン体験を実現するため、UI はミニマルに設計します。

黒を基調としたデザインを採用しつつ、
長時間利用でも疲れにくい視認性を重視します。

Keyboard Handling
event.code による物理キー判定
Command Mode
入力フォームではショートカット無効化
IME状態に依存しない操作設計
Backend
FastAPI
Python
Async API Processing

外部API連携、AIによるDelta抽出、スコアリング処理を担当します。

必要に応じて、以下の導入も検討します。

Redis
Celery
BackgroundTasks
Supabase Edge Functions
AI
Gemini API

主な用途：

Abstract の圧縮
Delta 候補の抽出
技術タグの生成
PickUp 理由の生成
関連研究との比較補助
Grounding に基づく短文生成
日本語の One-line Summary 生成
Metadata
arXiv API
OpenAlex API
Semantic Scholar API
Papers with Code
Zenn / Qiita / X Search Link

主な用途：

論文メタデータ取得
Citation取得
著者情報取得
関連論文取得
実装リンク確認
Anchor Paper との関連確認
日本語圏での言及確認
Database
Supabase
PostgreSQL

管理する情報：

論文情報
ユーザーの既読状態
Skip / PickUp / Save の履歴
技術タグ
スコア
ユーザーごとの関心タグ
Grounding 情報
Confidence
Anchor Paper との関係
日本語圏での言及情報
翻訳・解析キャッシュ
Database Design

想定テーブル例：

papers
users
user_paper_actions
paper_tags
paper_scores
saved_papers
anchor_papers
paper_relations
paper_groundings
paper_japanese_mentions
paper_processing_cache
papers

論文の基本情報を保存します。

id
title
abstract
authors
published_at
arxiv_url
pdf_url
citation_count
arxiv_category
created_at
updated_at
user_paper_actions

ユーザーごとの操作履歴を保存します。

id
user_id
paper_id
action
created_at

action には以下を想定します。

skip
pickup
save
paper_scores

論文のスコア情報を保存します。

id
paper_id
recency_score
citation_score
author_score
implementation_score
delta_score
user_interest_score
japanese_social_score
total_score
created_at
paper_groundings

AI出力の根拠を保存します。

id
paper_id
output_type
generated_text
source_type
source_text
source_location
confidence
created_at

例：

output_type:
delta
pickup_reason
technical_tag
one_line_summary

source_type:
title
abstract
paper_body
metadata
openalex
semantic_scholar
papers_with_code
zenn
qiita
x_search
paper_japanese_mentions

日本語圏での言及情報を保存します。

id
paper_id
source
url
title
snippet
mentioned_at
created_at

source には以下を想定します。

zenn
qiita
x
blog
slides
github
paper_processing_cache

翻訳・解析済みの結果をキャッシュします。

id
paper_id
processing_tier
input_hash
output_json
model_name
created_at
updated_at

processing_tier には以下を想定します。

tier_1_list
tier_2_delta
tier_3_detail
anchor_papers

分野の基準となる著名論文を保存します。

id
title
authors
published_year
field
paper_url
citation_count
created_at
updated_at
paper_relations

最新論文と Anchor Paper の関係を保存します。

id
paper_id
anchor_paper_id
relation_type
description
confidence
created_at

例：

relation_type:
extends
improves
compares_with
uses
replaces_partially
unknown
Getting Started
1. Clone Repository
git clone https://github.com/yourname/ThrowAway_or_PickUp.git
cd ThrowAway_or_PickUp
2. Setup Environment Variables

.env を作成し、必要なAPIキーを設定します。

GEMINI_API_KEY=your_gemini_api_key
OPENALEX_API_KEY=your_openalex_api_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
3. Start Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
4. Start Frontend
cd frontend
npm install
npm run dev
5. Start Scanning

ブラウザでアプリを開き、キーボードで論文を仕分けます。

J: Skip
K: PickUp
Space: Save
Roadmap
Phase 1: MVP
arXiv API から最新論文を取得
Title / Authors / Category の一覧表示
Abstract の短縮表示
J / K / Space 操作
event.code によるIME-safeショートカット
Supabase に操作履歴を保存
Gemini API による Delta 候補生成
Skip を完全削除ではなく履歴として保存
Phase 2: Japanese UX Upgrade
Hybrid Keyword Policy に基づく日本語表示
One-line Japanese Summary 生成
専門用語の英語維持
Translation Cache
Tiered Processing 導入
Command Mode UI
Phase 3: Reliability Upgrade
PickUp 理由の表示
Grounding 表示
Confidence 表示
技術タグ生成
OpenAlex / Semantic Scholar 連携
Citation・著者情報の取得
AI 出力と根拠文のセット保存
Phase 4: Rising Paper Detection
Citation 増加傾向の分析
GitHub 実装リンクの検出
Papers with Code 連携
ユーザー関心タグとのマッチング
Rising Papers の自動検出
Phase 5: Japanese Social Evidence
arXiv ID による Zenn / Qiita 検索リンク生成
X検索リンク生成
日本語圏での言及バッジ表示
JapaneseSocialSignal のスコア統合
日本語解説記事への導線表示
Phase 6: Anchor Paper Comparison
著名論文データベースの構築
最新論文と Anchor Paper の比較
「何が新しいのか」の説明生成
分野ごとの基準論文管理
論文間の関係性を保存
Phase 7: Personalization
ユーザーの PickUp 履歴から関心を学習
分野ごとの重み調整
おすすめ論文の精度改善
Skip した論文の再評価機能
ユーザーごとのスコア最適化
Target Users
情報系学生
バックエンドエンジニア
データベース・検索・AIに関心のあるエンジニア
英語論文を読みたいが、最初の取捨選択で疲れてしまう人
最新技術をキャッチアップしたい個人開発者
Zenn / Qiita / X で技術情報を追っている日本人エンジニア
研究に興味はあるが、論文の取捨選択に時間をかけたくない人
Design Principle

このアプリの設計思想はシンプルです。

複雑さはノイズである。
しかし、根拠のない単純化は危険である。

ThrowAway_or_PickUp は、情報を減らすアプリです。

ただし、根拠まで削ることはしません。

What We Remove
長い要約
過剰な解説
不自然な日本語訳
SNS 的な評価画面
全文リーダー機能
余計な UI
汎用研究アシスタント的な機能
見ていない論文への無駄なAI処理
What We Keep
差分
根拠
信頼度
技術タグ
英語専門用語
日本語の読みやすさ
保存先への導線
既存研究との比較
日本語圏での言及
Developer Note

このプロジェクトは、単なる論文要約アプリではありません。

目指しているのは、
読む前の意思決定を支援する日本人向け論文スクリーニングツール
です。

「何を読むか」だけでなく、
「何を今は読まないか」を安全に決めることを重視します。

Skip は捨てることではありません。
PickUp は盲信することでもありません。

その中間にある、
根拠つきの高速な判断
を実現することが、このプロジェクトの目的です。

Philosophy

ThrowAway_or_PickUp は、AI によって人間の判断を置き換えるためのアプリではありません。

AI によって、
人間が判断する前に必要な情報を圧縮するためのアプリです。

読む前に、迷わない。
拾う前に、根拠を見る。
スキップしても、完全には捨てない。
日本語で読みやすく、専門用語は崩さない。
見ていない論文に、時間もお金も使わない。

それが、このプロジェクトの基本方針です。
