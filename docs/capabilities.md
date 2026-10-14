# Capability ledger — current reconciliation

FRIDAY is Adithya's private product, with owner access and separately approved team accounts. No affiliation or performance equivalence to reference products is implied. Existing branding, account control and architecture are preserved.

| Capability | Status / evidence | Remaining acceptance |
|---|---|---|
| Owner sign-in, individual invitations/revocation | Implemented; prior access API tests passed | Production HTTPS, recovery, multi-device validation |
| Persistent chat, streaming adapter, bounded context | Implemented; mocked stream and persistence tests | Real authenticated provider conversation and reopen |
| Separate durable research worker | Implemented; 72 backend tests and an isolated deployed-image supplied-URL/model run completed | Brave Search with live key; production PostgreSQL/Celery recovery and browser-close run |
| Sources, activity, reports | Supplied public HTTPS page retrieved and cited report saved in disposable live-image test | Human accuracy review of the report and live owner workflow |
| Command center and project dashboard | Implemented; updated fixture browser workflow and prior manual inspection | Live provider run and multi-device production validation |
| Capability-aware provider boundary | Adapter capabilities declared; unknown adapter rejected | Future checkpoint adapter and per-model evaluation; no silent fallback |
| Cloud execution while laptop is off | VPS deployed with API, worker and scheduler running | Laptop-off acceptance and failure recovery tests |
| Browser voice input/playback | Implemented where browser supports it | Provider speech, interruption and cross-device verification remain |
| Explicit user-controlled memory | Implemented and deployed | Local save/edit/delete/context tests pass; live owner page verified; live lifecycle not yet exercised |
| Consequential action approvals | Planned | Material-parameter binding, expiry/replay/ownership tests; account invitations are not action approvals |
| Browser/computer tools and isolated coding | Planned | Hardened worker isolation, actual actions and verification |
| Bots, scheduling, integrations and artifacts beyond Markdown research | Planned | Functional bounded runtime and end-to-end tests |
| Training pipeline | Offline curation and experimental scripts implemented | Reviewed data, three-way family-separated splits, GPU smoke test, baseline, regressions, promotion |
| Council, mobile and physical devices | Planned | Actual integrations; no fake pairing or simulated support |

The configured model produced a live research report from a supplied public page. Brave web search is still unconfigured, and the disposable SQLite run does not establish production PostgreSQL/Celery recovery or report accuracy. Reference products are capability references only, not dependencies.

