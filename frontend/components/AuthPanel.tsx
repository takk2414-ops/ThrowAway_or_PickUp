"use client";

import type { FormEvent } from "react";

import { isSupabaseAuthConfigured } from "../lib/supabaseAuth";
import type { AuthSession } from "../lib/supabaseAuth";

export type AuthMode = "signin" | "signup";

type AuthPanelProps = {
  authError: string | null;
  authMessage: string | null;
  authMode: AuthMode;
  authSession: AuthSession | null;
  email: string;
  isAuthPending: boolean;
  onAuthModeChange: (authMode: AuthMode) => void;
  onEmailChange: (email: string) => void;
  onPasswordChange: (password: string) => void;
  onSignOut: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  password: string;
};

export function AuthPanel({
  authError,
  authMessage,
  authMode,
  authSession,
  email,
  isAuthPending,
  onAuthModeChange,
  onEmailChange,
  onPasswordChange,
  onSignOut,
  onSubmit,
  password,
}: AuthPanelProps) {
  return (
    <section className="auth-panel" aria-label="ログイン">
      {authSession ? (
        <div className="auth-row">
          <div>
            <p className="auth-label">ログイン中</p>
            <p className="auth-email">{authSession.email ?? authSession.userId}</p>
          </div>
          <button className="secondary-button" onClick={onSignOut} type="button">
            Logout
          </button>
        </div>
      ) : (
        <form className="auth-form" onSubmit={onSubmit}>
          <div className="auth-tabs" role="tablist" aria-label="認証モード">
            <button
              aria-selected={authMode === "signin"}
              className={authMode === "signin" ? "auth-tab active" : "auth-tab"}
              onClick={() => onAuthModeChange("signin")}
              role="tab"
              type="button"
            >
              Login
            </button>
            <button
              aria-selected={authMode === "signup"}
              className={authMode === "signup" ? "auth-tab active" : "auth-tab"}
              onClick={() => onAuthModeChange("signup")}
              role="tab"
              type="button"
            >
              Sign up
            </button>
          </div>
          <label>
            Email
            <input
              autoComplete="email"
              onChange={(event) => onEmailChange(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label>
            Password
            <input
              autoComplete={authMode === "signin" ? "current-password" : "new-password"}
              minLength={6}
              onChange={(event) => onPasswordChange(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          <button className="primary-button" disabled={isAuthPending} type="submit">
            {isAuthPending ? "Sending..." : authMode === "signin" ? "Login" : "Sign up"}
          </button>
        </form>
      )}

      {!isSupabaseAuthConfigured() && (
        <p className="auth-message error">
          NEXT_PUBLIC_SUPABASE_URL と NEXT_PUBLIC_SUPABASE_ANON_KEY を設定してください。
        </p>
      )}
      {authMessage && <p className="auth-message">{authMessage}</p>}
      {authError && <p className="auth-message error">{authError}</p>}
    </section>
  );
}
