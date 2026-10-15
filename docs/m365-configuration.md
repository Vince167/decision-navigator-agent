# Microsoft 365 configuration artifacts — proposed, not applied

## 1. Microsoft Lists / SharePoint
Artifact: `config/sharepoint/lists.schema.json`.

1. Confirm target SharePoint site, data region, site owners, retention labels, sensitivity label, legal-hold requirements, and DLP policy.
2. Create five lists: `DN_Decisions`, `DN_Evidence`, `DN_Actions`, `DN_Approvals`, `DN_Audit` with the specified columns, indexes, validation, and versioning.
3. Break permission inheritance. Map Entra groups to the listed roles; the audit service identity gets Add-only, auditors Read-only.
4. Enforce item access through the API/flows; remove direct UI edit rights for approval/audit fields.
5. Apply retention labels and confirm deletion behavior before any pilot data.
6. Run schema validation with synthetic data only.

## 2. Power Automate
Artifacts: `config/power-automate/*.flow.json`.

1. Create solution `DecisionNavigatorMvp` in an approved Power Platform environment.
2. Create environment variables for site URL, list names, API base URL, and retention label IDs; never store secrets in flow definitions.
3. Add least-privilege SharePoint and Approvals connection references using an approved service identity.
4. Implement `DN - Decision exact-payload approval` exactly in the listed order, including re-fetch/re-hash immediately before write.
5. Implement `DN - Approved action mock execution`; keep target connector hard-coded to `mock`.
6. Leave `DN - Stalled decision reminder` off. Capability H needs separate consent/throttling/privacy approval.
7. Configure secure inputs/outputs for payload steps, run-only user restrictions, failure alerts, retry policy `none` for decision writes, and concurrency control `1` per target record.
8. Export an unmanaged solution for source control, then a managed solution only after review.

## 3. Copilot Studio
Artifacts: `config/copilot-studio/agent.yaml` and `system-instructions.md`.

1. Create one agent in the approved environment; enable English (US) and German (Germany).
2. Require Microsoft Entra ID sign-in. Disable public website and web knowledge.
3. Import `config/openapi/openapi.json` as a custom connector/action set after API hosting and Entra registration are approved.
4. Paste the supplied system instructions without adding autonomous decision/approval language.
5. Configure the four topics in `agent.yaml`; deterministic API responses remain authoritative.
6. Keep G, H, I disabled in `feature-flags.json`. Do not add Graph/Teams/SharePoint knowledge connections for A–F.
7. Configure transcript/log settings to avoid raw restricted evidence; confirm analytics and retention.
8. Publish only to a non-production pilot channel after test, privacy, security, and business owner approval.

## 4. Microsoft Teams
Artifact: `config/teams/manifest.template.json`.

1. Replace template variables only after Entra/Copilot Studio IDs exist.
2. Remove `ChannelMessage.Read.Group` for the A–F pilot; it is included solely as a visible placeholder for disabled capability G.
3. Add reviewed icons; validate the manifest.
4. Package and upload only after tenant app-catalog approval.
5. Scope initial availability to approved pilot users/groups.

## 5. Production-grade authentication/control gap
The local API accepts actor/role headers and stores data in memory. Before any Microsoft 365 connection, replace this with Entra token validation, derive immutable user ID and app roles from signed claims, persist records in approved storage, implement service-to-service credentials in Key Vault/connection references, and add centralized monitoring. Until then, the integration remains **proposed and unconnected**.
