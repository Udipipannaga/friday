# Security model and known limitations

## Implemented protections

- Maintained `pwdlib` Argon2 hashing; random session tokens stored only as SHA-256 digests, with seven-day expiry and logout revocation.
- Exact configured Origin plus custom header on mutating API requests; HttpOnly, SameSite=Strict cookies. Set Secure cookies and HTTPS before external hosting.
- Ownership enforced server-side on every conversation, message submission, project/job, source view and report. Cross-user requests return 404.
- Persisted login throttling by peer IP and account email, bounded password/input lengths, daily job quota and active-job limits. Forwarded client IP headers are not trusted automatically.
- Keys stay in server environment, outside frontend responses and prompts. Provider error bodies and exception details are not written to activity logs. Production API access logs are disabled by the supplied command.
- HTML is extracted as text. React Markdown does not enable raw HTML; remote images are omitted; links open without opener access. CSP, nosniff, frame denial and no-store headers are sent.
- Public HTTPS only, no credentials in URLs, port 443 only. All DNS answers must be globally routable; a validated IP is pinned for the socket while TLS verifies the original hostname. Redirect targets are revalidated. Private, loopback, link-local, reserved and multicast destinations are rejected. Proxy environment variables are not used by provider/search clients.
- Source reads have socket timeouts, redirect/size/type limits and a wall-clock check. Compressed pages are refused to avoid decompression bombs. The cloud worker also has a hard task time limit.
- Model-generated text cannot execute tools or code. No messaging, purchase, booking, remote-shell or desktop tools exist in this milestone.

## Required before public launch

This is a local development release, not a completed security audit. Open registration has no email verification, MFA, password recovery, administrative abuse controls or mature account lifecycle. Anyone can register an unclaimed address; the configured email is a profile preference, not proof of identity. Close registration after provisioning a private installation and build verified identity flows before accepting public users.

Add reverse-proxy request-size/rate limits, TLS, Secure cookies, database/Redis network isolation, a secret manager, encrypted disks/backups, dependency scanning and an independent application review. Do not expose the supplied development server directly to the internet. Resource lists are bounded but account-level data retention/storage quotas need further work. Login throttle records and expired sessions need operational cleanup. Application data is not encrypted within database rows; rely on encrypted storage until per-field requirements are designed.

Windows local execution has no supervisor-enforced hard kill for a blocked DNS resolver; the cloud worker time limit bounds that case. Add a dedicated egress proxy/firewall as defense in depth for public deployment, and verify DNS timeout behavior on the production host. Local SQLite tests do not establish PostgreSQL concurrency or multi-host failover correctness.

Quota units bound submitted jobs and model output, not exact provider billing. Usage may be unknown after an interrupted call. Rate-limited searches can retry and may be counted by the service. Provider-level spend limits should be configured separately.

## Approval requirements retained for later stages

Before enabling email/messages, public posting, purchases, bookings, subscriptions or important deletion, implement a backend approval record bound to user, tool, canonical material parameters, expiry and single execution. Test altered, expired, cross-user and replayed approvals. Unknown external outcomes require reconciliation, not blind retry. A waiting task must release its worker and resume from saved state. No approval UI is simulated now because none of the current tools requires these actions.

## Isolation and devices

Code must run in disposable sandboxes with bounded CPU, RAM, disk, network and credential scope. Browser workers must have isolated profiles and explicitly scoped sessions. A future Windows companion must be separately authenticated and installed; cloud browser control is not laptop control. Local-only tasks wait if that laptop is offline. Never bypass CAPTCHA or authentication challenges.

Future memory deletion must delete associated retrieval/index data. Future device access must be scoped and revocable, with explicit memory access. Robot movement requires a constrained controller, emergency stop and physical safety validation outside the language model.
