# Deployment, backups and portability

## Current verification boundary

The app runs locally on Windows with SQLite and an independent polling worker. On October 4, 2026, the application was also deployed privately to the owner's Hostinger VPS using Docker Compose, PostgreSQL, Redis and Celery. The API health check and Celery worker ping passed. A live PostgreSQL/API smoke check verified owner sessions, denied anonymous access, closed registration, and conversation persistence across service restarts. The deployed image passed 51 backend tests using SQLite fixtures and provider doubles; these do not establish live model performance or PostgreSQL concurrency behavior.

On October 5, 2026, the VPS was also exposed through Caddy at `https://friday.srv2033118.hstgr.cloud`. Caddy obtained a publicly trusted certificate and off-host checks passed for the page, health endpoint, denied anonymous access, and closed registration. The Windows localhost tunnel remains unnecessary and unverified. Search credentials and live research acceptance testing remain outstanding. Off-host backups, restore drills, image security scanning and the remaining recovery/concurrency checks below are outstanding.

**October 13 domain cutover:** The Hostinger-managed `frieday.tech` apex A record points to the existing VPS at `72.62.192.125` (TTL 300). `www` remains a CNAME to the apex. Caddy serves `https://frieday.tech`; `www` and `friday.srv2033118.hstgr.cloud` issue permanent redirects to the apex. `FRIDAY_ORIGIN` in the protected VPS `.env` is `https://frieday.tech`. External HTTPS checks returned 200 for the page and health endpoint, 401 for anonymous private API access and a deliberately invalid login, and 301 for both redirect hosts. The owner's sign-in on the new origin was verified during the memory deployment; browser cookies from the old hostname did not transfer. The previous Caddyfile and environment file remain backed up on the VPS for rollback.

**October 13 memory deployment:** A root-only PostgreSQL dump and source archive were saved under `/opt/friday-backups` before deployment. The `005` migration created the personal memory table, and the API, worker and scheduler containers were rebuilt. All services were running; the API health endpoint returned 200 and anonymous memory access returned 401. The owner signed in on `frieday.tech` and opened the new empty Memory page. Local validation passed 70 backend tests, the frontend production build, and a scratch SQLite migration to `005`. The save/edit/delete/context lifecycle is covered by local API tests; it was not exercised against the owner's live data. Automatic extraction and semantic retrieval are not implemented.

**October 14 supplied-source research:** The Research form accepts up to five user-supplied public HTTPS page URLs, so this path does not require a Brave search key. The configured model remains necessary for synthesis. A PostgreSQL dump and source archive were saved under `/opt/friday-backups` before rebuilding API, worker and scheduler. All three restarted, and the API became healthy. In a disposable SQLite database using the deployed image, a real `https://example.com/` page was retrieved and the configured model completed a job with a saved report. An isolated memory save/context/delete check passed in the deployed image as well. These tests did not change the owner's production data or verify report factual accuracy, a browser-close owner research run, or PostgreSQL/Celery failure recovery.

**October 9 update:** The owner browser session and a live saved chat reply were verified over HTTPS. The configured third-party `qwen2.5:1.5b` model also produced 140 raw responses through a private direct Ollama collection path; they were not submitted through the FRIDAY web chat or job queue. The owner-only Human review page loads all 140, with zero human reviews and no accuracy score. Its raw queue and run manifest are mounted read-only at `/opt/friday/private-evaluation`, outside the public source repository; judgments go to PostgreSQL. The API database is at migration `004`, and the full backend suite passed 67 tests locally. A VPS backup and database dump were taken before deployment. This does not validate answer quality or the research workflow with live search credentials.

**October 11 update:** A separate AI first-pass issue screen marked 38 of the 140 responses for closer inspection. This triage is read-only, has no scores, and does not mark a case human-reviewed. Its private JSONL is mounted with the raw queue, outside GitHub. The owner page can filter to AI flags and shows each case's reason beside the ungraded response. The full backend suite passed 68 tests locally; production browser verification is recorded separately from these tests.

## GitHub and browser access

A GitHub repository holds the application source and deployment configuration; the VPS still runs the backend. The current repository is public at `https://github.com/Udipipannaga/friday`. Do not upload local databases, environment files, SSH keys, credentials, or the enclosing workspace's work directory. The existing `.gitignore` and source packaging exclude runtime data and dependencies.

The live VPS uses the Hostinger hostname above. Caddy terminates HTTPS; the API remains bound to server loopback and PostgreSQL/Redis are private to Docker. The runtime environment sets `FRIDAY_ORIGIN` to the HTTPS address, enables secure cookies, and closes registration. The owner's sign-in is still required on a new browser/origin. Do not place the VPS root private key in GitHub or an automated deployment workflow.

For a reviewed GitHub-source deployment, run `scripts/deploy-from-github.sh` on the VPS with the exact 40-character commit SHA after it has been pushed to `main`. The script verifies that `main` still points to that SHA, creates an immutable release under `/opt/friday-releases`, links the existing protected `/opt/friday/.env`, builds and starts Docker Compose, and checks HTTPS health. It does not store the private key in GitHub or automatically execute every push. A deployment is not complete until the public page and authenticated browser session are checked.

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

