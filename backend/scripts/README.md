# Daily Feed Import

日次の論文リストは `import_daily_feed.py` から生成します。

推奨実行時刻:

```text
毎日 4:00 JST
```

朝にユーザーがサイトを開く前に、論文リストとAI分析を準備するための時刻です。arXivのannouncement直後を厳密に追うよりも、起床前に表示データを揃えることを優先します。

cron例:

```cron
0 4 * * * cd /path/to/ThrowAway_or_PickUp/backend && ./.venv/bin/python scripts/import_daily_feed.py
```

この処理は、同じJST日付のリストが既に存在する場合は再取り込みしません。
