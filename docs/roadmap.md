# Product roadmap and capability acceptance matrix

FRIDAY owns its product interface, user accounts, orchestration, durable state, permissions and artifacts. AI APIs remain replaceable dependencies. Capability categories are a reference, not a claim of model ownership, intelligence parity or benchmark performance.

## Stage 1 — current implementation

| Capability | Infrastructure and FRIDAY responsibility | Acceptance test | Status |
|---|---|---|---|
| Accounts | Argon2, database sessions, ownership and throttling | Register/login/logout; reject another user's resource IDs | Implemented; automated tests pass; no email verification/OAuth |
| Text conversation | Configured model API; FRIDAY context, persistence, UI, job cancellation | Ask, close/reopen, restart storage, resume history | Implemented; fixture E2E tested; live model unconfigured |
| Durable research | Brave Search, HTTPS pages, model synthesis; FRIDAY plan/checkpoints/sources/report | Start, close frontend, recover worker, inspect actual source-linked report | Implemented; fixture E2E + real-page retrieval tested; live search/model unconfigured |
| Activity and usage | Database events, reservations, reported tokens, job limits | Observe steps; exceed quota; interrupted usage shown uncertain | Implemented/tested locally; exact monetary cap not provided |
| Markdown artifacts | Database + authenticated download | Research report saved and retrievable only by owner | Implemented/tested; other artifact formats planned |
| Cloud operation | PostgreSQL, Celery, Redis, Docker Compose | Start containers, kill worker/Redis, recover without lost checkpoint | Configuration supplied; not run on this Windows host |

**Gate before expansion:** configure the model and search provider, validate real conversation + research end to end, and run the Compose/PostgreSQL/Celery recovery suite on a Docker-capable host. Then perform a private deployment review. Do not call this milestone fully live-verified until those checks pass.

## Stage 2 — voice and user-controlled memory

| Capability | Required work | Acceptance test | Status |
|---|---|---|---|
| Voice | Replaceable speech-to-text and speech generation; push-to-talk; permission/error states; stop playback; text fallback | Speak, interrupt playback, deny mic, recover; verify on Windows/mobile browsers | Planned |
| Personal memory | Separate explicit user-approved memory store; create/read/edit/delete; no secrets; basic retrieval first | Save an item, use in later chat, edit, delete and verify absence from retrieval/index | Planned |
| Conversation lifecycle | Verified identity, recovery, session inventory/revocation, account export/deletion | Verify email ownership; revoke session; export/delete data consistently | Planned; required before public registration |

No continuous recording, wake-word, locked-screen speech, emotional experience or automatically invented memories are claimed.

## Stage 3 — computer tools, engineering and richer artifacts

| Capability | Required work | Acceptance test | Status |
|---|---|---|---|
| Browser/computer tools | Isolated Playwright worker, typed tools, scoped credentials, screenshot/action logs, challenge handoff | Complete a sandbox task; stop at authentication/CAPTCHA; deny unauthorized destinations | Planned |
| Windows control | Separately installed authenticated companion; permission prompts; offline waiting state | Authorized local action works when awake; queues safely while offline; revoked device cannot act | Planned |
| Coding | Disposable workspaces/containers, constrained execution/network, diffs and test artifacts | Change a fixture repository, run meaningful tests, export diff; verify escape/secret denial | Planned |
| Mathematics/data analysis | Sandboxed computation and verified result artifacts | Reproduce a calculation with code and numeric checks | Planned; model-only chat is not a verified calculator |
| File analysis | Size/type checks, isolated parsers, provenance and retention controls | Analyze test documents with known answers; reject hostile/oversized inputs | Planned |
| Document/sheet/slide output | Dedicated generators and render/validation steps | Export real artifacts and verify content/layout/formulas | Planned |
| Vision and image generation | Capability-aware provider adapters, upload controls and separate image-generation tool | Analyze reference image; generate/export image; verify disclosure and limits | Planned |

## Stage 4 — specialist skills and service integrations

Implement a small typed skill registry: name, purpose, input/output schema, allowed tools, permission requirements, limits, completion checks. Start with research (current bounded implementation), planning and writing, then marketing, sales, deals, operations, support and back office. Engineering and Blender/creative integrations must each pass real tool acceptance tests.

Connect services through supported APIs/MCP with explicit user scopes and credential isolation. Before the first sending, posting, purchasing, booking, subscription or important deletion tool, implement backend approval records bound to exact actions, owners, expiry and one execution. Test altered/replayed/cross-user approvals and uncertain external outcomes. Draft-only skills may precede external writes.

Acceptance examples: a marketing plan with checked source material; lead research with inspectable evidence; a CRM update that rejects unapproved scopes; an outreach draft that cannot be sent without exact recipient/content approval; invoice extraction checked against a fixture invoice. All remain planned.

## Stage 5 — mobile and physical devices

Android/iOS clients (React Native + Expo subject to native requirements) share the API and durable server state. Phones are interfaces, not required background workers. Add short-lived pairing, per-device credentials, scoped memory access, revocation and reconnect synchronization. Then glasses, a talking-character watch and desk companion. Finally a robot with a separate constrained motion controller, physical safety mechanisms and independent hardware testing.

Acceptance: switch clients without losing history/project state; revoke a paired device and reject later calls; disconnected hardware cannot perform stale actions; verify emergency stop separately from language-model behavior. All native clients and device integrations remain planned.

## Continuation reconciliation (2026-10-03)

See [requirements-traceability.md](requirements-traceability.md) for all 330 tracked requirement blocks and [capabilities.md](capabilities.md) for current boundaries. Priority is unchanged: verify one real-provider persistent conversation and source-based durable research run before voice, memory, computer use or specialists. P1 live verification is blocked by credentials; P2 PostgreSQL/Compose acceptance is blocked by absent Docker. Track B prepares provenance and family-separated datasets only; no paid collection/training.
