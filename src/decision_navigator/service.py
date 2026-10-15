from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable

from .models import (
    ActionCreate,
    ActionRecord,
    ApprovalAction,
    ApprovalRecord,
    ApprovalRequest,
    AuditRecord,
    DecisionCreate,
    DecisionPatch,
    DecisionRecord,
    EvidenceCreate,
    EvidenceRecord,
    ExecuteRequest,
    Option,
    PilotClass,
    ReadinessResult,
    Role,
    State,
    TransitionRequest,
    utcnow,
)
from .repository import Repository


class DomainError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


ROLE_SETS = {
    "edit": {Role.REQUESTER, Role.EDITOR, Role.DECISION_OWNER, Role.ADMIN},
    "contribute": {Role.CONTRIBUTOR, Role.EDITOR, Role.DECISION_OWNER, Role.ADMIN},
    "own": {Role.DECISION_OWNER, Role.ADMIN},
    "approve": {Role.APPROVER, Role.DECISION_OWNER, Role.ADMIN},
    "execute": {Role.EXECUTOR, Role.ADMIN},
    "audit": {Role.AUDITOR, Role.ADMIN},
}


def canonical_json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def classify(inp) -> PilotClass:
    if (
        inp.regulated_or_gxp
        or inp.safety_critical
        or inp.legal_or_hr_decision
        or inp.data_classification == "special_personal"
        or (inp.impact == "high" and inp.reversibility == "irreversible")
    ):
        return PilotClass.C
    if (
        inp.impact in {"medium", "high"}
        or inp.reversibility == "partially_reversible"
        or inp.data_classification in {"confidential", "restricted"}
        or inp.external_side_effects
    ):
        return PilotClass.B
    return PilotClass.A


