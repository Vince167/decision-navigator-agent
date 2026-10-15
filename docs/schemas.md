# Structured record schemas

The executable Pydantic models are in `src/decision_navigator/models.py`; generated JSON Schema files are in `config/schemas/`; Microsoft Lists mappings are in `config/sharepoint/lists.schema.json`.

## DecisionRecord
**Identity/version:** `id:string`, `version:integer>=1`, `created_at:datetime`, `updated_at:datetime`.

**Required at creation:** `language: en|de`, `title:string(1..200)`, `decision_question:string(1..2000)`, `requested_by:string`, `classification_input:ClassificationInput`, computed `pilot_classification:A|B|C`, `state`.

**Required for Ready:** non-empty `problem_statement`, `desired_outcome`, `decision_owner_id`, `success_criteria[]`, `target_date:date`, `stakeholder_ids[]`, `evaluation_criteria[]`, at least two `options[]`, valid `recommendation_option_id`, `risks_assessed=true`, no `unresolved_questions` or `blocked_reasons`; Class B also needs separate `approver_ids[]`.

**Option:** `id`, `title`, `description`, `criterion_values[{criterion_id,value,rationale}]`, `evidence_ids[]`, `risks[]`, `assumptions[]`. Every option must use exactly the Decision's criterion IDs.

**Criterion:** `id`, `name`, `weight:0..1`, `scale:qualitative|0-5|0-100`; all weights total 1.0.

**Decision result:** `selected_option_id`, `decision_text`, `conditions[]`, `decided_at`; written only by exact-payload approval.

## EvidenceRecord
Required: `id`, `decision_id`, `claim`, `source_title`, absolute `source_url`, precise `source_locator`, exact `excerpt`, `captured_by`, `captured_at`, `status`, `content_hash`. Optional: `option_ids[]`, verifier fields, `supersedes_evidence_id`.

Status: `unverified|verified|conflicting|superseded`. Relationships must stay within one Decision. Core fields are immutable; correction is append-and-supersede.

## ActionRecord
Required: `id`, `decision_id`, `title`, `owner_id`, `target_connector=mock`, `operation`, `payload:object`, `payload_hash:sha256`, `status`, `created_by`, timestamps. Optional: `due_date`, `approval_id`, `idempotency_key`, `result`.

Status: `Proposed|PendingApproval|Approved|Mocked|Failed|Cancelled`. Payload is frozen when approval is requested. Only the mock connector is valid.

## ApprovalRecord
Required: `id`, `decision_id`, `target_type:decision|action`, `target_id`, exact `payload`, `payload_hash`, `status`, `requested_by`, `required_approver_ids[]`, `created_at`. Terminal fields: `acted_by`, `acted_at`, `comment`.

Status: `Pending|Approved|Rejected|Expired|Revoked`. Target/payload/hash are immutable. Duplicate identical approval is a replay; a different hash is rejected.

## AuditRecord
Required: `id`, `decision_id`, `record_type`, `record_id`, `event_type`, `actor_id`, `actor_roles[]`, `timestamp`, `correlation_id`, `details`. Optional `before_hash`, `after_hash`.

Record type: `decision|evidence|action|approval|system`. Append-only; there is no update/delete contract.

## Relationships
```text
Decision 1 ── * Evidence
Decision 1 ── * Action
Decision 1 ── * Approval
Decision 1 ── * Audit
Decision 1 ── * Option (embedded, stable ID)
Evidence * ── * Option (IDs; same Decision only)
Approval 1 ── 1 Decision OR Action target
Action 0..1 ── 1 Approval
Evidence 0..1 ── 1 superseded Evidence
```
