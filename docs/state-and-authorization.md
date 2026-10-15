# State transitions and authorization rules

## Pilot classification (deterministic)
| Class | Rule | MVP treatment |
|---|---|---|
| A | Low impact, reversible, public/internal data, not regulated/safety/legal-HR, no external side effect | Pilot eligible; owner may be approver if assigned |
| B | Medium/high impact, partially reversible, confidential/restricted data, or external side effect; not Class C | Pilot eligible only with named approver separate from owner |
| C | Regulated/GxP, safety-critical, legal/HR decision, special personal data, or high-impact + irreversible | Automatically Blocked; out of pilot |

Classification is a routing control, not a risk opinion or authorization.

## State transition matrix
| From | To | Authorized role | Deterministic preconditions |
|---|---|---|---|
| Draft | In Evaluation | Requester, Editor, DecisionOwner, Admin | Valid current record |
| Draft | Blocked | Requester, Editor, DecisionOwner, Admin | Non-empty reason |
| In Evaluation | Ready for Decision | DecisionOwner, Admin | Readiness has zero gaps |
| In Evaluation | Blocked | Requester, Editor, DecisionOwner, Admin | Non-empty reason |
| Ready for Decision | In Evaluation | DecisionOwner, Admin | Human reopens evaluation or content changes |
| Ready for Decision | Decided | Assigned human approver via `record_approval` | Exact decision payload/hash; current version; Class B separation |
| Ready for Decision | Blocked | Requester, Editor, DecisionOwner, Admin | Non-empty reason |
| Decided | In Execution | DecisionOwner, Admin | At least one action; every active action Approved/Mocked/Cancelled |
| Decided | Closed | DecisionOwner, Admin | No actions exist |
| Decided | Blocked | Requester, Editor, DecisionOwner, Admin | Non-empty reason |
| In Execution | Closed | DecisionOwner, Admin | Every action Mocked or Cancelled |
| In Execution | Blocked | Requester, Editor, DecisionOwner, Admin | Non-empty reason |
| Blocked | Recorded prior state | DecisionOwner, Admin | All blocking reasons cleared; exact prior state only |
| Closed | — | Nobody | Terminal; new work requires a new linked decision |

Direct Draft → Ready, Ready → In Execution, In Evaluation → Decided, and any transition out of Closed are prohibited.

## Role authority
| Role | Permitted | Prohibited |
|---|---|---|
| Agent | Ask, structure, draft, retrieve, call permitted preparation/read actions | Decide, approve, assign itself authority, execute, bypass state checks |
| Requester | Create Draft; clarify; request evaluation; block with reason | Approve Class B unless separately assigned Approver; execute without Executor role |
| Contributor | Add/supersede/verify evidence; draft options/actions | Change state, decide, approve, execute |
| Editor | Edit undecided content; block with reason | Human decision/approval/execution |
| DecisionOwner | Own content; move to evaluation/ready; request approvals; close | Self-approve Class B; bypass evidence/readiness |
| Approver | Approve/reject exact payload when named | Edit payload while approving; approve stale/different hash |
| Executor | Execute an approved action using exact hash/idempotency key | Approve own authority; execute live connector in MVP |
| Auditor | Read records and immutable audit trail | Modify any record |
| Admin | Recovery/governance operations recorded in audit | Silent audit deletion; bypass Class C pilot boundary |

## Permitted record updates
- **Decision:** Draft/In Evaluation content is editable with `expected_version`. Editing Ready content returns it to In Evaluation. Decision content is immutable after Decided except controlled state/closure fields.
- **Evidence:** claim/source/locator/excerpt/hash/capture fields are immutable. Corrections create a superseding record. Only status, verifier, and supersession linkage may change through the controlled action.
- **Action:** editable only while Proposed. Approval freezes operation/payload/hash. Later changes require a new Action or new approval request. Execution writes status/idempotency/result only.
- **Approval:** payload/hash/request metadata are immutable. Only one terminal status plus actor/time/comment is allowed; identical approval replay is safe.
- **Audit:** append-only; no update/delete path exists.
