# Complete tool/action contract index

The authoritative machine-readable contract is `config/openapi/openapi.json`. All mutation calls require `X-Actor-Id` and comma-separated `X-Actor-Roles`; the local prototype trusts these headers and is **not production authentication**. Microsoft Entra ID token validation is a deployment dependency.

| Operation ID | Method/path | Required input | Success | Principal guards / errors |
|---|---|---|---|---|
| `get_health` | GET `/health` | none | Mode, connection truth, A–I flags | Always read-only |
| `create_decision` | POST `/decisions` | `DecisionCreate`; actor headers | 201 `DecisionRecord` | Edit role; C becomes Blocked; `FORBIDDEN`, validation 422 |
| `get_decision` | GET `/decisions/{decision_id}` | path ID | `DecisionRecord` | `NOT_FOUND` |
| `update_decision` | PATCH same | `DecisionPatch.expected_version` and fields | Updated record/version | Undecided only; optimistic concurrency; `VERSION_CONFLICT`, `IMMUTABLE_STATE` |
| `upsert_option` | PUT `/decisions/{decision_id}/options/{option_id}` | complete `Option`; path/body IDs equal | Updated Decision | Contributor role; undecided only; validation 422 |
| `add_evidence` | POST `/decisions/{id}/evidence` | `EvidenceCreate` | 201 `EvidenceRecord` | Contributor; valid same-decision options; immutable content hash |
| `verify_evidence` | POST `/evidence/{id}/status` | `status=verified|conflicting` | Updated Evidence | Contributor/verifier; superseded records immutable |
| `assess_readiness` | GET `/decisions/{id}/readiness` | path ID | `ReadinessResult` | Deterministic; read-only; warnings do not equal gaps |
| `transition_state` | POST `/decisions/{id}/transitions` | target state; reason for Blocked | Updated Decision | Matrix/role/preconditions; `INVALID_TRANSITION`, `NOT_READY`, `STILL_BLOCKED` |
| `create_action` | POST `/decisions/{id}/actions` | `ActionCreate` | 201 Action with canonical payload hash | Contributor; Ready/Decided/Blocked; connector must be `mock` |
| `request_approval` | POST `/decisions/{id}/approvals` | target type/id, exact payload, approver IDs | 201 pending Approval/hash | Owner; exact keys/current version/current action; Class B separation |
| `record_approval` | POST `/approvals/{id}/decision` | approve/reject, exact 64-char hash, optional comment | Terminal Approval; target update | Assigned human approver; exact/stale checks; replay-safe |
| `execute_action_mock` | POST `/actions/{id}/execute-mock` | idempotency key, exact payload hash | Mock result; `side_effect=false` | Executor; Approved; mock connector; replay-safe/conflict-detecting |
| `generate_decision_brief` | GET `/decisions/{id}/brief` | path ID | Markdown/plain text | Generated only from stored records |
| `get_audit_log` | GET `/decisions/{id}/audit` | actor headers | ordered audit records | Auditor/Admin only; read-only |

## Canonicalization and hashing
`payload_hash = SHA-256(UTF-8(JSON(payload, sort_keys=true, separators=(',', ':'), ensure_ascii=false)))`.

## Error envelope
```json
{"error":"MACHINE_CODE","message":"human-readable explanation"}
```
Expected status classes: 400 malformed domain request, 403 role/approver violation, 404 missing ID, 409 state/version/hash/idempotency conflict, 422 schema/relation failure.

## Duplicate protections
- Approval: a second identical `approve` for an already Approved record returns the same record; a different terminal action/hash fails.
- Execution: same idempotency key + action + hash returns stored result; same key with any different action/hash fails `IDEMPOTENCY_CONFLICT`.
- Optimistic concurrency: Decision update requires current `expected_version`.
