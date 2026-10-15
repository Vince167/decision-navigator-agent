from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class State(str, Enum):
    DRAFT = "Draft"
    IN_EVALUATION = "In Evaluation"
    READY = "Ready for Decision"
    DECIDED = "Decided"
    IN_EXECUTION = "In Execution"
    CLOSED = "Closed"
    BLOCKED = "Blocked"


class PilotClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class Role(str, Enum):
    REQUESTER = "Requester"
    CONTRIBUTOR = "Contributor"
    EDITOR = "Editor"
    DECISION_OWNER = "DecisionOwner"
    APPROVER = "Approver"
    EXECUTOR = "Executor"
    AUDITOR = "Auditor"
    ADMIN = "Admin"
    AGENT = "Agent"


class ClassificationInput(BaseModel):
    impact: Literal["low", "medium", "high"]
    reversibility: Literal["reversible", "partially_reversible", "irreversible"]
    data_classification: Literal[
        "public", "internal", "confidential", "restricted", "special_personal"
    ] = "internal"
    regulated_or_gxp: bool = False
    safety_critical: bool = False
    legal_or_hr_decision: bool = False
    external_side_effects: bool = False


class Criterion(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    weight: float = Field(ge=0, le=1)
    scale: Literal["qualitative", "0-5", "0-100"] = "0-5"


class CriterionValue(BaseModel):
    criterion_id: str
    value: str | float
    rationale: str = Field(min_length=1, max_length=2000)


class Option(BaseModel):
    id: str = Field(default_factory=lambda: new_id("opt"))
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=4000)
    criterion_values: list[CriterionValue] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class DecisionCreate(BaseModel):
    language: Literal["en", "de"] = "en"
    title: str = Field(min_length=1, max_length=200)
    decision_question: str = Field(min_length=1, max_length=2000)
    requested_by: str = Field(min_length=1)
    decision_owner_id: str | None = None
    classification_input: ClassificationInput


class DecisionRecord(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: new_id("dec"))
    version: int = Field(default=1, ge=1)
    language: Literal["en", "de"] = "en"
    title: str
    decision_question: str
    problem_statement: str | None = None
    desired_outcome: str | None = None
    scope_in: list[str] = Field(default_factory=list)
    scope_out: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    target_date: date | None = None
    requested_by: str
    decision_owner_id: str | None = None
    contributor_ids: list[str] = Field(default_factory=list)
    approver_ids: list[str] = Field(default_factory=list)
    stakeholder_ids: list[str] = Field(default_factory=list)
    classification_input: ClassificationInput
    pilot_classification: PilotClass
    state: State = State.DRAFT
    blocked_from_state: State | None = None
    blocked_reasons: list[str] = Field(default_factory=list)
    evaluation_criteria: list[Criterion] = Field(default_factory=list)
    options: list[Option] = Field(default_factory=list)
    recommendation_option_id: str | None = None
    recommendation_rationale: str | None = None
    unresolved_questions: list[str] = Field(default_factory=list)
    risks_assessed: bool = False
    selected_option_id: str | None = None
    decision_text: str | None = None
    conditions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    decided_at: datetime | None = None
    closed_at: datetime | None = None


class DecisionPatch(BaseModel):
    expected_version: int = Field(ge=1)
    language: Literal["en", "de"] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    decision_question: str | None = Field(default=None, min_length=1, max_length=2000)
    problem_statement: str | None = Field(default=None, max_length=4000)
    desired_outcome: str | None = Field(default=None, max_length=2000)
    scope_in: list[str] | None = None
    scope_out: list[str] | None = None
    success_criteria: list[str] | None = None
    target_date: date | None = None
    decision_owner_id: str | None = None
    contributor_ids: list[str] | None = None
    approver_ids: list[str] | None = None
    stakeholder_ids: list[str] | None = None
    classification_input: ClassificationInput | None = None
    blocked_reasons: list[str] | None = None
    evaluation_criteria: list[Criterion] | None = None
    recommendation_option_id: str | None = None
    recommendation_rationale: str | None = None
    unresolved_questions: list[str] | None = None
    risks_assessed: bool | None = None


class EvidenceRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ev"))
    decision_id: str
    option_ids: list[str] = Field(default_factory=list)
    claim: str = Field(min_length=1, max_length=2000)
    source_title: str = Field(min_length=1, max_length=500)
    source_url: HttpUrl
    source_locator: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(min_length=1, max_length=4000)
    captured_by: str
    captured_at: datetime = Field(default_factory=utcnow)
    status: Literal["unverified", "verified", "conflicting", "superseded"] = "unverified"
    verified_by: str | None = None
    verified_at: datetime | None = None
    supersedes_evidence_id: str | None = None
    content_hash: str


class EvidenceCreate(BaseModel):
    option_ids: list[str] = Field(default_factory=list)
    claim: str = Field(min_length=1, max_length=2000)
    source_title: str = Field(min_length=1, max_length=500)
    source_url: HttpUrl
    source_locator: str = Field(min_length=1, max_length=500)
    excerpt: str = Field(min_length=1, max_length=4000)
    status: Literal["unverified", "verified", "conflicting"] = "unverified"
    supersedes_evidence_id: str | None = None


class ActionRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("act"))
    decision_id: str
    title: str = Field(min_length=1, max_length=300)
    owner_id: str = Field(min_length=1)
    due_date: date | None = None
    target_connector: Literal["mock"] = "mock"
    operation: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    payload_hash: str
    status: Literal[
        "Proposed", "PendingApproval", "Approved", "Mocked", "Failed", "Cancelled"
    ] = "Proposed"
    approval_id: str | None = None
    idempotency_key: str | None = None
    result: dict[str, Any] | None = None
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ActionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    owner_id: str = Field(min_length=1)
    due_date: date | None = None
    target_connector: Literal["mock"] = "mock"
    operation: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]


class ApprovalRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("apr"))
    decision_id: str
    target_type: Literal["decision", "action"]
    target_id: str
    payload: dict[str, Any]
    payload_hash: str
    status: Literal["Pending", "Approved", "Rejected", "Expired", "Revoked"] = "Pending"
    requested_by: str
    required_approver_ids: list[str] = Field(default_factory=list)
    acted_by: str | None = None
    acted_at: datetime | None = None
    comment: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class ApprovalRequest(BaseModel):
    target_type: Literal["decision", "action"]
    target_id: str
    payload: dict[str, Any]
    required_approver_ids: list[str] = Field(default_factory=list)


class ApprovalAction(BaseModel):
    decision: Literal["approve", "reject"]
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    comment: str | None = Field(default=None, max_length=2000)


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: new_id("aud"))
    decision_id: str
    record_type: Literal["decision", "evidence", "action", "approval", "system"]
    record_id: str
    event_type: str
    actor_id: str
    actor_roles: list[str]
    timestamp: datetime = Field(default_factory=utcnow)
    before_hash: str | None = None
    after_hash: str | None = None
    correlation_id: str = Field(default_factory=lambda: new_id("corr"))
    details: dict[str, Any] = Field(default_factory=dict)


class TransitionRequest(BaseModel):
    target_state: State
    reason: str | None = Field(default=None, max_length=2000)


class ReadinessResult(BaseModel):
    decision_id: str
    ready: bool
    gaps: list[str]
    warnings: list[str]
    score: int = Field(ge=0, le=100)


class ExecuteRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
