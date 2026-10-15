from datetime import date

import pytest
from pydantic import ValidationError

from decision_navigator.i18n import text
from decision_navigator.models import (
    ActionCreate,
    ApprovalAction,
    ApprovalRequest,
    ClassificationInput,
    Criterion,
    CriterionValue,
    DecisionCreate,
    DecisionPatch,
    EvidenceCreate,
    ExecuteRequest,
    Option,
    PilotClass,
    State,
    TransitionRequest,
)
from decision_navigator.repository import Repository
from decision_navigator.service import DecisionService, DomainError, sha256


def svc():
    return DecisionService(Repository())


def create(service, classification=None, language="en"):
    return service.create_decision(
        DecisionCreate(
            language=language,
            title="Select pilot approach",
            decision_question="Which bounded pilot approach should be used?",
            requested_by="requester",
            decision_owner_id="owner",
            classification_input=classification
            or ClassificationInput(
                impact="low", reversibility="reversible", data_classification="internal"
            ),
        ),
        "requester",
        ["Requester"],
    )


def prepare_ready(service, classification=None, evidence_status="verified", approvers=None):
    d = create(service, classification)
    service.update_decision(
        d.id,
        DecisionPatch(
            expected_version=d.version,
            problem_statement="The team needs a bounded pilot that can be reversed.",
            desired_outcome="Choose a practical pilot without autonomous authority.",
            scope_in=["Decision preparation"],
            scope_out=["Live enterprise execution"],
            success_criteria=["Human approval remains mandatory", "No live side effect"],
            target_date=date(2026, 11, 6),
            decision_owner_id="owner",
            approver_ids=approvers or [],
            stakeholder_ids=["team"],
            evaluation_criteria=[
                Criterion(id="fit", name="Pilot fit", weight=0.5),
                Criterion(id="risk", name="Control risk", weight=0.5),
            ],
            unresolved_questions=[],
            risks_assessed=True,
        ),
        "owner",
        ["DecisionOwner"],
    )
    o1 = Option(
        title="Bounded local prototype",
        description="Use mock-only integrations.",
        criterion_values=[
            CriterionValue(criterion_id="fit", value=5, rationale="Meets MVP boundary"),
            CriterionValue(criterion_id="risk", value=1, rationale="No live side effect"),
        ],
    )
    o2 = Option(
        title="Defer",
        description="Do not run a pilot yet.",
        criterion_values=[
            CriterionValue(criterion_id="fit", value=2, rationale="Does not test the concept"),
            CriterionValue(criterion_id="risk", value=0, rationale="No operational change"),
        ],
    )
    service.upsert_option(d.id, o1, "contributor", ["Contributor"])
    service.upsert_option(d.id, o2, "contributor", ["Contributor"])
    ev1 = service.add_evidence(
        d.id,
        EvidenceCreate(
            option_ids=[o1.id],
            claim="Mock execution has no enterprise side effect.",
            source_title="Local prototype specification",
            source_url="https://example.invalid/spec#mock",
            source_locator="Section F",
            excerpt="The mock connector records a result and performs no enterprise side effect.",
            status=evidence_status,
        ),
        "contributor",
        ["Contributor"],
    )
    ev2 = service.add_evidence(
        d.id,
        EvidenceCreate(
            option_ids=[o2.id],
            claim="Deferring produces no pilot evidence.",
            source_title="Pilot comparison note",
            source_url="https://example.invalid/spec#defer",
            source_locator="Option 2",
            excerpt="Deferring the pilot produces no operational learning during the pilot window.",
            status="verified",
        ),
        "contributor",
        ["Contributor"],
    )
    o1.evidence_ids = [ev1.id]
    o2.evidence_ids = [ev2.id]
    service.upsert_option(d.id, o1, "contributor", ["Contributor"])
    service.upsert_option(d.id, o2, "contributor", ["Contributor"])
    d = service.repo.decision(d.id)
    service.update_decision(
        d.id,
        DecisionPatch(
            expected_version=d.version,
            recommendation_option_id=o1.id,
            recommendation_rationale="Best balance of learning and control.",
        ),
        "owner",
        ["DecisionOwner"],
    )
    service.transition(d.id, TransitionRequest(target_state=State.IN_EVALUATION), "owner", ["DecisionOwner"])
    return service.repo.decision(d.id), o1, o2, ev1, ev2


def make_ready(service, **kwargs):
    d, o1, o2, ev1, ev2 = prepare_ready(service, **kwargs)
    service.transition(d.id, TransitionRequest(target_state=State.READY), "owner", ["DecisionOwner"])
    return service.repo.decision(d.id), o1, o2, ev1, ev2


