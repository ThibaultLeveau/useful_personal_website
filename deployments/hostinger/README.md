# Publish the application images and deploy them with Portainer

This is the production procedure for `https://thibault-leveau.com`. It uses GitHub Container
Registry (GHCR) to store the Docker images and a Portainer **Stack** on the Hostinger VPS to pull and
start them.

The application has two images:

- `ghcr.io/thibaultleveau/useful-personal-website-backend`
- `ghcr.io/thibaultleveau/useful-personal-website-frontend`

PostgreSQL and Caddy use their official registry images. Caddy is included in the stack and obtains
the HTTPS certificate automatically after DNS and ports 80/443 are correct.

## Before starting

You need:

1. Docker Desktop running on the computer containing this repository.
2. This deployment directory committed and pushed to the GitHub `main` branch. Portainer clones the
   repository because the stack also needs the versioned PostgreSQL permission scripts and Caddy
   configuration; do not use Portainer's Web editor or file-upload option for this stack. In
   Portainer versions that show **Enable relative path volumes** for Git stacks, enable it. The
   Compose file uses repository-relative bind mounts; without that option Docker may mount an empty
   directory and the database operation containers will report that their scripts do not exist.
3. A Hostinger VPS with Docker and Portainer already running.
4. The DNS `A` record for `thibault-leveau.com` pointing to the public IPv4 address of the VPS.
5. TCP ports 80 and 443, and UDP port 443, allowed in the Hostinger and operating-system firewalls.
   Restrict SSH to trusted source addresses. Do not expose PostgreSQL, 3000, or 8000.
6. Nothing else on the VPS listening on ports 80 or 443. If another reverse proxy already owns
   those ports, stop here and integrate the application with that proxy instead of deploying the
   included Caddy service.

