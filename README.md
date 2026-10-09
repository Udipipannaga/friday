# FRIDAY

An independent AI application with its own accounts, conversations, project state, background workers and interface. No ChatGPT UI or account is required. Third-party models are replaceable infrastructure; FRIDAY does not own those models or claim performance parity with ChatGPT/Astra.

**Current private prototype:** persistent chat and durable, source-based research are implemented, with a limited deterministic physics checker and an owner-only company operating desk. The app is deployed to the owner's Hostinger VPS; its authenticated owner session, a live chat reply, and QuiCut weekly-note workflow were verified on October 9, 2026. This is not a complete product or a validated model. The sign-in screen prefills `udipi.adithya@gmail.com`. At the owner's request, that account was created locally and its password hash was brought to the VPS. The source package contains neither the account database nor the password. Email ownership is not verified, and Gmail/Google OAuth is not connected.

The [interactive interface](docs/interface.md) includes Higgsfield-generated orbital artwork, a Ctrl/Cmd+K command palette, focus mode, prompt chips, message copying, research filters, accent choices and reduced-motion controls.

The hosted private instance is at [https://friday.srv2033118.hstgr.cloud](https://friday.srv2033118.hstgr.cloud). New visitors can request access; only the owner can approve and issue invitations. Public self-registration is closed. The GitHub repository holds source and reviewed deployment files; the running database and secrets stay on the VPS. See [deployment status](docs/deployment.md).

## Start on Windows

Prerequisites: Python 3.14, Node.js 24, npm. Run from this folder:

```powershell
.\Start-Friday.ps1 -Install
```

Open http://localhost:8000. The script creates a Python environment, installs locked dependencies, builds the frontend, migrates a local SQLite database, and runs the API plus an independent worker. On later launches use `./Start-Friday.ps1`. Keep this terminal open. Closing the browser is safe; stopping the server or turning off the laptop stops local execution until restart.

The script copies `.env.example` to `backend/.env` if absent. Configure these **in that file, never in a conversation**:

```dotenv
FRIDAY_PROVIDER=openai
FRIDAY_MODEL=your-accessible-model-id
FRIDAY_API_KEY=your-provider-key
FRIDAY_SEARCH_KEY=your-brave-search-key
FRIDAY_ORIGIN=http://localhost:8000
```

Restart the API and worker after changing configuration. There is deliberately no default model or silent fallback. Model access, pricing, capabilities and account eligibility must be checked against your provider account. API use can incur charges; daily request counts and output limits are not a provider-level spending cap.

Without keys, accounts, sign-in, saved conversation containers, settings, and capability status work. AI submissions return a setup error; **no mock model is enabled in the application**. Existing messages/projects can still be reopened if present.

## What is implemented

- Argon2 password hashing; hashed, expiring server-side sessions; strict cookies; same-origin request checks; persisted login throttling.
- Ownership checks for conversations, jobs, sources and artifacts.
- Stored conversation history and a configurable OpenAI Responses adapter behind a provider protocol. Partial model output is saved and polled by the UI every second; it is not a direct browser-to-provider stream.
- Database-backed chat and research jobs. A standalone local worker or Celery worker executes them independently of the frontend.
- Research: deterministic bounded plan, Brave Search, up to five public HTTPS pages, text extraction, evidence metadata, synthesis, citation/evidence validation, saved Markdown report.
- Persisted activity, quotas, execution leases, cancellation, bounded search retries, recovery from completed checkpoints.
- Dark responsive React interface, chat search, project dashboard, source links, report download and truthful setup states.
- Authenticated, unit-aware `POST /api/physics/check` for one static wing lift-versus-weight calculation. It uses a deterministic formula, not an AI model, and is not a flight-safety simulation. See [physics learning](docs/physics-learning.md) for the narrow scope and evaluation fixtures.
- Owner-only company desks with separate company/person/job records, QuiCut creator-video and real-job gates, five draft-only operating tools, and a persistent request/result/draft log. The tools use validated templates rather than model generation. No send, pay, delete, or price-change action exists in this desk.
- Owner-only Human review page for the 140 saved raw responses from the configured third-party `qwen2.5:1.5b` model. It stores reference checks and manual judgments in FRIDAY's database, separately from immutable raw responses, and allows a private JSONL export. The reference answers were AI-generated and require independent checking. Zero responses were human-reviewed when this page launched; **there is no accuracy score**. The private queue and manifest are mounted read-only on the VPS and excluded from GitHub.

## Verification and limits

See [docs/verification.md](docs/verification.md) for test boundaries and [docs/deployment.md](docs/deployment.md) for deployment status. Fixtures test model/search contracts and orchestration; they are not live provider validation. A real public HTTPS page was retrieved successfully. Docker is absent on the Windows development host. On October 9, 2026, the full backend suite passed 67 tests, the frontend production build passed, the VPS database migrated to revision `004`, and the authenticated owner browser verified QuiCut's persistent draft log and the 140-case Human review page. A live chat reply was saved, but its correctness was not measured. The physics checker has automated API and unit tests; its model-training/evaluation fixtures are not evidence of any fine-tuned model.

Browser voice playback and dictation are available where supported. Long-term conversational memory, live camera/vision, gesture control, computer use, coding sandboxes, file analysis, additional artifact formats, business integrations, completed owner approval/send/payment workflows, native mobile apps and devices remain planned. Operating-desk person and company records are a narrow structured memory only. Physics dataset preparation is separate from model training; no FRIDAY physics checkpoint or 140-question accuracy score exists. See [docs/roadmap.md](docs/roadmap.md). This milestone has no messaging, purchasing, booking, shell or computer-control tools.

## Development and tests

With `.venv` installed at the project root:

```powershell
cd backend
..\.venv\Scripts\python -m alembic upgrade head
..\.venv\Scripts\python -m pytest -q --timeout=30
..\.venv\Scripts\python -m uvicorn friday.api:app --host 127.0.0.1 --port 8000 --no-access-log
# Another terminal, same backend directory:
..\.venv\Scripts\python -m friday.execution
# Optional frontend hot reload, another terminal:
cd ..\frontend
npm ci
npm run dev
```

For Vite development, set `FRIDAY_ORIGIN=http://localhost:5173` and visit that exact origin. The proxy forwards `/api` to port 8000. For the compiled app, use origin `http://localhost:8000`. Do not mix `localhost` and `127.0.0.1` in browser origins.

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
```

The frontend uses Vite's native config loader for compatibility with this Windows environment; Node 24 is required. Full dependency versions are committed in `frontend/package-lock.json` and `backend/requirements.lock.txt`.

Browser integration tests use an explicit, isolated fixture worker; see `docs/verification.md`. They never create your personal account or send requests to a paid model.

## Portable deployment

The retained deployment stack is React/TypeScript + FastAPI + PostgreSQL + Celery/Redis. SQLite and the polling worker are a Windows development convenience only. See [docs/deployment.md](docs/deployment.md) for Docker Compose, backups, cloud preparation and migration. The owner-provided Hostinger VPS currently serves the sign-in page publicly over HTTPS.

## Troubleshooting

- **Setup error:** set model and service keys in the server `.env`, then restart both processes.
- **Queued indefinitely:** start a worker. With Docker, both `scheduler` and `worker` must be healthy. Jobs remain in the database if Redis is unavailable.
- **Origin rejected:** match the browser URL to `FRIDAY_ORIGIN`. Requests require the `X-Friday-Request: 1` header.
- **Uncertain model outcome:** inspect your provider usage. FRIDAY intentionally does not automatically replay a potentially billed call. A new request consumes a new quota unit.
- **No accessible evidence:** the report is not fabricated. Try a narrower question; dynamic pages, PDFs and paywalls are unsupported in this milestone.
- **Terminal failure:** see project activity. Retrying creates a new project and can incur another provider charge.

Technical references used for the integration: [OpenAI text generation](https://developers.openai.com/api/docs/guides/text), [OpenAI streaming](https://developers.openai.com/api/docs/guides/streaming-responses), [Brave Web Search](https://api-dashboard.search.brave.com/api-reference/web/search/get), [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html), [Celery tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html), and [FastAPI containers](https://fastapi.tiangolo.com/deployment/docker/).

## Complete-requirements reconciliation

The private-owner product direction remains in force. See `docs/requirements-traceability.md` (330 tracked blocks across all 29 sections), `docs/capabilities.md`, `docs/training-plan.md`, and `docs/data-provenance.md`. The current owner-only operating desk was browser-tested on October 9, 2026; live model and search execution still require separate verification. No trained FRIDAY checkpoint exists. The earlier browser test referred to an older public-signup UI and must not be cited as proof of the current invitation-only workflow.