def decide(service, **kwargs):
    d, o1, o2, ev1, ev2 = make_ready(service, **kwargs)
    payload = {
        "decision_id": d.id,
        "decision_version": d.version,
        "selected_option_id": o1.id,
        "decision_text": "Proceed with the bounded local prototype.",
        "conditions": ["No live connector"],
    }
    required = d.approver_ids or ["owner"]
    approval = service.request_approval(
        d.id,
        ApprovalRequest(
            target_type="decision", target_id=d.id, payload=payload, required_approver_ids=required
        ),
        "owner",
        ["DecisionOwner"],
    )
    approver = required[0]
    role = "Approver" if approver != "owner" else "DecisionOwner"
    service.act_on_approval(
        approval.id,
        ApprovalAction(decision="approve", payload_hash=approval.payload_hash),
        approver,
        [role],
    )
    return service.repo.decision(d.id), o1, approval


# T01
def test_01_valid_intake_creates_draft():
    d = create(svc())
    assert d.state == State.DRAFT and d.version == 1


# T02
def test_02_bilingual_german_interaction_is_available():
    d = create(svc(), language="de")
    assert d.language == "de"
    assert "nicht" in text("de", "agent_boundary")


# T03
def test_03_class_a_is_deterministic_for_low_reversible_internal():
    assert create(svc()).pilot_classification == PilotClass.A


# T04
def test_04_class_b_is_deterministic_for_external_side_effect():
    d = create(
        svc(),
        ClassificationInput(
            impact="low",
            reversibility="reversible",
            data_classification="internal",
            external_side_effects=True,
        ),
    )
    assert d.pilot_classification == PilotClass.B and d.state == State.DRAFT


# T05
def test_05_class_c_is_blocked_from_pilot():
    d = create(
        svc(),
        ClassificationInput(
            impact="high",
            reversibility="irreversible",
            data_classification="restricted",
            regulated_or_gxp=True,
        ),
    )
    assert d.pilot_classification == PilotClass.C
    assert d.state == State.BLOCKED
    assert d.blocked_reasons


# T06
def test_06_agent_role_cannot_create_or_approve_for_human():
    service = svc()
    with pytest.raises(DomainError, match="role not permitted"):
        service.create_decision(
            DecisionCreate(
                title="X",
                decision_question="Choose?",
                requested_by="agent",
                decision_owner_id="owner",
                classification_input=ClassificationInput(impact="low", reversibility="reversible"),
            ),
            "agent",
            ["Agent"],
        )


# T07
def test_07_invalid_state_skip_is_rejected():
    service = svc()
    d = create(service)
    with pytest.raises(DomainError) as exc:
        service.transition(d.id, TransitionRequest(target_state=State.READY), "owner", ["DecisionOwner"])
    assert exc.value.code == "INVALID_TRANSITION"


# T08
def test_08_all_options_must_use_exactly_common_criteria():
    service = svc()
    d, o1, _, _, _ = prepare_ready(service)
    o1.criterion_values.pop()
    service.upsert_option(d.id, o1, "contributor", ["Contributor"])
    result = service.assess_readiness(d.id)
    assert any("exactly the common criteria" in gap for gap in result.gaps)


# T09
def test_09_evidence_requires_a_valid_url():
    with pytest.raises(ValidationError):
        EvidenceCreate(
            claim="Claim",
            source_title="Source",
            source_url="not-a-url",
            source_locator="p.1",
            excerpt="Quote",
        )


# T10
def test_10_evidence_cannot_reference_unknown_option():
    service = svc()
    d = create(service)
    with pytest.raises(DomainError) as exc:
        service.add_evidence(
            d.id,
            EvidenceCreate(
                option_ids=["opt_missing"],
                claim="Claim",
                source_title="Source",
                source_url="https://example.invalid/x",
                source_locator="p.1",
                excerpt="Quote",
            ),
            "contributor",
            ["Contributor"],
        )
    assert exc.value.code == "INVALID_RELATION"


# T11
def test_11_conflicting_evidence_blocks_readiness():
    service = svc()
    d, *_ = prepare_ready(service, evidence_status="conflicting")
    result = service.assess_readiness(d.id)
    assert not result.ready
    assert any("Conflicting evidence" in gap for gap in result.gaps)


# T12
def test_12_criterion_weights_must_total_one():
    service = svc()
    d, *_ = prepare_ready(service)
    service.update_decision(
        d.id,
        DecisionPatch(
            expected_version=d.version,
            evaluation_criteria=[
                Criterion(id="fit", name="Pilot fit", weight=0.6),
                Criterion(id="risk", name="Control risk", weight=0.6),
            ],
        ),
        "owner",
        ["DecisionOwner"],
    )
    assert any("weights must total 1.0" in gap for gap in service.assess_readiness(d.id).gaps)


# T13
def test_13_class_b_requires_separate_approver():
    service = svc()
    classification = ClassificationInput(
        impact="medium", reversibility="reversible", data_classification="internal"
    )
    d, *_ = prepare_ready(service, classification=classification, approvers=["owner"])
    result = service.assess_readiness(d.id)
    assert not result.ready
    assert any("separation" in gap.lower() for gap in result.gaps)


# T14
def test_14_complete_class_a_can_become_ready():
    service = svc()
    d, *_ = make_ready(service)
    assert d.state == State.READY
    assert service.assess_readiness(d.id).ready


