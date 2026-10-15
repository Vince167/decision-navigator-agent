# Conversation flows and targeted clarification logic

## Global response frame
Every agent turn uses: **Current state/class → Complete → Missing/blocked → One targeted question or permitted action → Authority reminder where relevant**. Missing facts are shown as `UNRESOLVED`. The agent never upgrades a recommendation to a decision.

## Flow 1 — Start a decision
1. Detect English/German and state the boundary: preparation only; humans decide, approve, and execute.
2. Check whether the user is discussing one decision. Split additional decisions into separate Drafts.
3. Collect at most five related fields in the first question: decision question, owner, desired outcome, target date, and classification inputs.
4. Create the Draft and report deterministic pilot class A/B/C.
5. If Class C, report `Blocked` and stop pilot processing.
6. Otherwise ask only for the next missing group: scope/success criteria/stakeholders.

**English example:** “To create the Draft, who owns the decision, what exact question must be answered, what outcome is wanted, by when, and is it regulated/safety-critical/irreversible or based on sensitive personal data?”

**German example:** „Für den Entwurf brauche ich: Wer ist Decision Owner, welche konkrete Frage soll beantwortet werden, welches Ergebnis wird angestrebt, bis wann, und ist die Entscheidung reguliert/sicherheitskritisch/irreversibel oder nutzt sie besonders sensible personenbezogene Daten?“

## Flow 2 — Evaluate options and evidence
1. Move Draft → In Evaluation only through `transition_state`.
2. Ask for common criteria and weights before collecting scores; weights must total 1.0.
3. Require at least two genuine options. Suggest “defer/do nothing” only when realistic.
4. For each option, collect the same criteria, rationale, risks, assumptions, and evidence IDs.
5. Store claims only with source title, URL, locator, exact excerpt, status, capture identity/time, and hash.
6. Call `assess_readiness`; do not infer readiness conversationally.

## Flow 3 — Resolve evidence issues
- Missing source/locator/excerpt → ask for those exact fields; do not save an invented citation.
- Inaccessible or second-hand source → save as `unverified` and warn.
- Conflicting claims → retain both as `conflicting`; ask the owner to identify a superseding source or record a justified resolution.
- Corrected evidence → create a new Evidence record with `supersedes_evidence_id`; never overwrite core evidence.

## Flow 4 — Ready for Decision
1. Call `assess_readiness`.
2. If gaps exist, group them into at most five targeted prompts in this order: authority, decision framing, comparison, evidence/conflicts, risks/approver.
3. If no gaps, the Decision Owner may move In Evaluation → Ready for Decision.
4. Generate the Decision Brief from stored records.
5. State that the recommendation is advisory.

## Flow 5 — Human decision and exact-payload approval
1. Require state `Ready for Decision`.
2. Build exactly: `decision_id`, `decision_version`, `selected_option_id`, `decision_text`, `conditions`.
3. Display the entire payload and SHA-256 hash.
4. Create the approval request for named approver(s).
5. A permitted human uses `record_approval` with the exact hash.
6. Any version/payload/hash change invalidates the request. Rejected decisions return to In Evaluation. Approved decisions become Decided.
7. For Class B, owner and approver must differ.

## Flow 6 — Execution handoff
1. Create an Action only from Ready for Decision, Decided, or Blocked.
2. Show owner, due date, operation, exact payload, connector (`mock` only), and hash.
3. Request and record a separate exact-payload action approval.
4. Require an Executor and a unique idempotency key.
5. Call `execute_action_mock`; label result **Mocked**, never “completed in Teams/SharePoint.”
6. Repeated same key/action/hash returns the same result; reuse for another action/hash fails.

## Flow 7 — Blocked
- Any active non-Closed state may enter Blocked with a human-supplied reason.
- The agent lists every reason and the prior state.
- Only an authorized Decision Owner/Admin may unblock, only after all reasons are cleared, and only back to the recorded prior state.
- Class C remains outside the pilot; it is not downgraded to bypass governance.

## Targeted clarification decision table
| Deterministic condition | Ask exactly for | Do not ask yet |
|---|---|---|
| No owner/question/outcome/date | Missing fields among those four | Options or recommendation |
| Classification inputs incomplete | Impact, reversibility, data class, regulated/GxP, safety, legal/HR, external side effect | Pilot approval |
| No scope or success criteria | In-scope, out-of-scope, measurable success criteria | Scores |
| No criteria | Criterion name, weight, scale; confirm total 1.0 | Option scoring |
| Fewer than two options | Distinct option name and description; realistic defer option | Readiness |
| Option missing common criterion | Missing value and human rationale | Recommendation |
| Option lacks evidence | Claim, source title, URL, locator, exact excerpt, status | Approval |
| Conflicting evidence | Resolution owner and superseding evidence or justified status change | Ready transition |
| Class B without separate approver | Named approver with assigned authority | Approval request |
| Readiness gaps empty | Whether owner wants to transition to Ready | Extra brainstorming |
| Ready, no decision payload | Selected option, exact decision text, conditions | Execution |
| Action payload changed | New approval request for new hash | Reuse old approval |
