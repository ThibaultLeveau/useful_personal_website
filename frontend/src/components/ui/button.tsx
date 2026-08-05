import { forwardRef, type ButtonHTMLAttributes } from "react";

import { classes } from "@/lib/classes";

type ButtonVariant = "primary" | "secondary" | "quiet" | "danger";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, type = "button", variant = "primary", ...props },
  ref,
) {
  return (
    <button
      className={classes("button", `button--${variant}`, className)}
      ref={ref}
      type={type}
      {...props}
    />
  );
});
