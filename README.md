# Decision Navigator – From Discussion to Execution

**MVP implementation package · v0.1.0 · local/mock only**

Status vocabulary used throughout:
- **Built** — implemented in this package.
- **Proposed** — specified but not created in a target tenant.
- **Mocked** — executed locally with an explicit no-side-effect adapter.
- **Blocked** — intentionally prevented by boundary or missing approval/access.
- **Unresolved** — information or approval is missing.

## 1) Concise build plan, assumptions, and unresolved dependencies

### Build plan
1. **Bound the use case:** one bilingual agent prepares one decision; deterministic code owns classification, readiness, state, authorization, approvals, and execution guards.
2. **Define five records:** Decision, Evidence, Action, Approval, Audit; generate JSON Schema and Lists mappings.
3. **Implement A–F:** intake/classification; evidence; option comparison; readiness/brief; human exact-payload approval; mock action handoff.
4. **Prepare but disable G–I:** live meeting monitoring; reminders/stall detection; live enterprise connectors.
5. **Supply M365 artifacts:** Copilot Studio instructions/config, Teams manifest template, Lists schema, Power Automate flow definitions.
6. **Verify locally:** 20 executable cases plus a clearly fictional end-to-end demo; validate JSON/OpenAPI/package.
7. **Do not deploy:** target access, identities, policies, and approvals are unconfirmed.

### Explicit assumptions
- The user-requested A–I labels and “20 specified test cases” were not present in the retrieved project materials. This package therefore uses the following **assumed, unapproved** mapping:
  - **A** intake and A/B/C classification;
  - **B** evidence register and citations;
  - **C** equal-criteria option comparison;
  - **D** deterministic readiness and Decision Brief;
  - **E** human decision plus exact-payload approval;
  - **F** action handoff with mock-only execution;
  - **G** live meeting monitoring;
  - **H** proactive reminders/stall detection;
  - **I** live enterprise connectors.
- Pilot classes are assumed to mean: **A** low-risk/reversible; **B** controlled/higher-impact with separate approver; **C** regulated/safety/legal-HR/special-personal or high+irreversible and therefore out of pilot.
- Local roles are trusted test inputs, not verified corporate authorization.
- `example.invalid` sources in tests/demo are deliberately fictional.

### Assumed MVP success criteria
| Criterion | Result |
|---|---|
| Exactly one conversational agent; authoritative rules deterministic | Met locally |
| A–F implemented; G–I disabled | Met locally |
| Five separate record types and full contracts | Met |
| Human-only decision/approval; exact-payload binding | Met locally |
| Duplicate approval/execution protection | Met locally |
| English/German agent behavior | Instructions and tests present |
| All 20 local acceptance cases pass | 20/20 pass |
| No live enterprise side effect | Mock connector only; verified locally |
| Microsoft 365 deployment/connection | Not a success claim; unresolved |

These criteria are implementation assumptions, not business-approved pilot KPIs.

### Unresolved dependencies
Approved A–I and A/B/C definitions; target SharePoint site/environment; Entra registrations/roles; Copilot Studio and Teams IDs; API hosting/persistence; DLP; data residency; sensitivity/retention/legal hold; privacy/DPIA; records management; security/threat model; connector/app-catalog approvals; service identity; pilot owner/users/success metrics; UAT/release approval.

## 2) MVP architecture and component responsibilities

One agent handles conversation only; deterministic workflows are authoritative.

```text
Teams [Proposed] → Copilot Studio ONE agent [Proposed]
  → OpenAPI boundary [Built]
  → FastAPI Decision Service [Built/Tested]
     ├─ classification/readiness/state/auth/hash/idempotency
     ├─ five-record in-memory repository [Built/Ephemeral]
     └─ mock connector [Built/Tested, no side effect]
  → Microsoft Lists + Power Automate [Proposed/Disabled]
```

The agent cannot decide, approve, or execute. The service enforces Class C blocking, Class B separation, common option criteria, evidence conflict handling, exact-payload approvals, stale-version rejection, and duplicate-execution protection. Full responsibilities and trust boundaries: [`docs/architecture.md`](docs/architecture.md).

## 3) Ready-to-use agent system instructions

Use [`config/copilot-studio/system-instructions.md`](config/copilot-studio/system-instructions.md). They include:
- English/German behavior;
- bounded clarification;
- A–I feature gates;
- evidence/citation and option-comparison rules;
- role/authority boundaries;
- exact-payload approval and idempotency rules;
- security, prompt-injection, and no-overclaim controls.

Copilot Studio mapping: [`config/copilot-studio/agent.yaml`](config/copilot-studio/agent.yaml) (**Proposed, not imported**).

## 4) Conversation flows and targeted clarification logic

Six primary flows are defined: start/classify; evaluate options/evidence; resolve evidence; reach readiness; request/record human decision; prepare/approve/mock-execute action. Blocked is an interrupt flow. The agent asks only for the next gate's missing fields, grouped into no more than five related items, and never asks for data already stored.

Full English/German examples and condition-to-question table: [`docs/conversation-flows.md`](docs/conversation-flows.md).

## 5) Structured schemas: Decision, Evidence, Action, Approval, Audit