Hostinger documents its [Docker VPS template](https://www.hostinger.com/support/8306612-how-to-use-the-docker-vps-template-at-hostinger/)
and [managed firewall](https://www.hostinger.com/support/8172641-how-to-use-a-managed-vps-firewall-at-hostinger/).

## 1. Build and upload both Docker images

GitHub's registry is used because the source repository already belongs to `ThibaultLeveau`. The
commands below run in PowerShell from the repository root.

### 1.1 Create a GitHub package token once

In GitHub, open **Settings → Developer settings → Personal access tokens → Tokens (classic)** and
create a token with `write:packages`. Store it in your password manager. Do not place it in this
repository or an environment file.

Sign Docker into GHCR. Paste the token at the password prompt; the prompt does not display it:

```powershell
docker login ghcr.io --username ThibaultLeveau
```

GitHub documents the token scopes and `docker login` flow in its
[Container registry guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

### 1.2 Choose an immutable release tag

```powershell
$FullCommit = git rev-parse HEAD
$ShortCommit = git rev-parse --short HEAD
$ImageTag = "1.0.0-$ShortCommit"
$ImageTag
```

Keep the printed tag. You will enter the same value in Portainer. A version-plus-commit tag is used
instead of `latest` so a redeployment cannot silently download different code.

### 1.3 Build and push the backend

```powershell
docker buildx build `
  --platform linux/amd64 `
  --file backend/Dockerfile `
  --target runtime `
  --label "org.opencontainers.image.source=https://github.com/ThibaultLeveau/useful_personal_website" `
  --label "org.opencontainers.image.revision=$FullCommit" `
  --tag "ghcr.io/thibaultleveau/useful-personal-website-backend:$ImageTag" `
  --push .
```

### 1.4 Build and push the frontend

```powershell
docker buildx build `
  --platform linux/amd64 `
  --file frontend/Dockerfile `
  --target runtime `
  --label "org.opencontainers.image.source=https://github.com/ThibaultLeveau/useful_personal_website" `
  --label "org.opencontainers.image.revision=$FullCommit" `
  --tag "ghcr.io/thibaultleveau/useful-personal-website-frontend:$ImageTag" `
  --push .
```

These commands upload Linux/AMD64 images, which is the normal Hostinger VPS architecture. Confirm
with `uname -m` over SSH: `x86_64` means the commands above are correct. Stop and build for
`linux/arm64` instead if the VPS reports `aarch64` or `arm64`.

### 1.5 Make the two packages public

The first command-line push creates private packages by default. On GitHub, open your profile,
select **Packages**, open each new package, then **Package settings → Change visibility → Public**.

Public images match this open-source project and let Portainer pull them without storing a GitHub
token. GitHub confirms that public GHCR packages support anonymous pulls. If you intentionally keep
them private, add `ghcr.io` as a custom registry in Portainer with username `ThibaultLeveau` and a
separate classic token having only `read:packages`.

## 2. Generate the private Portainer environment file

Use the exact `$ImageTag` from the build step:

```powershell
.\deployments\portainer\New-PortainerEnvironment.ps1 -ImageTag $ImageTag
```

This creates `deployments/portainer/portainer.env` containing independent cryptographically random
database passwords and application keys, plus the exact Git commit. Git ignores this file. Keep it
private: anyone with it can access or impersonate production services.

Do not manually reuse one password for several fields. Do not upload
`portainer.env.example`; it intentionally contains blank placeholders.

## 3. Create the stack in Portainer

1. Sign in to Portainer on the VPS and open the local **Docker Standalone** environment.
2. Select **Stacks → Add stack**.
3. Name the stack `useful-personal-website`.
4. Select **Git repository**.
5. Enter repository URL
   `https://github.com/ThibaultLeveau/useful_personal_website.git`.
6. Set the repository reference to `refs/heads/main`.
7. Set the Compose path to `deployments/portainer/compose.yaml`.
8. In **Environment variables**, choose **Load variables from .env file** and select the private
   `deployments/portainer/portainer.env` file generated above.
9. Confirm that `IMAGE_TAG` is the tag uploaded in step 1.
10. Click **Deploy the stack**.

Before deploying, verify that the Portainer Git-stack form either has **Enable relative path
volumes** enabled or documents an equivalent way to expose the cloned repository to the Docker
daemon. Do not continue with this Compose file if that capability is unavailable. The PostgreSQL
jobs require `../../infrastructure/postgres` and Caddy requires `./Caddyfile`; both are repository
files, not named Docker volumes.

Portainer documents this Git/Compose flow and environment-file upload in its
[stack deployment guide](https://docs.portainer.io/sts/user/docker/stacks/add). Portainer clones the
entire repository, then pulls the two application images from GHCR; it does not rebuild them on the
VPS.

The first deployment runs in this order:

1. PostgreSQL starts and becomes healthy.
2. Database roles are created or reconciled.
3. Alembic migrations reach the exact schema head.
4. Runtime permissions are reconciled and checked.
5. The private media volume is initialized.
6. Backend and frontend become healthy.
7. Caddy starts and obtains the TLS certificate.

In Portainer, `postgres`, `backend`, `frontend`, and `caddy` should remain **running**. The
`role-init`, `migrate`, `permissions`, `permissions-check`, and `media-init` containers should finish
with exit code `0`; their **exited** state is expected because they are one-shot safety jobs.

If deployment fails, open the first failed one-shot container and read its logs. Do not bypass a
migration or permission failure.

### Existing-volume password mismatch

The PostgreSQL image stores the bootstrap password and all reconciled role passwords in
`useful-personal-website-postgres-data`. Generating a new `portainer.env` does **not** change
passwords in an existing volume. If `migrate` reports `InvalidPasswordError` for
`useful_migration_owner` or `backend` reports it for `useful_runtime`, first determine whether the
stack was deployed before or whether a new environment file was uploaded.

If the database and media contain no data that must be preserved, remove the stack and delete these
two named volumes before redeploying:

```sh
docker volume rm useful-personal-website-postgres-data useful-personal-website-local-media
```

Run this only after confirming the volumes are disposable. Never delete `postgres-data` as a routine
update. If data must be preserved, restore the original environment file or use an approved
PostgreSQL operator procedure to regain the bootstrap role; do not keep guessing passwords and do
not edit PostgreSQL authentication files ad hoc.

For a non-destructive diagnosis over SSH, use:

```sh
docker ps -a --filter label=com.docker.compose.project=useful-personal-website \
  --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
docker volume inspect useful-personal-website-postgres-data \
  --format 'created={{.CreatedAt}} mount={{.Mountpoint}} labels={{json .Labels}}'
```

Do not include `docker inspect` environment output in support requests because it contains secrets.

## 4. Create the first administrator

The application deliberately has no default login. Connect to the VPS over SSH and run:

```sh
read -r -s -p "Temporary administrator password: " bootstrap_password
printf '\n'
printf '%s\n' "$bootstrap_password" | docker exec -i \
  -e APP_BOOTSTRAP_ADMIN_EMAIL='thibault.leveau@gmail.com' \
  -e APP_BOOTSTRAP_ADMIN_DISPLAY_NAME='Thibault Leveau' \
  useful-personal-website-backend \
  python -m app.commands.bootstrap_admin --password-stdin
unset bootstrap_password
```

Use a unique temporary password of at least 12 characters from your password manager. It is not
displayed, stored in shell history, or added to Portainer. The command is takeover-safe and refuses
to create a second initial administrator.

Open `https://thibault-leveau.com/admin/login`, sign in, and immediately choose a new private
password when requested. Then configure:

- website name: `Thibault Leveau`;
- public contact email: `thibault.leveau@gmail.com`;
- analytics provider: `None`;
- footer legal links: `/legal` and `/privacy`.

Verify these URLs:

- `https://thibault-leveau.com/`
- `https://thibault-leveau.com/api/v1/health/live`
- `https://thibault-leveau.com/api/v1/health/ready`
- `https://thibault-leveau.com/legal`
- `https://thibault-leveau.com/privacy`

## 5. Back up before considering production complete

Enable Hostinger's [automatic weekly VPS backup](https://www.hostinger.com/support/1583232-how-to-back-up-or-restore-a-vps-at-hostinger/).
The persistent volumes are deliberately named:

- `useful-personal-website-postgres-data`
- `useful-personal-website-local-media`
- `useful-personal-website-caddy-data`

The PostgreSQL and media volumes form one recovery point and must be backed up together. Perform the
first restore into an isolated test location and time it; the one-hour recovery objective is not
proven merely by enabling weekly backups. Hostinger warns that restoring a VPS backup overwrites the
current server state.

## Updating the application later

1. Back up PostgreSQL and media.
2. Pull the reviewed source commit locally.
3. choose a new version-plus-commit image tag.
4. Build and push both images with the commands in step 1.
5. In Portainer, edit the stack environment variable `IMAGE_TAG`.
6. Update/redeploy the stack with image re-pull enabled.
7. Confirm all migration/permission jobs exit `0` and all four long-running services become healthy.

Never overwrite an existing release tag and never delete the two application data volumes during a
routine update.
