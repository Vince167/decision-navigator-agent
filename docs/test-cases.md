# Test cases and actual results

Command executed locally:
```bash
pytest --junitxml=reports/junit.xml
```

Actual result: **20 passed, 0 failed in 0.38 seconds**. The tests exercise the in-memory local service and mock connector only; they do not test Microsoft 365, network, tenant policy, identity, deployment, or production performance.

| ID | Executable case | Expected result | Actual |
|---|---|---|---|
| T01 | Valid intake | New record is Draft, version 1 | PASS |
| T02 | German interaction | `de` preserved; German authority boundary available | PASS |
| T03 | Low/reversible/internal classification | Class A | PASS |
| T04 | External side-effect classification | Class B, not automatically blocked | PASS |
| T05 | Regulated/high/irreversible classification | Class C and Blocked | PASS |
| T06 | Agent attempts human mutation | Forbidden | PASS |
| T07 | Draft skips to Ready | `INVALID_TRANSITION` | PASS |
| T08 | Option omits common criterion | Readiness gap | PASS |
| T09 | Evidence has invalid URL | Schema validation error | PASS |
| T10 | Evidence links unknown option | `INVALID_RELATION` | PASS |
| T11 | Conflicting evidence | Readiness blocked | PASS |
| T12 | Criterion weights total 1.2 | Readiness blocked | PASS |
| T13 | Class B owner is also approver | Separation-of-duties gap | PASS |
| T14 | Complete Class A package | Transitions to Ready for Decision | PASS |
| T15 | Decision approval payload omits required keys | `EXACT_PAYLOAD_REQUIRED` | PASS |
| T16 | Approval supplies wrong hash | `PAYLOAD_HASH_MISMATCH` | PASS |
| T17 | Valid human approval | Decision becomes Decided with selected option | PASS |
| T18 | Identical approval replay | Same terminal approval; no second state mutation | PASS |
| T19 | Execute unapproved action | `NOT_APPROVED` | PASS |
| T20 | Action payload mismatch and duplicate execution | Mismatch rejected; same key/action/hash replayed; conflicting reuse rejected | PASS |

Machine-readable result: `reports/junit.xml`.