- Executable types/validation: [`src/decision_navigator/models.py`](src/decision_navigator/models.py)
- Generated separate JSON Schemas: [`config/schemas/`](config/schemas/)
- Lists column/type/validation/update mapping: [`config/sharepoint/lists.schema.json`](config/sharepoint/lists.schema.json)
- Required fields, relationships, and permitted updates: [`docs/schemas.md`](docs/schemas.md)

Core controls: optimistic Decision version; stable IDs; evidence source/title/URL/locator/excerpt/status/hash; exact Action payload hash; immutable terminal Approval; append-only Audit. Corrections supersede Evidence rather than overwrite it.

## 6) State-transition and authorization rules

Primary path: `Draft → In Evaluation → Ready for Decision → Decided → In Execution → Closed`. `Blocked` records the prior state and may return only there after all reasons are cleared. `Closed` is terminal.

- Ready requires zero deterministic gaps.
- Decided requires exact-payload human approval.
- Class B owner cannot approve their own decision.
- In Execution requires actions that are already Approved/Mocked/Cancelled.
- Closed requires all actions Mocked/Cancelled.
- Agent role has no human authority.

Complete matrix, roles, and record update rules: [`docs/state-and-authorization.md`](docs/state-and-authorization.md).

## 7) Complete contracts for all named tools/actions

Authoritative OpenAPI 3 contract: [`config/openapi/openapi.json`](config/openapi/openapi.json). It defines 15 operations:

`get_health`, `create_decision`, `get_decision`, `update_decision`, `upsert_option`, `add_evidence`, `verify_evidence`, `assess_readiness`, `transition_state`, `create_action`, `request_approval`, `record_approval`, `execute_action_mock`, `generate_decision_brief`, `get_audit_log`.

Inputs, outputs, guards, errors, canonical hash algorithm, and replay behavior: [`docs/tool-contracts.md`](docs/tool-contracts.md).

## 8) Decision Brief template

Ready-to-fill template: [`docs/Decision-Brief-template.md`](docs/Decision-Brief-template.md). Runtime briefs are generated from stored records by `generate_decision_brief` and keep recommendation separate from the human decision.

## 9) Microsoft 365 configuration artifacts and runnable local prototype

### Artifacts
- Teams: [`config/teams/manifest.template.json`](config/teams/manifest.template.json) — **Proposed; IDs/icons unresolved; not packaged or uploaded**.
- Copilot Studio: [`config/copilot-studio/`](config/copilot-studio/) — **Proposed; not created/imported/published**.
- SharePoint/Lists: [`config/sharepoint/lists.schema.json`](config/sharepoint/lists.schema.json) — **Proposed; not provisioned**.
- Power Automate: [`config/power-automate/`](config/power-automate/) — **Proposed; disabled; not imported**.
- Feature gates: [`config/feature-flags.json`](config/feature-flags.json) — A–F on locally; G–I off.
- Configuration procedure: [`docs/m365-configuration.md`](docs/m365-configuration.md).

### Run locally
```bash
cd decision-navigator-mvp
python -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -e '.[test]'
uvicorn decision_navigator.main:app --app-dir src --host 127.0.0.1 --port 8000
```
Then open `http://127.0.0.1:8000/docs`. Local calls use `X-Actor-Id` and `X-Actor-Roles`; these are a **mock identity boundary**, not production authentication. Storage is in memory and resets on restart.

## 10) Twenty test cases and accurate results

Executed locally:
```text
.................... [100%]
20 passed in 0.38s
```

Coverage includes classification, bilingual behavior, authority boundaries, invalid transitions, equal-criteria comparison, evidence validation/conflict, readiness, Class B separation, exact decision/action payload approval, stale/wrong hash rejection, approval replay, preapproval execution rejection, and idempotency replay/conflict.

Details: [`docs/test-cases.md`](docs/test-cases.md). Machine result: [`reports/junit.xml`](reports/junit.xml). These results apply only to the local in-memory/mock prototype; no Microsoft 365 integration was tested.

## 11) Clearly fictional demo

Run:
```bash
PYTHONPATH=src python scripts/demo.py
```

The demo uses a fictional “Bluebird” team, synthetic identities, `example.invalid` evidence, Class B separation, a fictional human approval, and mock action execution. It closes the local record with `side_effect=false`; it does not contact an enterprise system. Captured output: [`reports/fictional-demo-output.txt`](reports/fictional-demo-output.txt).

## 12) Deployment checklist and remaining approvals

Checklist: [`docs/deployment-checklist.md`](docs/deployment-checklist.md). Security/governance controls: [`docs/security-governance.md`](docs/security-governance.md).

**Current truth:** local code and tests are built; Microsoft 365 artifacts are proposed; action execution is mocked; Class C/live connectors are blocked; target access, production identity, persistence, tenant configuration, deployment, authorization, business approval, privacy/security/records approval, and UAT remain unresolved.

## Repository layout
```text
config/        Copilot Studio, Teams, Lists, Power Automate, OpenAPI, schemas
src/           Local FastAPI/Pydantic implementation
tests/         Exactly 20 executable cases
docs/          Architecture, flows, rules, contracts, brief, configuration, governance
scripts/       Clearly fictional demo
reports/       JUnit result and demo output
```