# T15
def test_15_decision_approval_requires_exact_payload_shape():
    service = svc()
    d, o1, *_ = make_ready(service)
    bad = {"decision_id": d.id, "decision_version": d.version, "selected_option_id": o1.id}
    with pytest.raises(DomainError) as exc:
        service.request_approval(
            d.id,
            ApprovalRequest(target_type="decision", target_id=d.id, payload=bad),
            "owner",
            ["DecisionOwner"],
        )
    assert exc.value.code == "EXACT_PAYLOAD_REQUIRED"


# T16
def test_16_approval_rejects_payload_hash_mismatch():
    service = svc()
    d, o1, *_ = make_ready(service)
    payload = {
        "decision_id": d.id,
        "decision_version": d.version,
        "selected_option_id": o1.id,
        "decision_text": "Proceed.",
        "conditions": [],
    }
    approval = service.request_approval(
        d.id,
        ApprovalRequest(target_type="decision", target_id=d.id, payload=payload, required_approver_ids=["owner"]),
        "owner",
        ["DecisionOwner"],
    )
    with pytest.raises(DomainError) as exc:
        service.act_on_approval(
            approval.id,
            ApprovalAction(decision="approve", payload_hash="0" * 64),
            "owner",
            ["DecisionOwner"],
        )
    assert exc.value.code == "PAYLOAD_HASH_MISMATCH"


# T17
def test_17_valid_human_approval_sets_decided_and_selected_option():
    service = svc()
    d, o1, _ = decide(service)
    assert d.state == State.DECIDED
    assert d.selected_option_id == o1.id
    assert d.decided_at is not None


# T18
def test_18_duplicate_identical_approval_is_safe_replay():
    service = svc()
    d, _, approval = decide(service)
    replay = service.act_on_approval(
        approval.id,
        ApprovalAction(decision="approve", payload_hash=approval.payload_hash),
        "owner",
        ["DecisionOwner"],
    )
    assert replay.status == "Approved"
    assert service.repo.decision(d.id).version == d.version


# T19
def test_19_action_cannot_execute_before_approval_or_with_wrong_hash():
    service = svc()
    d, _, _ = decide(service)
    action = service.create_action(
        d.id,
        ActionCreate(
            title="Create mock task",
            owner_id="executor",
            operation="create_task",
            payload={"title": "Mock task"},
        ),
        "owner",
        ["DecisionOwner"],
    )
    with pytest.raises(DomainError) as exc:
        service.execute_mock(
            action.id,
            ExecuteRequest(idempotency_key="unique-key-0001", payload_hash=action.payload_hash),
            "executor",
            ["Executor"],
        )
    assert exc.value.code == "NOT_APPROVED"


# T20
def test_20_exact_action_approval_and_duplicate_execution_protection():
    service = svc()
    d, _, _ = decide(service)
    action = service.create_action(
        d.id,
        ActionCreate(
            title="Create mock task",
            owner_id="executor",
            operation="create_task",
            payload={"title": "Mock task"},
        ),
        "owner",
        ["DecisionOwner"],
    )
    with pytest.raises(DomainError) as mismatch:
        service.request_approval(
            d.id,
            ApprovalRequest(
                target_type="action",
                target_id=action.id,
                payload={"title": "Changed task"},
                required_approver_ids=["owner"],
            ),
            "owner",
            ["DecisionOwner"],
        )
    assert mismatch.value.code == "EXACT_PAYLOAD_REQUIRED"
    approval = service.request_approval(
        d.id,
        ApprovalRequest(
            target_type="action",
            target_id=action.id,
            payload=action.payload,
            required_approver_ids=["owner"],
        ),
        "owner",
        ["DecisionOwner"],
    )
    service.act_on_approval(
        approval.id,
        ApprovalAction(decision="approve", payload_hash=approval.payload_hash),
        "owner",
        ["DecisionOwner"],
    )
    first = service.execute_mock(
        action.id,
        ExecuteRequest(idempotency_key="unique-key-0002", payload_hash=action.payload_hash),
        "executor",
        ["Executor"],
    )
    replay = service.execute_mock(
        action.id,
        ExecuteRequest(idempotency_key="unique-key-0002", payload_hash=action.payload_hash),
        "executor",
        ["Executor"],
    )
    assert first == replay and first["side_effect"] is False
    other = service.create_action(
        d.id,
        ActionCreate(
            title="Other mock task",
            owner_id="executor",
            operation="create_task",
            payload={"title": "Other"},
        ),
        "owner",
        ["DecisionOwner"],
    )
    other.status = "Approved"
    with pytest.raises(DomainError) as conflict:
        service.execute_mock(
            other.id,
            ExecuteRequest(idempotency_key="unique-key-0002", payload_hash=other.payload_hash),
            "executor",
            ["Executor"],
        )
    assert conflict.value.code == "IDEMPOTENCY_CONFLICT"
