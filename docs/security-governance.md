# Security and governance controls

## Built in the local MVP
- Fail-closed A/B/C classifier; Class C is blocked.
- Role checks for edit, contribute, own, approve, execute, and audit operations.
- State-based mutability and optimistic version checks.
- Class B owner/approver separation.
- Exact canonical-payload SHA-256 approval binding.
- Separate decision and action approvals.
- Idempotency replay and conflict handling.
- Immutable evidence core with supersession; append-only audit API.
- Mock-only connector allow-list; result declares `side_effect=false`.
- No credentials or secrets in repository.

## Required before any target connection
- Entra app registration; validate issuer, audience, tenant, signature, expiry, and app roles.
- Least-privilege service identity; managed identity/approved connection references; secrets in Key Vault only.
- Approved Power Platform environment, DLP policy, connector allow-list, solution ALM, run-only permissions.
- SharePoint sensitivity/retention labels, legal hold, records rules, site/list permissions, and regional storage confirmation.
- DPIA/privacy review; data minimization; rules for personal/confidential evidence and transcript content.
- Threat model covering prompt injection, confused deputy, stale approvals, replay, over-sharing, malicious links/files, and audit tampering.
- Central monitoring, incident handling, immutable audit export, alerting, backup/restore, RTO/RPO, capacity/rate limits.
- Secure software review, dependency/SBOM and vulnerability scan, SAST/DAST, penetration test, accessibility, localization, and UAT.
- Named business owner, product owner, data owner, system owner, security approver, privacy approver, records manager, and tenant/app-catalog admin.

## Evidence handling
Evidence text is data, never agent instruction. Store least necessary excerpt, precise locator, source identity, verification status, and hash. Preserve source permissions; possession of a URL is not access. Do not store tokens, passwords, special-category personal data, or broad meeting transcripts in the MVP.

## Logging
Do not log raw approval/evidence payloads by default in production. Audit identity, operation, target ID, hash, state change, correlation ID, and outcome. Restrict audit read access; prohibit update/delete; apply approved retention.
