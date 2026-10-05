# Private command center

FRIDAY is a private workspace for Adithya and individually approved teammates. The home view is a JARVIS-inspired CSS reactor HUD with real workspace counts and direct chat, research, and settings actions. It is not a public marketing site. Reduced-motion preferences disable decorative rotation.

Public registration is disabled in the local configuration and example configuration. FRIDAY_OWNER_EMAIL designates the existing authenticated owner account (udipi.adithya@gmail.com by default). The email alone grants no login access. Owner sessions persist for 90 days, refreshed when /api/me is accessed; members have seven-day sessions. Anyone using the already signed-in owner browser has owner access: this does not identify the physical person at the computer. Sign out on shared devices.

Visitors can request access by email. Settings contains an owner-only review list with approve, deny, and revoke actions. Approve returns a single-use, email-bound invitation lasting 48 hours; the owner copies and sends this manually. Tokens are stored hashed and appear in a URL fragment, cleared from the browser URL on load. Invite acceptance requires the invited email and a new password. Revocation deletes sessions and blocks subsequent login/API access. Reissuing a link invalidates its predecessor. Requests are self-reported emails, not verified identities. No email delivery service is connected.

The app currently runs on localhost. Team members on other devices cannot use localhost invitation links. Hosting, HTTPS and FRIDAY_ORIGIN must be configured before remote team use. Preserve FRIDAY_REGISTRATION_OPEN=false. Never enable open registration for the private deployment.

Teammates receive isolated conversations and research projects; shared projects, granular team roles, full administrator audit history and device management remain planned. Revoking access stops new authenticated activity; already running research jobs are not cancelled by revocation. Model/search services still require credentials. No live model capability is claimed by this UI.

Validation: backend access tests cover closed signup, owner-only review, duplicate requests, email binding, token expiry/reuse, member isolation, revocation, and owner cookie persistence. Existing backend regression suite and frontend build/lint are run. Browser inspection covers owner dashboard and settings; invitation acceptance is tested through API, not a complete multi-device deployment.
