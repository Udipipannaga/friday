# Verification record — 2026-10-03

## Completed on this Windows host

- Backend: **47 automated tests passed** with Python 3.14. Tests exercise SQLite, real FastAPI routes and the production execution engine.
- Frontend: ESLint, TypeScript strict check and Vite production build passed. `npm install` audit reported zero known vulnerabilities in the resolved frontend dependencies at install time; this is not a security audit.
- Browser: **one multi-step Playwright/Edge integration test passed**. It registers a disposable test account, sends a fixture model message, reloads and reopens history, submits research, closes the browser page, reconnects using the session, verifies the completed report/download link, and checks mobile navigation without horizontal overflow. The personal account email is only checked as a prefilled value.
- Process recovery: a child process checkpoints source evidence and exits abruptly; a separate process resumes and completes without fetching that source again. Lease expiry is deliberately forced in the fixture to avoid a three-minute test delay.
- Live network: the production pinned-IP HTTPS retriever fetched `https://example.com`, extracted the title `Example Domain` and 171 text characters.
- Alembic: initial migration applied to local development and isolated E2E databases; `alembic check` reported no schema drift.
- Desktop and mobile screenshots inspected visually. UI is usable at 1280×720 and 390×844.
- Windows launcher: `Start-Friday.ps1 -Install` completed dependency installation, frontend build and migrations, then started the local API and independent worker. It uses project-local package caches to avoid restricted home-directory writes.

The test environment produces one Starlette warning about future test-client migration from `httpx` to `httpx2`. Tests pass; this warning does not establish future compatibility. Dependency upgrades should rerun the suite.

## Interactive interface follow-up

After the redesign, lint, TypeScript/build and the browser workflow passed again. The browser test now also checks keyboard command search, appearance selection and persistence, motion toggling, orbital animation pause, focus mode, message copying, and project filters. Desktop/mobile visual inspection and artwork HTTP 200 checks passed without browser page errors. The requested local owner account's login and profile lookup were verified, then the test session was logged out. No password was saved in source files.

## What the tests actually establish

Account ownership checks reject cross-account reads, sends, cancellation and downloads. Passwords are hashed, CSRF/origin checks reject foreign requests, sessions expire and logout revokes them. Missing model keys return setup errors without consuming quota.

Conversations survive engine recreation. Submission returns without waiting for work. Duplicate idempotency keys do not double-reserve quotas, changed parameters are rejected, cancellation blocks future commits/model calls, one claimant wins a concurrent lease race, stale workers cannot write, search retries stop at three, interrupted model calls are not replayed, saved model output can be finalized after recovery, inaccessible evidence never reaches synthesis, and fabricated citation IDs are rejected.

URL tests cover forbidden schemes, credentials, ports, control characters, backslashes, loopback/private/link-local/reserved/multicast addresses, mixed public/private DNS and redirects into private networks. Provider contract tests exercise Responses request shape, streamed text and usage parsing, and sanitized 401/429/500 errors using HTTP fixtures.

## Explicitly unverified or unavailable

- **Live OpenAI model access and conversation quality:** no API key or explicit model configured.
- **Live Brave Search and complete real-source/model research:** no search key configured. The browser integration used clearly labeled test fixtures for search, page content and model output. It does not prove live model synthesis quality.
- **PostgreSQL, Redis, Celery and Docker startup/failover:** Docker is absent on this host. SQLite/local-worker results must not be described as those integration tests.
- **Public hosting, verified identity, voice, long-term memory, computer control, coding sandboxes, additional artifact formats, integrations and devices:** not implemented/deployed/tested.
- No performance comparison or model-equivalence benchmark was run.

## Reproduce the fixture browser test

Use three terminals, with the project root `.venv` installed and frontend already built. The fixture key strings below are not valid API credentials and are used only in an isolated test database.

API terminal, from `backend`:

```powershell
$env:FRIDAY_DATABASE_URL='sqlite:///./friday-e2e.db'
$env:FRIDAY_ORIGIN='http://localhost:8011'
$env:FRIDAY_API_KEY='test-fixture-not-a-key'
$env:FRIDAY_MODEL='fixture-model'
$env:FRIDAY_SEARCH_KEY='test-fixture-not-a-key'
..\.venv\Scripts\python -m alembic upgrade head
..\.venv\Scripts\python -m uvicorn friday.api:app --host 127.0.0.1 --port 8011 --no-access-log
```