class DecisionService:
    def __init__(self, repository: Repository | None = None):
        self.repo = repository or Repository()

    @staticmethod
    def _roles(roles: Iterable[str | Role]) -> set[Role]:
        parsed: set[Role] = set()
        for role in roles:
            try:
                parsed.add(role if isinstance(role, Role) else Role(role))
            except ValueError as exc:
                raise DomainError("UNKNOWN_ROLE", f"unknown role: {role}", 403) from exc
        return parsed

    def _require(self, roles: Iterable[str | Role], operation: str) -> set[Role]:
        parsed = self._roles(roles)
        if not parsed.intersection(ROLE_SETS[operation]):
            raise DomainError("FORBIDDEN", f"role not permitted for {operation}", 403)
        if parsed == {Role.AGENT}:
            raise DomainError("AGENT_AUTHORITY_BOUNDARY", "agent cannot decide, approve, or execute", 403)
        return parsed

    def _audit(
        self,
        decision_id: str,
        record_type: str,
        record_id: str,
        event_type: str,
        actor: str,
        roles: Iterable[str | Role],
        before: Any = None,
        after: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        parsed = [r.value if isinstance(r, Role) else str(r) for r in roles]
        self.repo.audits.append(
            AuditRecord(
                decision_id=decision_id,
                record_type=record_type,
                record_id=record_id,
                event_type=event_type,
                actor_id=actor,
                actor_roles=parsed,
                before_hash=sha256(before) if before is not None else None,
                after_hash=sha256(after) if after is not None else None,
                details=details or {},
            )
        )

    def create_decision(self, data: DecisionCreate, actor: str, roles: Iterable[str | Role]) -> DecisionRecord:
        self._require(roles, "edit")
        pilot = classify(data.classification_input)
        blocked = pilot == PilotClass.C
        record = DecisionRecord(
            **data.model_dump(),
            pilot_classification=pilot,
            state=State.BLOCKED if blocked else State.DRAFT,
            blocked_from_state=State.DRAFT if blocked else None,
            blocked_reasons=["Class C is outside the MVP pilot boundary"] if blocked else [],
        )
        self.repo.decisions[record.id] = record
        self._audit(record.id, "decision", record.id, "created", actor, roles, after=record)
        return record

    def update_decision(
        self, decision_id: str, patch: DecisionPatch, actor: str, roles: Iterable[str | Role]
    ) -> DecisionRecord:
        self._require(roles, "edit")
        record = self.repo.decision(decision_id)
        if record.state in {State.DECIDED, State.IN_EXECUTION, State.CLOSED}:
            raise DomainError("IMMUTABLE_STATE", f"decision content cannot be changed in {record.state}", 409)
        if patch.expected_version != record.version:
            raise DomainError("VERSION_CONFLICT", "expected_version does not match", 409)
        before = record.model_copy(deep=True)
        updates = patch.model_dump(exclude_unset=True, exclude={"expected_version"})
        for key, value in updates.items():
            setattr(record, key, value)
        if patch.classification_input is not None:
            record.pilot_classification = classify(patch.classification_input)
            if record.pilot_classification == PilotClass.C:
                record.blocked_from_state = State.DRAFT if record.state == State.BLOCKED else record.state
                record.state = State.BLOCKED
                if "Class C is outside the MVP pilot boundary" not in record.blocked_reasons:
                    record.blocked_reasons.append("Class C is outside the MVP pilot boundary")
        if before.state == State.READY and updates:
            record.state = State.IN_EVALUATION
        record.version += 1
        record.updated_at = utcnow()
        self._audit(decision_id, "decision", decision_id, "updated", actor, roles, before, record)
        return record

    def upsert_option(
        self, decision_id: str, option: Option, actor: str, roles: Iterable[str | Role]
    ) -> DecisionRecord:
        self._require(roles, "contribute")
        record = self.repo.decision(decision_id)
        if record.state not in {State.DRAFT, State.IN_EVALUATION, State.READY, State.BLOCKED}:
            raise DomainError("IMMUTABLE_STATE", "options cannot be changed after decision", 409)
        before = record.model_copy(deep=True)
        existing = next((i for i, item in enumerate(record.options) if item.id == option.id), None)
        if existing is None:
            record.options.append(option)
        else:
            record.options[existing] = option
        if record.state == State.READY:
            record.state = State.IN_EVALUATION
        record.version += 1
        record.updated_at = utcnow()
        self._audit(decision_id, "decision", decision_id, "option_upserted", actor, roles, before, record, {"option_id": option.id})
        return record

    def add_evidence(
        self, decision_id: str, data: EvidenceCreate, actor: str, roles: Iterable[str | Role]
    ) -> EvidenceRecord:
        self._require(roles, "contribute")
        decision = self.repo.decision(decision_id)
        if decision.state in {State.DECIDED, State.IN_EXECUTION, State.CLOSED}:
            raise DomainError("IMMUTABLE_STATE", "evidence cannot be added after decision", 409)
        option_ids = {item.id for item in decision.options}
        if any(option_id not in option_ids for option_id in data.option_ids):
            raise DomainError("INVALID_RELATION", "evidence references an unknown option", 422)
        body = data.model_dump(mode="json")
        record = EvidenceRecord(
            decision_id=decision_id,
            captured_by=actor,
            content_hash=sha256(body),
            verified_by=actor if data.status == "verified" else None,
            verified_at=utcnow() if data.status == "verified" else None,
            **data.model_dump(),
        )
        if data.supersedes_evidence_id:
            prior = self.repo.evidence.get(data.supersedes_evidence_id)
            if not prior or prior.decision_id != decision_id:
                raise DomainError("INVALID_RELATION", "superseded evidence not found in decision", 422)
            prior.status = "superseded"
        self.repo.evidence[record.id] = record
        if decision.state == State.READY:
            decision.state = State.IN_EVALUATION
            decision.version += 1
        self._audit(decision_id, "evidence", record.id, "evidence_added", actor, roles, after=record)
        return record

    def verify_evidence(
        self, evidence_id: str, status: str, actor: str, roles: Iterable[str | Role]
    ) -> EvidenceRecord:
        self._require(roles, "contribute")
        if status not in {"verified", "conflicting"}:
            raise DomainError("INVALID_STATUS", "status must be verified or conflicting", 422)
        record = self.repo.evidence.get(evidence_id)
        if not record:
            raise DomainError("NOT_FOUND", "evidence not found", 404)
        if record.status == "superseded":
            raise DomainError("IMMUTABLE_RECORD", "superseded evidence cannot be updated", 409)
        before = record.model_copy(deep=True)
        record.status = status
        record.verified_by = actor
        record.verified_at = utcnow()
        self._audit(record.decision_id, "evidence", record.id, "evidence_status_changed", actor, roles, before, record)
        return record

    def assess_readiness(self, decision_id: str) -> ReadinessResult:
        d = self.repo.decision(decision_id)
        evidence = {item.id: item for item in self.repo.evidence_for(decision_id)}
        gaps: list[str] = []
        warnings: list[str] = []
        checks = 0
        passed = 0

        def require(ok: bool, message: str) -> None:
            nonlocal checks, passed
            checks += 1
            if ok:
                passed += 1
            else:
                gaps.append(message)

        require(bool(d.problem_statement), "Problem statement is missing")
        require(bool(d.desired_outcome), "Desired outcome is missing")
        require(bool(d.decision_owner_id), "Decision owner is missing")
        require(bool(d.success_criteria), "Success criteria are missing")
        require(d.target_date is not None, "Target decision date is missing")
        require(bool(d.stakeholder_ids), "Stakeholders are missing")
        require(bool(d.evaluation_criteria), "Evaluation criteria are missing")
        require(len(d.options) >= 2, "At least two genuine options are required")
        require(bool(d.recommendation_option_id), "Recommendation is missing")
        require(d.risks_assessed, "Risk assessment is incomplete")
        require(not d.unresolved_questions, "Unresolved questions remain")
        require(d.pilot_classification != PilotClass.C, "Class C is outside the pilot boundary")
        require(not d.blocked_reasons, "Blocking reasons remain")

        criterion_ids = {c.id for c in d.evaluation_criteria}
        if d.evaluation_criteria:
            total_weight = sum(c.weight for c in d.evaluation_criteria)
            require(abs(total_weight - 1.0) < 0.0001, "Evaluation criterion weights must total 1.0")
        option_ids = {o.id for o in d.options}
        if d.recommendation_option_id and d.recommendation_option_id not in option_ids:
            gaps.append("Recommendation does not reference a current option")
        for option in d.options:
            actual = {v.criterion_id for v in option.criterion_values}
            if actual != criterion_ids:
                gaps.append(f"Option {option.id} is not compared on exactly the common criteria")
            if not option.evidence_ids:
                gaps.append(f"Option {option.id} has no cited evidence")
            for evidence_id in option.evidence_ids:
                item = evidence.get(evidence_id)
                if item is None:
                    gaps.append(f"Option {option.id} references missing evidence {evidence_id}")
                elif item.status == "conflicting":
                    gaps.append(f"Conflicting evidence {evidence_id} must be resolved")
                elif item.status == "unverified":
                    warnings.append(f"Evidence {evidence_id} is unverified")
        if d.pilot_classification == PilotClass.B:
            require(bool(d.approver_ids), "Class B requires at least one named approver")
            if d.decision_owner_id and d.decision_owner_id in d.approver_ids:
                gaps.append("Class B requires separation between owner and approver")
        score = int(round((passed / checks) * 100)) if checks else 0
        return ReadinessResult(decision_id=decision_id, ready=not gaps, gaps=sorted(set(gaps)), warnings=sorted(set(warnings)), score=score)

    def transition(
        self, decision_id: str, request: TransitionRequest, actor: str, roles: Iterable[str | Role]
    ) -> DecisionRecord:
        d = self.repo.decision(decision_id)
        before = d.model_copy(deep=True)
        target = request.target_state
        if target == State.BLOCKED:
            self._require(roles, "edit")
            if d.state == State.CLOSED:
                raise DomainError("INVALID_TRANSITION", "Closed is terminal", 409)
            if not request.reason:
                raise DomainError("REASON_REQUIRED", "blocking requires a reason", 422)
            d.blocked_from_state = d.state
            d.state = State.BLOCKED
            if request.reason not in d.blocked_reasons:
                d.blocked_reasons.append(request.reason)
        elif d.state == State.BLOCKED:
            self._require(roles, "own")
            if d.blocked_reasons:
                raise DomainError("STILL_BLOCKED", "clear all blocked reasons before unblocking", 409)
            expected = d.blocked_from_state or State.DRAFT
            if target != expected:
                raise DomainError("INVALID_TRANSITION", f"Blocked may return only to {expected.value}", 409)
            d.state = target
            d.blocked_from_state = None
        elif d.state == State.DRAFT and target == State.IN_EVALUATION:
            self._require(roles, "edit")
            d.state = target
        elif d.state == State.IN_EVALUATION and target == State.READY:
            self._require(roles, "own")
            result = self.assess_readiness(decision_id)
            if not result.ready:
                raise DomainError("NOT_READY", "; ".join(result.gaps), 409)
            d.state = target
        elif d.state == State.READY and target == State.IN_EVALUATION:
            self._require(roles, "own")
            d.state = target
        elif d.state == State.DECIDED and target == State.IN_EXECUTION:
            self._require(roles, "own")
            actions = self.repo.actions_for(decision_id)
            if not actions:
                raise DomainError("NO_ACTIONS", "create at least one action before execution", 409)
            if any(a.status not in {"Approved", "Mocked", "Cancelled"} for a in actions):
                raise DomainError("ACTIONS_NOT_APPROVED", "all active actions must be approved", 409)
            d.state = target
        elif d.state == State.DECIDED and target == State.CLOSED:
            self._require(roles, "own")
            if self.repo.actions_for(decision_id):
                raise DomainError("ACTIONS_EXIST", "use In Execution when actions exist", 409)
            d.state = target
            d.closed_at = utcnow()
        elif d.state == State.IN_EXECUTION and target == State.CLOSED:
            self._require(roles, "own")
            actions = self.repo.actions_for(decision_id)
            if any(a.status not in {"Mocked", "Cancelled"} for a in actions):
                raise DomainError("ACTIONS_OPEN", "all actions must be terminal", 409)
            d.state = target
            d.closed_at = utcnow()
        else:
            raise DomainError("INVALID_TRANSITION", f"{d.state.value} -> {target.value} is not permitted", 409)
        d.version += 1
        d.updated_at = utcnow()
        self._audit(decision_id, "decision", decision_id, "state_transition", actor, roles, before, d, {"target": target.value, "reason": request.reason})
        return d

    def create_action(
        self, decision_id: str, data: ActionCreate, actor: str, roles: Iterable[str | Role]
    ) -> ActionRecord:
        self._require(roles, "contribute")
        decision = self.repo.decision(decision_id)
        if decision.state not in {State.READY, State.DECIDED, State.BLOCKED}:
            raise DomainError("INVALID_STATE", "actions may be prepared only from Ready for Decision onward", 409)
        record = ActionRecord(
            decision_id=decision_id,
            created_by=actor,
            payload_hash=sha256(data.payload),
            **data.model_dump(),
        )
        self.repo.actions[record.id] = record
        self._audit(decision_id, "action", record.id, "action_created", actor, roles, after=record)
        return record

    def request_approval(
        self, decision_id: str, request: ApprovalRequest, actor: str, roles: Iterable[str | Role]
    ) -> ApprovalRecord:
        self._require(roles, "own")
        decision = self.repo.decision(decision_id)
        if request.target_type == "decision":
            if decision.state != State.READY:
                raise DomainError("INVALID_STATE", "decision approval requires Ready for Decision", 409)
            if request.target_id != decision_id:
                raise DomainError("TARGET_MISMATCH", "decision target_id must equal decision_id", 422)
            expected_keys = {"decision_id", "decision_version", "selected_option_id", "decision_text", "conditions"}
            if set(request.payload) != expected_keys:
                raise DomainError("EXACT_PAYLOAD_REQUIRED", f"decision payload keys must be exactly {sorted(expected_keys)}", 422)
            if request.payload["decision_id"] != decision_id or request.payload["decision_version"] != decision.version:
                raise DomainError("PAYLOAD_STALE", "decision payload does not match current record", 409)
            option_ids = {o.id for o in decision.options}
            if request.payload["selected_option_id"] not in option_ids:
                raise DomainError("INVALID_OPTION", "selected option is not current", 422)
            approvers = request.required_approver_ids or decision.approver_ids
            if decision.pilot_classification == PilotClass.B:
                if not approvers:
                    raise DomainError("APPROVER_REQUIRED", "Class B requires a named approver", 422)
                if decision.decision_owner_id in approvers:
                    raise DomainError("SEPARATION_OF_DUTIES", "Class B owner cannot approve own decision", 422)
        else:
            action = self.repo.action(request.target_id)
            if action.decision_id != decision_id:
                raise DomainError("TARGET_MISMATCH", "action belongs to another decision", 422)
            if action.status not in {"Proposed", "PendingApproval"}:
                raise DomainError("INVALID_STATE", "action is not approval-eligible", 409)
            if request.payload != action.payload:
                raise DomainError("EXACT_PAYLOAD_REQUIRED", "action approval payload must exactly match current action payload", 409)
            approvers = request.required_approver_ids or decision.approver_ids
            action.status = "PendingApproval"
        approval = ApprovalRecord(
            decision_id=decision_id,
            target_type=request.target_type,
            target_id=request.target_id,
            payload=request.payload,
            payload_hash=sha256(request.payload),
            requested_by=actor,
            required_approver_ids=approvers,
        )
        self.repo.approvals[approval.id] = approval
        if request.target_type == "action":
            self.repo.action(request.target_id).approval_id = approval.id
        self._audit(decision_id, "approval", approval.id, "approval_requested", actor, roles, after=approval)
        return approval

    def act_on_approval(
        self, approval_id: str, action: ApprovalAction, actor: str, roles: Iterable[str | Role]
    ) -> ApprovalRecord:
        parsed = self._require(roles, "approve")
        approval = self.repo.approval(approval_id)
        if approval.status != "Pending":
            if approval.status == "Approved" and action.decision == "approve" and action.payload_hash == approval.payload_hash:
                return approval
            raise DomainError("APPROVAL_TERMINAL", "approval is already terminal", 409)
        if action.payload_hash != approval.payload_hash:
            raise DomainError("PAYLOAD_HASH_MISMATCH", "approval is valid only for the exact payload", 409)
        if approval.required_approver_ids and actor not in approval.required_approver_ids and Role.ADMIN not in parsed:
            raise DomainError("WRONG_APPROVER", "actor is not a required approver", 403)
        decision = self.repo.decision(approval.decision_id)
        if decision.pilot_classification == PilotClass.B and actor == decision.decision_owner_id:
            raise DomainError("SEPARATION_OF_DUTIES", "Class B owner cannot approve own decision", 403)
        before = approval.model_copy(deep=True)
        approval.status = "Approved" if action.decision == "approve" else "Rejected"
        approval.acted_by = actor
        approval.acted_at = utcnow()
        approval.comment = action.comment
        if approval.target_type == "decision":
            if decision.state != State.READY:
                raise DomainError("PAYLOAD_STALE", "decision state changed after approval request", 409)
            if approval.payload["decision_version"] != decision.version:
                raise DomainError("PAYLOAD_STALE", "decision version changed after approval request", 409)
            if approval.status == "Approved":
                decision.selected_option_id = approval.payload["selected_option_id"]
                decision.decision_text = approval.payload["decision_text"]
                decision.conditions = approval.payload["conditions"]
                decision.state = State.DECIDED
                decision.decided_at = utcnow()
                decision.version += 1
                decision.updated_at = utcnow()
            else:
                decision.state = State.IN_EVALUATION
                decision.version += 1
        else:
            target = self.repo.action(approval.target_id)
            if sha256(target.payload) != approval.payload_hash or target.payload_hash != approval.payload_hash:
                raise DomainError("PAYLOAD_STALE", "action payload changed after approval request", 409)
            target.status = "Approved" if approval.status == "Approved" else "Proposed"
            target.updated_at = utcnow()
        self._audit(approval.decision_id, "approval", approval.id, "approval_acted", actor, roles, before, approval)
        return approval

    def execute_mock(
        self, action_id: str, request: ExecuteRequest, actor: str, roles: Iterable[str | Role]
    ) -> dict[str, Any]:
        self._require(roles, "execute")
        action = self.repo.action(action_id)
        if action.target_connector != "mock":
            raise DomainError("CONNECTOR_DISABLED", "only the mock connector is enabled", 409)
        if request.payload_hash != action.payload_hash:
            raise DomainError("PAYLOAD_HASH_MISMATCH", "execution payload does not match approved payload", 409)
        existing = self.repo.executions.get(request.idempotency_key)
        if existing:
            if existing["action_id"] == action_id and existing["payload_hash"] == request.payload_hash:
                return existing["result"]
            raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency key was used for a different execution", 409)
        if action.status != "Approved":
            raise DomainError("NOT_APPROVED", "action must be approved before execution", 409)
        result = {
            "execution": "mocked",
            "action_id": action.id,
            "operation": action.operation,
            "payload_hash": action.payload_hash,
            "side_effect": False,
        }
        action.status = "Mocked"
        action.idempotency_key = request.idempotency_key
        action.result = result
        action.updated_at = utcnow()
        self.repo.executions[request.idempotency_key] = {
            "action_id": action_id,
            "payload_hash": request.payload_hash,
            "result": result,
        }
        self._audit(action.decision_id, "action", action.id, "mock_executed", actor, roles, after=action, details={"idempotency_key": request.idempotency_key})
        return result

    def decision_brief(self, decision_id: str) -> str:
        d = self.repo.decision(decision_id)
        readiness = self.assess_readiness(decision_id)
        evidence = self.repo.evidence_for(decision_id)
        actions = self.repo.actions_for(decision_id)
        lines = [
            f"# Decision Brief: {d.title}",
            "",
            f"- Decision ID: `{d.id}`",
            f"- State: **{d.state.value}**",
            f"- Pilot class: **{d.pilot_classification.value}**",
            f"- Decision owner: `{d.decision_owner_id or 'UNRESOLVED'}`",
            f"- Target date: `{d.target_date or 'UNRESOLVED'}`",
            f"- Readiness: **{'Ready' if readiness.ready else 'Not ready'} ({readiness.score}%)**",
            "",
            "## Decision question",
            d.decision_question,
            "",
            "## Problem and desired outcome",
            d.problem_statement or "UNRESOLVED",
            "",
            d.desired_outcome or "UNRESOLVED",
            "",
            "## Options compared",
        ]
        for option in d.options:
            lines.extend([f"### {option.title} (`{option.id}`)", option.description])
            for value in option.criterion_values:
                lines.append(f"- {value.criterion_id}: {value.value} — {value.rationale}")
            if option.evidence_ids:
                lines.append("- Evidence: " + ", ".join(f"`{x}`" for x in option.evidence_ids))
        lines.extend(
            [
                "",
                "## Recommendation (advisory, not the decision)",
                f"- Option: `{d.recommendation_option_id or 'UNRESOLVED'}`",
                f"- Rationale: {d.recommendation_rationale or 'UNRESOLVED'}",
                "",
                "## Evidence register",
            ]
        )
        for item in evidence:
            lines.append(f"- `{item.id}` [{item.status}] {item.claim} — {item.source_title}, {item.source_locator}, {item.source_url}")
        lines.extend(["", "## Readiness gaps"])
        lines.extend([f"- {gap}" for gap in readiness.gaps] or ["- None"])
        lines.extend(["", "## Decision record"])
        lines.append(f"- Selected option: `{d.selected_option_id or 'PENDING HUMAN DECISION'}`")
        lines.append(f"- Decision text: {d.decision_text or 'PENDING HUMAN DECISION'}")
        lines.extend(["", "## Execution actions"])
        for item in actions:
            lines.append(f"- `{item.id}` {item.title} — {item.status}; owner `{item.owner_id}`; due `{item.due_date or 'unset'}`")
        lines.extend(["", "## Controls", "- The agent does not decide, approve, or execute.", "- Any approval is bound to the exact canonical payload hash.", "- The local connector records a mock execution only; it has no enterprise side effect."])
        return "\n".join(lines) + "\n"
