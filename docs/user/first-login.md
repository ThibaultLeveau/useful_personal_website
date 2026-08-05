# First administrator setup and sign-in

## What this process guarantees

The application never creates a default administrator during startup, migration, or demo seeding.
The bootstrap command creates the sole initial administrator exactly once, does not echo the
password, and marks the account as requiring an immediate password change. Re-running it after an
administrator exists is refused; it cannot be used as an account-takeover or password-reset path.

Use a password manager for both the initial and replacement credentials. The initial value must be
12–1,024 characters, must not be a blocked common password, and is temporary. Do not place either
credential in `.env`, shell history, Compose files, issue trackers, or evidence logs.

## Prepare the database

Complete `.env` as described in the [container runbook](../development/containers.md), then build
the images and run the explicit database operations from the repository root:

```console
docker compose build backend frontend
docker compose up --detach postgres
docker compose --profile operations run --rm role-init
docker compose --profile operations run --rm migrate
docker compose --profile operations run --rm permissions
```

Bootstrap uses the non-owner runtime database role and therefore runs only after migration and
permission reconciliation. Replace the synthetic email and display name below with the controlled
administrator identity. The password is read from a concealed prompt and passed only through the
one-shot process standard input.

### PowerShell

```powershell
$bootstrapSecret = Read-Host "Initial administrator password" -AsSecureString
$bootstrapPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($bootstrapSecret)
try {
  $bootstrapPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bootstrapPointer)
  $bootstrapPlain | docker compose run --rm --no-deps -T `
    -e APP_BOOTSTRAP_ADMIN_EMAIL=owner@example.test `
    -e APP_BOOTSTRAP_ADMIN_DISPLAY_NAME="Site Owner" `
    backend python -m app.commands.bootstrap_admin --password-stdin
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bootstrapPointer)
  Remove-Variable bootstrapPlain, bootstrapSecret -ErrorAction SilentlyContinue
}
```

### POSIX shell

```sh
read -r -s -p "Initial administrator password: " bootstrap_password
printf '\n'
printf '%s\n' "$bootstrap_password" | docker compose run --rm --no-deps -T \
  -e APP_BOOTSTRAP_ADMIN_EMAIL=owner@example.test \
  -e APP_BOOTSTRAP_ADMIN_DISPLAY_NAME='Site Owner' \
  backend python -m app.commands.bootstrap_admin --password-stdin
unset bootstrap_password
```

Success prints only the new administrator identifier. A repeat invocation exits with code `3` and
`Bootstrap refused: an administrator already exists.` This is the expected safety behavior.

## Start and complete first sign-in

Start the application only after bootstrap completes:

```console
docker compose up --detach backend frontend
docker compose ps
```

Open `http://localhost:3000/admin/login` (or the configured `FRONTEND_PORT`) and:

1. Sign in with the administrator email and initial password.
2. On **Set a private password**, enter the initial password and a new unique password twice.
3. Save the new value in the password manager. The initial password is invalid immediately after
   the change, and other sessions are revoked.
4. Confirm the administration overview and **Account** page are available.
5. Use **Sign out** when leaving the device. Protected content is removed before server revocation
   is attempted; if the server cannot confirm revocation, the sign-in screen exposes a retry action.

The session has a 30-minute sliding idle limit and a 12-hour absolute limit. The account page can
continue an active session within that absolute limit. Expired sessions return to a dedicated safe
screen and do not preserve protected page content.

## Troubleshooting without weakening controls

- **The sign-in error does not identify the wrong field.** This is intentional non-enumeration.
  Re-enter both values from the password manager and use the request ID when reviewing server logs.
- **Bootstrap is refused.** An administrator already exists. Do not delete the database or rerun
  bootstrap with different values. Use an approved recovery/restore procedure; a password-recovery
  workflow is not part of the current release slice.
- **The session cannot be checked.** Confirm backend readiness at `/api/v1/health/ready`, migration
  head `20260802_0010`, permission reconciliation, and the server-only API upstream configuration.
- **Origin or CSRF is rejected.** Access the UI and API through the same configured origin. Confirm
  `APP_TRUSTED_ORIGINS` exactly matches that origin and that an intermediate proxy preserves
  `Origin`, cookies, `X-CSRF-Token`, and `Set-Cookie`. Never disable either check.
- **The session expired.** Sign in again. Unsaved form input may need to be entered again by design.

Never share passwords, cookies, CSRF values, authorization headers, or raw authentication traces in
support tickets or repository evidence.
