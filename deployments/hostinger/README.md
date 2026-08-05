# Hostinger single-VPS production profile

This profile implements the owner-approved first deployment: one Hostinger VPS, private local media,
weekly coordinated recovery, HTTPS at the host edge, and no analytics or external error-reporting
provider at launch.

## Required non-secret values

Copy `.env.example` to the untracked root `.env`, generate every blank credential independently, and
set at least:

```dotenv
APP_ENVIRONMENT=production
APP_BUILD_VERSION=1.0.0
APP_BUILD_COMMIT=<lowercase-git-commit>
APP_TRUSTED_ORIGINS=["https://thibault-leveau.com"]
APP_MEDIA_STORAGE_KIND=local
APP_MEDIA_LOCAL_ROOT=/app/media
APP_MEDIA_LOCAL_PRODUCTION_ACKNOWLEDGED=true
APP_CONTACT_POLICY_VERSION=privacy-2026-08
APP_CONTACT_PSEUDONYM_KEY_VERSION=contact-ip-2026-08-v1
APP_CONTACT_RETENTION_DAYS=365
APP_TOKEN_DIGEST_KEY_VERSION=api-token-2026-08-v1
APP_AUDIT_RETENTION_DAYS=7
UPW_PUBLIC_SITE_ORIGIN=https://thibault-leveau.com
UPW_API_UPSTREAM_ORIGIN=http://backend:8000
```

Do not commit `.env`. Generate the database passwords and three application secrets with at least 32
random URL-safe bytes each. Keep the cluster administrator, migration owner, runtime role, audit
operator, CSRF key, token pepper, and privacy key distinct.

## Network and TLS

1. Point the root-domain DNS records to the VPS. Decide separately whether `www` redirects to the
   root domain.
2. Install the example Caddy configuration at the host edge. Caddy terminates TLS; Compose keeps the
   frontend and API bound to host loopback.
3. In the Hostinger managed firewall and the operating-system firewall, expose only TCP 80/443 and
   a restricted SSH source. Never expose PostgreSQL, port 3000, or port 8000 publicly.
4. Verify that HTTP redirects to HTTPS, `/api/v1/health/live` reaches the backend, and ordinary pages
   reach the frontend through the same public origin.

Hostinger documents its [Docker-ready Ubuntu VPS option](https://www.hostinger.com/support/8306612-how-to-use-the-docker-vps-template-at-hostinger/)
and [managed firewall](https://www.hostinger.com/support/8172641-how-to-use-a-managed-vps-firewall-at-hostinger/)
in its official help center. Provider UI instructions can change; verify them there at deployment
time.

## Start and configure

Follow the [operator runbook](../../docs/user/operator-runbook.md) to build, migrate, reconcile
permissions, bootstrap the first administrator, and start the exact images. Do not run the fictional
demo seed in production.

After first login, set:

- website name: `Thibault Leveau`;
- public contact email: `thibault.leveau@gmail.com`;
- analytics provider: `None`;
- footer legal links: `/legal` and `/privacy`.

The privacy and legal routes read the public website name/email from the official site-configuration
API. They display an explicit incomplete state instead of silently publishing anonymous legal text.

## Local-media ownership

The `local-media` Docker volume is private application state, not disposable cache. The production
acknowledgement permits it only because this is a deliberate single-host deployment. Do not move,
delete, recreate, or prune the volume independently of its PostgreSQL records. Migrate to private
S3-compatible storage before adding another application host.

## Backup, retention, and recovery

- Enable Hostinger's [automatic weekly VPS backup](https://www.hostinger.com/support/1583232-how-to-back-up-or-restore-a-vps-at-hostinger/).
  Its documented default cadence matches the
  approved seven-day RPO, but the one-hour RTO remains unproven until a timed restore drill passes.
- Follow the coordinated backup procedure: capture PostgreSQL and `local-media` from one recorded
  cutoff. A whole-VPS snapshot does not replace the application-level consistency record.
- Schedule contact retention with 365 days and audit retention with seven days. Run both commands in
  dry-run mode first and alert `thibault.leveau@gmail.com` on non-zero exit.
- Before upgrades, take a recoverable application backup and an optional short-lived provider
  snapshot. Restore into isolation, verify migration head/media checksums, then test authenticated and
  public journeys before accepting the recovery objective.

Hostinger warns that restoring a VPS backup overwrites current server state. Never use the production
VPS as the first restore test.

## Promotion checklist

- DNS and automatic TLS pass for `https://thibault-leveau.com`;
- the Hostinger and OS firewalls expose only the intended ports;
- site identity, contact email, `/legal`, and `/privacy` render correctly;
- analytics remains disabled and no external error-reporting script is present;
- retention dry runs report the intended 365-day and seven-day cutoffs;
- a weekly backup exists and a timed isolated recovery meets the one-hour objective;
- the physical accessibility matrix is complete and all required rows pass.
