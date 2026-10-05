# Architecture and retained direction

The prior FRIDAY specification was recovered from the earlier personal-agent conversation on 2026-10-03. Its independent-product direction, proposed stack, security rules and staged roadmap are retained. This project started empty; no prior code was replaced.

## Components

1. **React/TypeScript client:** FRIDAY branding, registration/sign-in, chat, research dashboard, configuration state and capability disclosures. It uses only FRIDAY APIs.
2. **FastAPI service:** authentication, resource ownership, limits, request idempotency, job submission, cancellation, state reads and artifact downloads. It never waits for research or model completion inside the submit request.
3. **SQLAlchemy storage:** PostgreSQL in deployment; SQLite for local Windows execution/tests. Accounts, sessions, conversations, messages, jobs, checkpoints, source evidence, artifacts, events and usage reservations are authoritative here. Alembic migration `001` freezes the initial schema.
4. **Worker:** Celery for deployment. Celery Beat dispatches eligible database jobs every five seconds. Losing a broker message does not erase job state. Windows local mode polls the same execution engine in a separate Python process without Redis.
5. **Provider protocol:** `ModelProvider.complete(messages, on_text)` returns text and provider-reported usage. Only the OpenAI adapter is implemented. Future adapters must declare and test capability differences; a compatible-looking URL alone does not establish support.
6. **Research retrieval:** Brave Search adapter discovers candidates. The retriever fetches public HTTPS page bodies with address checks, pinned connections and bounded downloads. Search snippets are never passed off as verified page evidence.
7. **Progress delivery:** reconnectable reads from persistent state; one-second chat polling and 1.5-second project polling. This simpler transport avoids ephemeral-only event loss. SSE/WebSocket delivery can be added without changing the durable record.

## Execution semantics

Submission atomically saves a job and reserves a daily job quota unit. A unique `(user_id, request_key)` prevents duplicate submissions. User-row updates serialize quota and active-job checks. One response per conversation can execute at a time.

Workers atomically claim a job with an expiring lease token. Every checkpoint checks the token, running state and deadline while holding a write lock. Cancellation invalidates the lease. Old workers cannot publish stale output. SQLite serializes writes; production PostgreSQL behavior still requires integration verification.

Research checkpoints are plan → search → each retrieved source → model output → validated artifact. Completed page downloads are not repeated after recovery. Search errors retry at most three times with exponential backoff; each attempt persists. All-inaccessible evidence produces failure, never an invented report.

Before a model call, a unique usage reservation is committed. If the worker dies after that reservation but before the model result checkpoint, recovery records an uncertain outcome and fails rather than automatically charging again. If the output checkpoint exists, finalization resumes without another model call. This is an intentionally conservative **at-most-one attempted model call per job**, not an exactly-once external execution guarantee. A crash before actually sending the reserved call may also require a manual new request.

Cancellation is cooperative. Already-issued network requests may finish or incur charges, but cannot publish results after cancellation. Queued/running are the only active states. No fake pause, resume or approval-wait states are exposed.

## Research evidence

The model receives a JSON envelope containing the question and extracted source text. It has no action tools. It is instructed to treat pages as data. It returns findings with source numbers and exact evidence excerpts. FRIDAY rejects unknown source IDs, unmatched excerpts and generated HTTP URLs; final source links are constructed from stored retrieval records. This validates provenance, not the correctness of every inference. A human should review consequential conclusions.

Reports and history are stored in the FRIDAY database. Provider storage is disabled in the Responses request; this does not independently determine the provider's retention policy. Report Markdown is downloadable. Raw HTML is never rendered. Sources may contain personal information; deployment operators must set retention and backup policies.

## Bounds and future extension points

Per account: 30 new jobs per UTC day and three active jobs by default. Per conversation: one active response. Context: at most 20 latest messages / 30,000 characters. Research: one search request per attempt, five pages, 1 MB/page, extracted text at most 12,000 characters/page. Model output: configured maximum (default 3,000 tokens). Job total age: 900 seconds checked at checkpoints. Cloud worker hard kill: 700 seconds per delivery. Leases: 180 seconds, renewed at checkpoints/stream updates.

Future memory must be distinct from history and project state. Future skills require typed input/output, allowed tools, permissions, budgets and completion checks. Future consequential actions must be gated in backend code by exact, expiring, single-use approvals. Future devices use short-lived pairing challenges and scoped, revocable credentials. Robot movement remains a separate constrained control system with physical safeguards.
