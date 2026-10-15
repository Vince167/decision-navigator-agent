# Deployment checklist and remaining approvals

No target deployment, tenant connection, app publication, authorization, or organizational approval has been performed.

## A. Scope and ownership
- [ ] Confirm/approve the assumed A–I mapping and the 20 acceptance cases.
- [ ] Confirm A/B/C definitions, Class C routing owner, and financial/impact thresholds if required.
- [ ] Name business owner, Decision Navigator product owner, service owner, data owner, and support owner.
- [ ] Approve pilot users, duration, success metrics, exit criteria, rollback, and support hours.
- [ ] Confirm English/German terminology and accessibility expectations.

## B. Architecture and platform
- [ ] Select approved Power Platform environment and SharePoint site.
- [ ] Decide hosting for deterministic API; add persistence, HA/DR, backup, monitoring, and capacity plan.
- [ ] Register Entra apps/managed identities and define app roles/groups.
- [ ] Replace trusted local headers with validated Entra claims.
- [ ] Create approved custom connector and environment variables.
- [ ] Import Lists, Power Automate, Copilot Studio, and Teams artifacts through solution ALM.
- [ ] Remove the prepared ChannelMessage permission unless G receives separate approval.

## C. Security, privacy, records
- [ ] Security architecture/threat-model review.
- [ ] Privacy/DPIA and employee-representation review where applicable.
- [ ] DLP, connector, data-residency, sensitivity, retention, legal-hold, eDiscovery, and deletion approval.
- [ ] Least-privilege and separation-of-duties review; privileged recovery procedure.
- [ ] Logging/monitoring/SIEM and incident-response approval.
- [ ] SBOM/dependency scan, SAST/DAST, penetration test, secrets scan.

## D. Functional validation
- [x] Local 20-case unit suite passes.
- [x] Fictional local A–F end-to-end demo reaches Closed with mock-only result.
- [ ] API integration tests with real Entra tokens.
- [ ] Lists schema/provisioning tests in a non-production site.
- [ ] Power Automate concurrency, retry, stale approval, failure-path, and idempotency tests.
- [ ] Copilot Studio bilingual conversation evaluation and prompt-injection/red-team tests.
- [ ] Teams client validation (desktop/web/mobile), accessibility, and app manifest validation.
- [ ] UAT by Decision Owners, Approvers, Executors, Auditors, and records/privacy representatives.
- [ ] Performance, resilience, backup/restore, and disaster-recovery tests.

## E. Go-live controls
- [ ] Change record and release approval.
- [ ] Managed solution published; source/version tagged; rollback package verified.
- [ ] Feature flags A–F on; G–I off and policy-protected.
- [ ] Production connectors allow-listed; live execution remains off until separate approval.
- [ ] App catalog/tenant admin approval and scoped assignment.
- [ ] Runbook, support rota, escalation contacts, user guidance, and training published.
- [ ] Pilot telemetry and review cadence approved.

## Remaining approvals
Business scope; A–I mapping; A/B/C policy; security; privacy; records/retention; Power Platform environment/DLP; SharePoint site and permissions; Entra app/API permissions; custom connector; Copilot Studio publication; Teams app catalog; service identity; hosting/operations; UAT; change/release; pilot go/no-go.
