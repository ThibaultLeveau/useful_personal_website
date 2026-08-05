"use client";

import { useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { ChangePasswordRequest } from "@/generated/api/src/models";

import { passwordErrorView, type AuthErrorView } from "./auth-errors";
import styles from "./auth.module.css";
import { PasswordField } from "./password-field";

interface ChangePasswordFormProps {
  forced?: boolean;
  onChangePassword(request: ChangePasswordRequest): Promise<void>;
  onLogout(): Promise<void>;
}

interface PasswordErrors {
  confirm?: string;
  current?: string;
  next?: string;
}

function validate(current: string, next: string, confirm: string): PasswordErrors {
  const errors: PasswordErrors = {};
  if (!current) errors.current = "Enter your current password.";
  if (!next) errors.next = "Enter a new password.";
  else if (next.length < 12) errors.next = "Use at least 12 characters.";
  else if (next.length > 1024) errors.next = "Use at most 1,024 characters.";
  else if (next === current) errors.next = "Choose a password different from the current one.";
  if (!confirm) errors.confirm = "Confirm the new password.";
  else if (next !== confirm) errors.confirm = "The new passwords do not match.";
  return errors;
}

export function ChangePasswordForm({
  forced = false,
  onChangePassword,
  onLogout,
}: ChangePasswordFormProps) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<PasswordErrors>({});
  const [serverError, setServerError] = useState<AuthErrorView>();
  const [submitting, setSubmitting] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const errorSummary = useRef<HTMLDivElement>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(current, next, confirm);
    setErrors(nextErrors);
    setServerError(undefined);
    if (Object.keys(nextErrors).length > 0) {
      queueMicrotask(() => errorSummary.current?.focus());
      return;
    }

    setSubmitting(true);
    try {
      await onChangePassword({ currentPassword: current, newPassword: next });
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (error) {
      setServerError(passwordErrorView(error));
      queueMicrotask(() => errorSummary.current?.focus());
    } finally {
      setSubmitting(false);
    }
  }

  async function logout() {
    setLoggingOut(true);
    try {
      await onLogout();
    } finally {
      setLoggingOut(false);
    }
  }

  const hasErrors = Boolean(serverError || errors.current || errors.next || errors.confirm);

  return (
    <form className={styles.form} noValidate onSubmit={submit}>
      {hasErrors ? (
        <div
          aria-labelledby="password-error-title"
          className={styles.errorSummary}
          ref={errorSummary}
          role="alert"
          tabIndex={-1}
        >
          <h2 id="password-error-title">{serverError?.title ?? "Check the form"}</h2>
          {serverError ? <p>{serverError.message}</p> : null}
          <ul>
            {errors.current ? (
              <li>
                <a
                  href="#current-password"
                  onClick={() => document.getElementById("current-password")?.focus()}
                >
                  {errors.current}
                </a>
              </li>
            ) : null}
            {errors.next ? (
              <li>
                <a
                  href="#new-password"
                  onClick={() => document.getElementById("new-password")?.focus()}
                >
                  {errors.next}
                </a>
              </li>
            ) : null}
            {errors.confirm ? (
              <li>
                <a
                  href="#confirm-password"
                  onClick={() => document.getElementById("confirm-password")?.focus()}
                >
                  {errors.confirm}
                </a>
              </li>
            ) : null}
          </ul>
          {serverError?.requestId ? (
            <p className={styles.requestId}>Request ID: {serverError.requestId}</p>
          ) : null}
        </div>
      ) : null}

      <div className={styles.requirements} aria-labelledby="password-requirements-title">
        <h2 id="password-requirements-title">Password requirements</h2>
        <ul>
          <li>At least 12 characters; long password-manager values are supported.</li>
          <li>Different from the current password.</li>
          <li>Not present in the server’s common-password blocklist.</li>
        </ul>
      </div>

      <PasswordField
        autoComplete="current-password"
        error={errors.current}
        label={forced ? "Initial password" : "Current password"}
        maxLength={1024}
        name="current-password"
        onChange={(event) => {
          setCurrent(event.target.value);
          if (errors.current)
            setErrors((value) => {
              const nextErrors = { ...value };
              delete nextErrors.current;
              return nextErrors;
            });
        }}
        required
        value={current}
      />
      <PasswordField
        autoComplete="new-password"
        error={errors.next}
        hint="Use a password manager to generate and save a unique password."
        label="New password"
        maxLength={1024}
        minLength={12}
        name="new-password"
        onChange={(event) => {
          setNext(event.target.value);
          if (errors.next)
            setErrors((value) => {
              const nextErrors = { ...value };
              delete nextErrors.next;
              return nextErrors;
            });
        }}
        required
        value={next}
      />
      <PasswordField
        autoComplete="new-password"
        error={errors.confirm}
        label="Confirm new password"
        maxLength={1024}
        minLength={12}
        name="confirm-password"
        onChange={(event) => {
          setConfirm(event.target.value);
          if (errors.confirm)
            setErrors((value) => {
              const nextErrors = { ...value };
              delete nextErrors.confirm;
              return nextErrors;
            });
        }}
        required
        value={confirm}
      />

      <div className={styles.actions}>
        <Button disabled={submitting || loggingOut} type="submit">
          {submitting ? "Changing password…" : "Change password"}
        </Button>
        <Button disabled={submitting || loggingOut} onClick={logout} variant="quiet">
          {loggingOut ? "Signing out…" : "Sign out"}
        </Button>
      </div>
      <p aria-live="polite" className={styles.submitStatus} role="status">
        {submitting
          ? "Changing your password and rotating the protected session."
          : loggingOut
            ? "Clearing protected content and signing out."
            : ""}
      </p>
    </form>
  );
}
