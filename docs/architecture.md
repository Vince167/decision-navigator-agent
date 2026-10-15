# MVP architecture and responsibilities

```text
Teams (proposed shell; not deployed)
        |
Copilot Studio: ONE bilingual Decision Navigator agent (proposed; not imported)
  - conversation, targeted clarification, summary, Decision Brief request
  - no decision/approval/execution authority
        |
OpenAPI action boundary
        |
Deterministic Decision Service (BUILT, local FastAPI/Python)
  - validation, A/B/C classification, readiness
  - state machine and role rules
  - canonical hash, approval binding, idempotency
        |
Repository adapter
  - in-memory local repository (BUILT, ephemeral)
  - Microsoft Lists mapping (PROPOSED, not connected)
        |
Workflow adapters
  - local mock executor (BUILT and TESTED; no side effect)
  - Power Automate approval/mock flow definitions (PROPOSED, disabled)
        |
Five separated records: Decision / Evidence / Action / Approval / Audit
```

## Component responsibilities
| Component | Responsibility | Status |
|---|---|---|
| One agent | English/German interaction, bounded clarification, tool selection, explanation | Instructions built; Copilot Studio instance proposed |
| Decision Service | All authoritative validation and business rules | Built locally |
| Classification engine | Deterministic A/B/C routing; C fail-closed | Built locally |
| Readiness engine | Common criteria, evidence/conflict, owner/approver, risks, unresolved gaps | Built locally |
| State machine | Valid transitions and Blocked interrupt | Built locally |
| Approval guard | Canonical exact-payload SHA-256, stale-version check, SoD | Built locally |
| Execution guard | Approved payload + Executor role + idempotency | Built locally |
| Mock connector | Return auditable `Mocked` result, no side effect | Built/tested |
| Repository | Store five record types | In-memory built; Lists proposed |
| Audit writer | Append event records with before/after hashes | Built locally |
| OpenAPI contract | 15 agent actions/endpoints | Built/generated |
| Teams package | User channel | Template only; not packaged/deployed |
| Power Automate | Human approvals and mock action flow | Precise definitions only; not imported/enabled |
| Live meeting/reminders/connectors | Future G–I | Prepared/disabled |

## Trust boundaries
1. **Natural-language boundary:** the agent may propose; deterministic service decides whether an operation is valid.
2. **Identity boundary:** local headers are a mock. Production must derive identity/roles from validated Entra tokens.
3. **Approval boundary:** approval stores the exact canonical payload and hash; no “approve whatever is current.”
4. **Execution boundary:** action approval is separate from decision approval. Live connector allow-list is empty.
5. **Data boundary:** core evidence is immutable; audit is append-only; Class C is excluded.

## Out of scope for this MVP
Autonomous decisions; implicit approval; live Teams meeting listening/transcription; circular-discussion detection; proactive reminders; live SharePoint/Planner/Outlook/Teams writes; enterprise search/RAG; external web research; GxP/regulated, safety, legal/HR, or special-personal-data decisions; production hosting/HA/DR; analytics dashboards; tenant deployment; organizational approval.
