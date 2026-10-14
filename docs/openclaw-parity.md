# FRIDAY as a private OpenClaw-class operating agent

The target is functional breadth comparable to OpenClaw under FRIDAY's own brand, accounts, company desks, memory, and owner approval policy. OpenClaw is MIT-licensed infrastructure, not a FRIDAY-owned model. REA provided partial static evidence for the previous weekly scheduler adaptation; it did not prove runtime parity. The upstream OpenClaw source and Gateway are the authoritative implementation references.

## Runtime boundary

FRIDAY remains the only user-facing product. Its database owns accounts, access requests, conversation records, explicit memories, jobs, drafts, audit entries and usage limits. The OpenClaw Gateway is an optional replaceable agent engine behind a private internal endpoint. A third-party channel or device must authenticate to FRIDAY before it can act for a FRIDAY user; Gateway bearer tokens never reach a browser, phone, or team member.

The new `openclaw` model-provider adapter calls Gateway `/v1/chat/completions` and explicitly selects FRIDAY's `FRIDAY_MODEL` with `x-openclaw-model`. It rejects missing credentials, non-private Gateway URLs, empty/incomplete responses and client tool-call responses. It is **not active in production**. Enabling it requires a configured private Gateway and a reviewed restricted agent policy. The Gateway HTTP token carries operator authority, so network isolation alone is insufficient.

## Capability ledger

| Area | FRIDAY now | Parity work and acceptance test |
|---|---|---|
| Persistent chat and owner/team access | Implemented | Keep FRIDAY identity, session, and conversation ownership. Test owner and approved member isolation. |
| Durable background tasks | Research jobs and owner-enabled weekly draft | Add cancellation, progress receipts, recovery, and arbitrary bounded tasks. Test worker crash/restart and no duplicate external action. |
| Memory | Explicit user-controlled records | Add provenance, edit/delete, retrieval boundaries per user/company. Test deletion removes future recall. |
| Skills and tools | Five draft-only operating tools and narrow physics checker | Introduce signed/allowlisted tool manifests, typed input validation, and per-tool approval. Test unauthorized send/pay/shell denial. |
| Browser and computer | Planned | Run in isolated browser/desktop workers with scoped credentials and recorded actions. Test permission and teardown. |
| Coding | Planned | Ephemeral container/worktree per job, resource/network limits, reviewable diff and owner approval before merge/deploy. Test escape and cleanup. |
| Channels and devices | FRIDAY website only | Pair channel/device identities to FRIDAY users; no shared Gateway token. Test revocation and company separation. |
| Voice | Browser dictation and speech synthesis | Add duplex audio sessions and voice state, with consent and transcript controls. Test a complete spoken task. |
| Business integrations | Planned | Connect one service at a time with least-privilege credential storage and human approval for customer-visible/money actions. Test real sandbox transactions. |
| Model evaluation | NOT_RUN for the 140-question human-reviewed score | Record FRIDAY-only raw responses, then human review. No score before both exist. |

## Ordered integration gates

1. Run a pinned OpenClaw Gateway privately in an isolated container. Configure its model to match FRIDAY Settings. Explicitly disable channel startup, unsafe host execution, and unreviewed plugins. Confirm a real model reply, then test FRIDAY's adapter end to end. **Lab acceptance passed for one text reply; production cutover is pending gate 2.**
2. Add a Gateway lifecycle/approval bridge. FRIDAY must log tool proposal, policy decision, approval identity and result before any side effect. Shared-secret HTTP mode is owner-equivalent, so never route member traffic to a shared powerful agent.
3. Add browser, coding, skills, and connectors in separate sandboxes, each with a real acceptance workflow and a visible `planned`/`configured`/`tested` state.
4. Add channel/device clients only after per-user pairing, revocation, and privacy tests. Keep FRIDAY's UI as the primary surface.

Upstream references: [repository and license](https://github.com/openclaw/openclaw), [external app integration](https://docs.openclaw.ai/gateway/external-apps), [HTTP endpoint and its operator security boundary](https://docs.openclaw.ai/gateway/openai-http-api), [sandboxing](https://docs.openclaw.ai/gateway/sandboxing).

## Evidence from this pass

The official `ghcr.io/openclaw/openclaw:2026.9.3` image resolved to `sha256:6cb72e1599b3b76e2ea3dcc2f4dd7f112247367fbecadfcdee8caa7423f4989b` on the VPS. `openclaw --version` returned `2026.9.3`. An initial 8,192-token Gateway configuration did not return a completed answer within the first test window; Gateway estimated a 7,245-token prompt against a 6,144-token pre-reserve budget.

The repeat lab used the same local Ollama model (`qwen2.5:1.5b`) with a 16,384-token context. The Gateway ran read-only with no FRIDAY mounts, no published port, a temporary token, all tools denied, channels and cron disabled, and only the Ollama plugin active. Its network connected only to the Ollama container. The direct Gateway request returned HTTP 200, `finish_reason=stop`, and `OK.`. A separate ephemeral container loaded the actual FRIDAY `OpenClawProvider` and called the Gateway; it returned `OK.` with 5,526 input tokens and 3 output tokens. The Gateway reported one active plugin (`ollama`), `tools.deny` was `["*"]`, and Docker had no port binding. [The sanitized lab policy](openclaw-lab-config.json) records these settings without the temporary token. This verifies a **text response path only**. It does not verify approval-controlled tool execution, team isolation, browser/computer use, or parity with OpenClaw. Production remains on FRIDAY's existing Ollama provider until the approval bridge and per-user boundary are implemented and tested.

