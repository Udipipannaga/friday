# Deployment, backups and portability

## Current verification boundary

The app runs locally on Windows with SQLite and an independent polling worker. On October 4, 2026, the application was also deployed privately to the owner's Hostinger VPS using Docker Compose, PostgreSQL, Redis and Celery. The API health check and Celery worker ping passed. A live PostgreSQL/API smoke check verified owner sessions, denied anonymous access, closed registration, and conversation persistence across service restarts. The deployed image passed 51 backend tests using SQLite fixtures and provider doubles; these do not establish live model performance or PostgreSQL concurrency behavior.

The API remains bound to server loopback, with no public website or HTTPS endpoint configured. The Windows browser tunnel has not been verified working. Model and search credentials remain unconfigured, so real AI chat and research have not passed acceptance testing. Off-host backups, restore drills, image security scanning and the remaining recovery/concurrency checks below are outstanding.

## GitHub and browser access

A private GitHub repository can hold the application source and deployment configuration. It does not replace the running VPS or create a public backend endpoint. Do not upload local databases, environment files, SSH keys, credentials, or the enclosing workspace's work directory. The existing `.gitignore` and source packaging exclude runtime data and dependencies.

To eliminate the localhost tunnel, configure a chosen domain with DNS pointing to the VPS, terminate HTTPS at a reverse proxy, and set the app origin and secure cookies accordingly. Keep the API, PostgreSQL and Redis behind the proxy/private network. Review authentication and access controls before public exposure. Never place the VPS root private key in the repository or an automated deployment workflow; any future CI deployment should use separately scoped credentials and explicit approvals.

## Docker Compose

Install a supported Docker engine/Compose on your chosen host. From the project root:

```powershell
Copy-Item .env.example .env
# Edit .env locally. Set a strong POSTGRES_PASSWORD, API key, explicit model ID, search key.
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=50 api worker scheduler migrate
```

Use a long URL-safe password (for example random hexadecimal) for `POSTGRES_PASSWORD`, because Compose embeds it in the database URL. Do not run `docker compose config` without `--quiet` in logs you might share: expanded environment values can contain secrets.

The migration service waits for PostgreSQL, runs Alembic and exits. The API and workers wait for migration completion. Redis is internal-only. The API binds to the host loopback interface on port 8000. Persistent named volumes hold PostgreSQL and Redis data. Redis uses append-only persistence, but PostgreSQL remains authoritative. Keep one scheduler replica; duplicate task dispatches are still guarded by database leases.

Health checks cover API/database/Redis. Use an actual test job and monitor worker/scheduler logs to establish execution readiness; API health alone is not a worker health guarantee.

## Cloud readiness checklist

1. Choose a host and cost envelope with user authorization. No GPU is required for hosted APIs.
2. Validate the exact image tags/locked packages on the deployment platform; scan images and rebuild for security updates.
3. Supply secrets through a secret manager or protected environment file. Use a strong database password and scoped API credentials.
4. Terminate TLS at a reverse proxy. Set `FRIDAY_ORIGIN=https://your-domain` and `FRIDAY_SECURE_COOKIE=true`. Add request/body/rate limits and authenticated operational access.
5. Keep database/Redis inaccessible from the public network. Add a public-only egress policy for retrieval and scoped provider endpoints.
6. Close open registration for a private installation after creating the owner account. Complete identity/recovery controls before public multi-user service.
7. Run the live acceptance checks in `verification.md`, including PostgreSQL concurrent submissions, broker outage, worker kill/restart and frontend closure.
8. Configure retention, encrypted backups, restore drills, resource monitoring and provider spending limits. Do not treat application request quotas as exact billing limits.

Once deployed to an always-running server, closing or switching off the laptop does not stop server tasks. The current local deployment still depends on this laptop being on. Future local-device tasks must wait for that device to reconnect.

## PostgreSQL backups and restore

Run these inside a secure terminal. On Windows, avoid binary shell redirection with older PowerShell; create the dump inside the container and copy it out:

```powershell
docker compose exec db pg_dump -U friday -d friday -Fc -f /tmp/friday.dump
docker compose cp db:/tmp/friday.dump ./friday.dump
```

Encrypt the dump, restrict access and store a second copy off-host. It contains account hashes, sessions, chats and source evidence. Redis backups are not a substitute for database backups.

Restore into a **new empty target database/installation** during a maintenance window. Do not overwrite a running production database without a reviewed recovery plan:

```powershell
docker compose cp ./friday.dump db:/tmp/friday.dump
docker compose exec db pg_restore -U friday -d friday --no-owner /tmp/friday.dump
docker compose run --rm migrate
```

Verify row counts, account isolation, saved reports, job terminal states and active leases before reconnecting clients. Restored session tokens may remain valid; plan session revocation for security incidents. Retain the previous installation until validation is complete.

## Local SQLite backup

Use SQLite's online backup API instead of copying a live `.db` without its WAL:

```powershell
cd backend
..\.venv\Scripts\python -c "import sqlite3; source=sqlite3.connect('friday.db'); target=sqlite3.connect('friday-backup.db'); source.backup(target); target.close(); source.close()"
```

Stop the local API/worker before restoring from a backup. Keep the original database in a separate recovery location rather than deleting it. Never place a backup in a public static directory.

## Moving to an owned server

The application code, lockfiles, migrations and Compose file are portable. For cloud-to-owned-server PostgreSQL migration: stop new submissions, drain/cancel active work, record uncertain provider requests, back up PostgreSQL, restore on the new host, supply new secrets, migrate, validate, then switch DNS. Revoke old credentials and retain a rollback backup.

Moving the optional SQLite development database into PostgreSQL needs a validated data migration/export utility; it is **not implemented**. Use PostgreSQL from the first cloud deployment to avoid that conversion. No vendor-specific hosted database or orchestration API is required by FRIDAY's persisted schema.
