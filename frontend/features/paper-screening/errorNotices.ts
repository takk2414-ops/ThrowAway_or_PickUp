import { ApiError } from "../../lib/papers";

export type ErrorContext = "today" | "picked" | "action" | "analysis";

export type ErrorNotice = {
  title: string;
  message: string;
  checks: string[];
};

export function buildErrorNotice(
  error: unknown,
  fallbackMessage: string,
  context: ErrorContext,
): ErrorNotice {
  if (error instanceof ApiError) {
    if (error.detail === "Supabase schema is not applied") {
      return {
        title: "DB schemaが未反映です",
        message:
          "backendのコードが参照しているSupabaseテーブルまたはカラムが、Supabase本体にまだ作成されていません。",
        checks: [
          "Supabase SQL Editorで最新のsupabase/schema.sqlを実行してください。",
          context === "analysis"
            ? "paper_ai_analysesテーブルが存在するか確認してください。"
            : "papers / daily_paper_items / related_signals が現在のschemaと一致しているか確認してください。",
          "反映直後はschema cache更新まで少し待ってから再試行してください。",
        ],
      };
    }

    if (error.detail === "Supabase RLS blocked request") {
      return {
        title: "Supabase RLSで保存が拒否されました",
        message:
          "backendがDBへ保存しようとしましたが、SupabaseのRow Level Securityにより拒否されています。",
        checks: [
          "backend/.env の SUPABASE_SERVICE_ROLE_KEY が service_role のキーか確認してください。",
          "backendを再起動して、新しい環境変数を読み込ませてください。",
          "frontend/.env.local には service_role key を入れないでください。",
        ],
      };
    }

    if (error.status === 502) {
      if (error.detail === "arXiv rate limit exceeded. Please retry later.") {
        return {
          title: "arXivのrate limitに達しています",
          message:
            "短時間にarXiv APIへ複数回アクセスしたため、一時的に取り込みが制限されています。",
          checks: [
            "数十秒から数分待ってから画面を再読み込みしてください。",
            "開発中に何度も再読み込みすると、初回自動取り込みが連続実行されることがあります。",
            "運用環境では4:00 JSTのcronで事前生成し、ユーザーアクセス時のarXiv呼び出しを避けるのが安全です。",
          ],
        };
      }

      return {
        title:
          context === "analysis"
            ? "AI分析の保存または生成に失敗しました"
            : "Backend APIが外部サービス連携に失敗しました",
        message: error.detail ?? `${error.endpoint} が 502 を返しました。`,
        checks:
          context === "analysis"
            ? [
                "GEMINI_API_KEY が backend/.env に設定されているか確認してください。",
                "paper_ai_analysesテーブルがSupabaseに作成済みか確認してください。",
                "backendログでGemini API失敗かDB保存失敗かを確認してください。",
              ]
            : [
                "backendが起動しているか確認してください。",
                "Supabase接続、RLS、schemaのいずれかで失敗していないか確認してください。",
                "arXiv / Qiita / GitHubなど外部APIの一時失敗も疑ってください。",
              ],
      };
    }

    if (error.status === 503) {
      return {
        title: "backend設定が不足しています",
        message: error.detail ?? `${error.endpoint} が 503 を返しました。`,
        checks: [
          "backend/.env に必要な環境変数が入っているか確認してください。",
          "Supabase URL / anon key / service_role key / GEMINI_API_KEY を確認してください。",
          "環境変数を変更したらbackendを再起動してください。",
        ],
      };
    }

    return {
      title: `APIエラー: ${error.status}`,
      message: error.detail ?? `${error.endpoint} failed: ${error.status}`,
      checks: ["backendログを確認してください。"],
    };
  }

  if (error instanceof TypeError) {
    return {
      title: "Backend APIに接続できません",
      message: "frontendからbackendへ接続できませんでした。",
      checks: [
        "backendが http://127.0.0.1:8000 で起動しているか確認してください。",
        "NEXT_PUBLIC_API_BASE_URL が正しいか確認してください。",
        "backendを再起動してから画面を再読み込みしてください。",
      ],
    };
  }

  return {
    title: "エラーが発生しました",
    message: error instanceof Error ? error.message : fallbackMessage,
    checks: ["backendログとブラウザコンソールを確認してください。"],
  };
}