Worker terminal, from the same `backend` directory:

```powershell
$env:FRIDAY_DATABASE_URL='sqlite:///./friday-e2e.db'
$env:FRIDAY_E2E_FIXTURES='1'
..\.venv\Scripts\python -m tests.e2e_worker
```

Browser terminal, from `frontend` (Microsoft Edge installed):

```powershell
npm run test:e2e
```

These fixture processes must never point at a real account database. The worker refuses to run unless explicitly enabled and the database URL contains `e2e`. There is no production configuration option to select its fake model.

## Live milestone acceptance gate

1. Configure real provider credentials and an accessible explicit model in the local `.env`; restart services. Set provider spending limits separately.
2. Create your FRIDAY account and send a real conversation. Reopen it after API/worker restart. Inspect provider-reported usage.
3. Submit a factual research question with multiple accessible public sources. Close all browser tabs. Reopen the project and verify the report's cited URLs, retrieval timestamps and source content against actual pages. Assess correctness, not only successful completion.
4. Kill/restart the worker during retrieval; verify completed sources are reused. Kill it during a model call; verify uncertainty is surfaced and not automatically replayed.
5. Repeat cancellation, duplicate submission, quotas and cross-user isolation on PostgreSQL.
6. Stop Redis and restart it; confirm database jobs recover. Run `docker compose config --quiet`, build and health checks on a Docker-capable host.
7. Record results and limitations here before declaring the milestone live-verified or advancing to voice/memory.

## Continuation acceptance update (supersedes earlier UI test description)

- Backend: 51 tests passed on SQLite; includes capability metadata and rejection of unknown adapters, access lifecycle and prior durable research/security cases. One Starlette test-client deprecation warning remains.
- Training curation: 12 standard-library tests passed, including permission/consent rejection, secret detection, duplicate/family leakage checks, and exact binding of exported train/validation data to reviewed provenance. Not a legal or semantic correctness audit.
- Frontend: lint and TypeScript/Vite build passed. Updated Playwright/Edge workflow passed (1 test, 7.0 seconds test time) against isolated `friday-reconcile-e2e.db`, fixture model/search/source and independent test worker on port 8011. It covers persistent chat, close/reopen during research, report, navigation, appearance and mobile reduced motion. Fixture-only API registration is explicitly enabled; production public signup remains closed.
- Live provider/search/GPU training: NOT RUN. No funds spent; no private or restricted data collection. PostgreSQL/Redis/Celery Compose: untested because Docker is unavailable here.

Next exact local regression commands: from backend, `../.venv/Scripts/python.exe -m pytest tests -q`; from frontend, `npm run build` and `npm run lint`. Tests may need a writable `--basetemp` on this restricted Windows host. To perform live acceptance, privately configure `FRIDAY_API_KEY`, `FRIDAY_MODEL`, and `FRIDAY_SEARCH_KEY` in backend/.env, restart with Start-Friday.ps1, then follow the live acceptance gate above. Do not paste credentials into chat. A future self-hosted checkpoint requires an installed provider adapter; unsupported provider names fail closed.

### Fixture test update

For the test API only, set `FRIDAY_REGISTRATION_OPEN=true`. The updated test creates a disposable account through the isolated test API, because the production interface no longer offers public registration. Never enable this on the actual private instance. The current command center replaces the old cinematic chapter selectors.

## Real unchanged-model inference baseline (2026-10-03)

A user-authorized Colab T4 run of Qwen2.5-0.5B-Instruct completed on five synthetic prompts using existing compute credits. Results: arithmetic correct; tool choice correct but format wrong; permission and uncertain-delivery answers failed; planning generic. No weights were trained or promoted. Runtime disconnected after completion. See ../../friday-training/BASELINE-RESULTS.md for model revision and observed environment. This does not unblock live app chat/research or constitute a training run.

## Task-diagnostic preparation

Added 12 planning/research/writing development cases and an offline structural answer checker. Training-kit unit suite: 19 tests passed (seven new checker tests). No model run for these cases, no extra GPU credits, and no approved training-data collection. Free-text truth/safety remains a human review requirement. See ../../friday-training/task-evaluation/README.md.
