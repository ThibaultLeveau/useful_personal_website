"use client";

import { useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { LoginRequest } from "@/generated/api/src/models";

import { loginErrorView, type AuthErrorView } from "./auth-errors";
import styles from "./auth.module.css";
import { PasswordField } from "./password-field";

interface LoginFormProps {
  onLogin(request: LoginRequest): Promise<void>;
}

interface LoginErrors {
  email?: string;
  password?: string;
}

function validate(email: string, password: string): LoginErrors {
  const errors: LoginErrors = {};
  if (!email.trim()) errors.email = "Enter your administrator email.";
  if (!password) errors.password = "Enter your password.";
  return errors;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<LoginErrors>({});
  const [serverError, setServerError] = useState<AuthErrorView>();
  const [submitting, setSubmitting] = useState(false);
  const errorSummary = useRef<HTMLDivElement>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(email, password);
    setErrors(nextErrors);
    setServerError(undefined);
    if (Object.keys(nextErrors).length > 0) {
      queueMicrotask(() => errorSummary.current?.focus());
      return;
    }

    setSubmitting(true);
    try {
      await onLogin({ email: email.trim(), password });
      setPassword("");
    } catch (error) {
      setServerError(loginErrorView(error));
      queueMicrotask(() => errorSummary.current?.focus());
    } finally {
      setSubmitting(false);
    }
  }

  const hasErrors = Boolean(serverError || errors.email || errors.password);

  return (
    <form className={styles.form} noValidate onSubmit={submit}>
      {hasErrors ? (
        <div
          aria-labelledby="login-error-title"
          className={styles.errorSummary}
          ref={errorSummary}
          role="alert"
          tabIndex={-1}
        >
          <h2 id="login-error-title">{serverError?.title ?? "Check the form"}</h2>
          {serverError ? <p>{serverError.message}</p> : null}
          <ul>
            {errors.email ? (
              <li>
                <a
                  href="#admin-email"
                  onClick={() => document.getElementById("admin-email")?.focus()}
                >
                  {errors.email}
                </a>
              </li>
            ) : null}
            {errors.password ? (
              <li>
                <a
                  href="#login-password"
                  onClick={() => document.getElementById("login-password")?.focus()}
                >
                  {errors.password}
                </a>
              </li>
            ) : null}
          </ul>
          {serverError?.requestId ? (
            <p className={styles.requestId}>Request ID: {serverError.requestId}</p>
          ) : null}
        </div>
      ) : null}

      <div className={styles.field}>
        <label htmlFor="admin-email">Administrator email</label>
        <input
          aria-describedby={errors.email ? "admin-email-error" : undefined}
          aria-invalid={errors.email ? "true" : undefined}
          autoCapitalize="none"
          autoComplete="username"
          id="admin-email"
          inputMode="email"
          maxLength={320}
          name="email"
          onBlur={() => setErrors((current) => ({ ...current, ...validate(email, "x") }))}
          onChange={(event) => {
            setEmail(event.target.value);
            if (errors.email)
              setErrors((current) => {
                const nextErrors = { ...current };
                delete nextErrors.email;
                return nextErrors;
              });
          }}
          required
          spellCheck={false}
          type="email"
          value={email}
        />
        {errors.email ? (
          <p className={styles.fieldError} id="admin-email-error">
            {errors.email}
          </p>
        ) : null}
      </div>

      <PasswordField
        autoComplete="current-password"
        error={errors.password}
        label="Password"
        maxLength={1024}
        name="login-password"
        onBlur={() => setErrors((current) => ({ ...current, ...validate("x", password) }))}
        onChange={(event) => {
          setPassword(event.target.value);
          if (errors.password)
            setErrors((current) => {
              const nextErrors = { ...current };
              delete nextErrors.password;
              return nextErrors;
            });
        }}
        required
        value={password}
      />

      <Button className={styles.submit} disabled={submitting} type="submit">
        {submitting ? "Signing in…" : "Sign in"}
      </Button>
      <p aria-live="polite" className={styles.submitStatus} role="status">
        {submitting ? "Verifying your credentials securely." : ""}
      </p>
    </form>
  );
}
