# Decision Brief: {{title}}

## 1. Control block
- Decision ID: `{{decision_id}}`
- Version: `{{version}}`
- State: **{{state}}**
- Pilot class: **{{A|B|C}}**
- Decision owner: `{{person_id}}`
- Required approver(s): `{{person_ids}}`
- Target decision date: `{{date}}`
- Readiness result: `{{ready|not_ready}}` / `{{score}}%`
- Generated at: `{{timestamp}}`

## 2. Decision question
{{single answerable question}}

## 3. Context, desired outcome, and boundaries
**Problem statement:** {{text}}

**Desired outcome:** {{text}}

**In scope:**
- {{item}}

**Out of scope:**
- {{item}}

**Success criteria:**
- {{measurable criterion}}

## 4. Stakeholders and authority
| Role | Assigned person or group | Authority |
|---|---|---|
| Requester | {{id}} | Raise and clarify |
| Decision Owner | {{id}} | Own package; request decision |
| Contributors | {{ids}} | Supply evidence and judgments |
| Approver(s) | {{ids}} | Approve exact payload |
| Executor(s) | {{ids}} | Execute approved action only |

## 5. Common evaluation criteria
| Criterion ID | Criterion | Weight | Scale |
|---|---|---:|---|
| {{id}} | {{name}} | {{0.00}} | {{scale}} |

Weights must total 1.0.

## 6. Options compared
| Option | Description | Criterion values | Evidence IDs | Risks | Assumptions |
|---|---|---|---|---|---|
| {{option}} | {{text}} | {{same criteria for each option}} | {{ids}} | {{risks}} | {{assumptions}} |

## 7. Evidence register
| Evidence ID | Claim | Source title | URL | Locator | Exact excerpt | Status | Captured by / at |
|---|---|---|---|---|---|---|---|
| {{id}} | {{claim}} | {{title}} | {{url}} | {{page/section/time}} | {{quote}} | {{status}} | {{id}} / {{time}} |

## 8. Recommendation — advisory only
- Recommended option: `{{option_id}}`
- Rationale: {{text}}
- Evidence quality and limits: {{text}}
- Unresolved questions: {{none or list}}

> A recommendation is not the decision.

## 9. Human decision record
- Selected option: `{{PENDING HUMAN DECISION or option_id}}`
- Decision text: {{text}}
- Conditions: {{list}}
- Exact payload hash: `{{sha256}}`
- Approval record: `{{approval_id}}`
- Decision time: `{{timestamp}}`

## 10. Execution handoff
| Action ID | Owner | Due | Operation | Exact payload hash | Approval | Status |
|---|---|---|---|---|---|---|
| {{id}} | {{id}} | {{date}} | {{operation}} | {{sha256}} | {{approval_id}} | {{status}} |

## 11. Audit and limitations
- Audit event range: `{{first_event}}`–`{{last_event}}`
- Built: {{items}}
- Proposed: {{items}}
- Mocked: {{items}}
- Blocked: {{items}}
- Unresolved: {{items}}
