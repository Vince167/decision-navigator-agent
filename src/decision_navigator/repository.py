from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import ActionRecord, ApprovalRecord, AuditRecord, DecisionRecord, EvidenceRecord


class NotFoundError(KeyError):
    pass


@dataclass
class Repository:
    decisions: dict[str, DecisionRecord] = field(default_factory=dict)
    evidence: dict[str, EvidenceRecord] = field(default_factory=dict)
    actions: dict[str, ActionRecord] = field(default_factory=dict)
    approvals: dict[str, ApprovalRecord] = field(default_factory=dict)
    audits: list[AuditRecord] = field(default_factory=list)
    executions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def decision(self, decision_id: str) -> DecisionRecord:
        try:
            return self.decisions[decision_id]
        except KeyError as exc:
            raise NotFoundError(f"decision not found: {decision_id}") from exc

    def action(self, action_id: str) -> ActionRecord:
        try:
            return self.actions[action_id]
        except KeyError as exc:
            raise NotFoundError(f"action not found: {action_id}") from exc

    def approval(self, approval_id: str) -> ApprovalRecord:
        try:
            return self.approvals[approval_id]
        except KeyError as exc:
            raise NotFoundError(f"approval not found: {approval_id}") from exc

    def evidence_for(self, decision_id: str) -> list[EvidenceRecord]:
        return [item for item in self.evidence.values() if item.decision_id == decision_id]

    def actions_for(self, decision_id: str) -> list[ActionRecord]:
        return [item for item in self.actions.values() if item.decision_id == decision_id]

    def approvals_for(self, decision_id: str) -> list[ApprovalRecord]:
        return [item for item in self.approvals.values() if item.decision_id == decision_id]
