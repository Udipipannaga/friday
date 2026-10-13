# Capability ledger — current reconciliation

FRIDAY is Adithya's private product, with owner access and separately approved team accounts. No affiliation or performance equivalence to reference products is implied. Existing branding, account control and architecture are preserved.

| Capability | Status / evidence | Remaining acceptance |
|---|---|---|
| Owner sign-in, individual invitations/revocation | Implemented; prior access API tests passed | Production HTTPS, recovery, multi-device validation |
| Persistent chat, streaming adapter, bounded context | Implemented; mocked stream and persistence tests | Real authenticated provider conversation and reopen |
| Separate durable research worker | Implemented; SQLite recovery/retry/cancellation tests | Real search + cited synthesis with frontend closed; PostgreSQL/Celery run |
| Sources, activity, reports | Implemented; retrieval guards and report checks tested with fixtures; earlier public-page fetch recorded | Live project accuracy review; snippets are not inspected full sources |
| Command center and project dashboard | Implemented; updated fixture browser workflow and prior manual inspection | Live provider run and multi-device production validation |
| Capability-aware provider boundary | Adapter capabilities declared; unknown adapter rejected | Future checkpoint adapter and per-model evaluation; no silent fallback |
| Cloud execution while laptop is off | Planned deployment | Server deployed and laptop-off acceptance test |
| Browser voice input/playback | Implemented where browser supports it | Provider speech, interruption and cross-device verification remain |
| Explicit user-controlled memory | Implemented and deployed | Local save/edit/delete/context tests pass; live owner page verified; live lifecycle not yet exercised |
| Consequential action approvals | Planned | Material-parameter binding, expiry/replay/ownership tests; account invitations are not action approvals |
| Browser/computer tools and isolated coding | Planned | Hardened worker isolation, actual actions and verification |
| Bots, scheduling, integrations and artifacts beyond Markdown research | Planned | Functional bounded runtime and end-to-end tests |
| Training pipeline | Offline curation and experimental scripts implemented | Reviewed data, three-way family-separated splits, GPU smoke test, baseline, regressions, promotion |
| Council, mobile and physical devices | Planned | Actual integrations; no fake pairing or simulated support |

First live milestone remains BLOCKED by absent real model/search configuration. SQLite local evidence does not establish PostgreSQL deployment behavior. Reference products are capability references only, not dependencies.

