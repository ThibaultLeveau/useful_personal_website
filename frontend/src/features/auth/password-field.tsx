"use client";

import { useState, type InputHTMLAttributes } from "react";

import { Button } from "@/components/ui/button";

import styles from "./auth.module.css";

interface PasswordFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "type"> {
  error?: string | undefined;
  hint?: string | undefined;
  label: string;
  name: string;
}

export function PasswordField({ error, hint, label, name, ...props }: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);
  const inputId = name;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={styles.field}>
      <label htmlFor={inputId}>{label}</label>
      {hint ? (
        <p className={styles.hint} id={hintId}>
          {hint}
        </p>
      ) : null}
      <div className={styles.passwordControl}>
        <input
          {...props}
          aria-describedby={describedBy}
          aria-invalid={error ? "true" : undefined}
          id={inputId}
          name={name}
          type={visible ? "text" : "password"}
        />
        <Button
          aria-label={`${visible ? "Hide" : "Show"} ${label.toLowerCase()}`}
          aria-pressed={visible}
          className={styles.revealButton}
          onClick={() => setVisible((current) => !current)}
          variant="quiet"
        >
          {visible ? "Hide" : "Show"}
        </Button>
      </div>
      {error ? (
        <p className={styles.fieldError} id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
}
