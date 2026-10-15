"""Clearly fictional end-to-end demo; no enterprise connection or side effect."""

from datetime import date

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
    State,
    TransitionRequest,
)
from decision_navigator.repository import Repository
from decision_navigator.service import DecisionService


service = DecisionService(Repository())

decision = service.create_decision(
    DecisionCreate(
        language="en",
        title="FICTIONAL: Choose the Bluebird demo pilot format",
        decision_question="Which fictional pilot format should the Bluebird team use?",
        requested_by="fictional.requester",
        decision_owner_id="fictional.owner",
        classification_input=ClassificationInput(
            impact="medium",
            reversibility="reversible",
            data_classification="internal",
            external_side_effects=False,
        ),
    ),
    "fictional.requester",
    ["Requester"],
)

service.update_decision(
    decision.id,
    DecisionPatch(
        expected_version=decision.version,
        problem_statement="The fictional Bluebird team needs a safe format for a two-week demo.",
        desired_outcome="Select a reversible format that demonstrates decision readiness.",
        scope_in=["Synthetic data", "Local mock execution"],
        scope_out=["Real users", "Enterprise systems", "Production data"],
        success_criteria=["20 local tests pass", "No enterprise side effect"],
        target_date=date(2026, 11, 6),
        decision_owner_id="fictional.owner",
        approver_ids=["fictional.approver"],
        stakeholder_ids=["fictional.bluebird.team"],
        evaluation_criteria=[
            Criterion(id="learning", name="Learning value", weight=0.6),
            Criterion(id="control", name="Control strength", weight=0.4),
        ],
        risks_assessed=True,
        unresolved_questions=[],
    ),
    "fictional.owner",
    ["DecisionOwner"],
)

local = Option(
    title="Local mock-only prototype",
    description="Use synthetic records and mock execution.",
    criterion_values=[
        CriterionValue(criterion_id="learning", value=5, rationale="Exercises A–F locally"),
        CriterionValue(criterion_id="control", value=5, rationale="No enterprise connector"),
    ],
)
defer = Option(
    title="Defer pilot",
    description="Wait for enterprise access before any demonstration.",
    criterion_values=[
        CriterionValue(criterion_id="learning", value=1, rationale="No near-term feedback"),
        CriterionValue(criterion_id="control", value=5, rationale="No system activity"),
    ],
)
service.upsert_option(decision.id, local, "fictional.contributor", ["Contributor"])
service.upsert_option(decision.id, defer, "fictional.contributor", ["Contributor"])

local_ev = service.add_evidence(
    decision.id,
    EvidenceCreate(
        option_ids=[local.id],
        claim="The fictional local connector has no enterprise side effect.",
        source_title="Fictional Bluebird demo specification",
        source_url="https://example.invalid/bluebird#mock",
        source_locator="Section 2",
        excerpt="The demo records a mock result and does not call an enterprise system.",
        status="verified",
    ),
    "fictional.contributor",
    ["Contributor"],
)
defer_ev = service.add_evidence(
    decision.id,
    EvidenceCreate(
        option_ids=[defer.id],
        claim="Deferring provides no two-week pilot feedback.",
        source_title="Fictional Bluebird demo specification",
        source_url="https://example.invalid/bluebird#defer",
        source_locator="Section 3",
        excerpt="If the demo is deferred, no feedback is collected during the two-week window.",
        status="verified",
    ),
    "fictional.contributor",
    ["Contributor"],
)
local.evidence_ids = [local_ev.id]
defer.evidence_ids = [defer_ev.id]
service.upsert_option(decision.id, local, "fictional.contributor", ["Contributor"])
service.upsert_option(decision.id, defer, "fictional.contributor", ["Contributor"])

decision = service.repo.decision(decision.id)
service.update_decision(
    decision.id,
    DecisionPatch(
        expected_version=decision.version,
        recommendation_option_id=local.id,
        recommendation_rationale="Highest fictional learning while retaining strong controls.",
    ),
    "fictional.owner",
    ["DecisionOwner"],
)
service.transition(decision.id, TransitionRequest(target_state=State.IN_EVALUATION), "fictional.owner", ["DecisionOwner"])
service.transition(decision.id, TransitionRequest(target_state=State.READY), "fictional.owner", ["DecisionOwner"])
decision = service.repo.decision(decision.id)

decision_payload = {
    "decision_id": decision.id,
    "decision_version": decision.version,
    "selected_option_id": local.id,
    "decision_text": "Proceed with the fictional local mock-only prototype.",
    "conditions": ["Synthetic data only", "No enterprise connection"],
}
decision_approval = service.request_approval(
    decision.id,
    ApprovalRequest(
        target_type="decision",
        target_id=decision.id,
        payload=decision_payload,
        required_approver_ids=["fictional.approver"],
    ),
    "fictional.owner",
    ["DecisionOwner"],
)
service.act_on_approval(
    decision_approval.id,
    ApprovalAction(decision="approve", payload_hash=decision_approval.payload_hash, comment="Fictional approval"),
    "fictional.approver",
    ["Approver"],
)

action = service.create_action(
    decision.id,
    ActionCreate(
        title="FICTIONAL: create demo follow-up item",
        owner_id="fictional.executor",
        due_date=date(2026, 11, 7),
        operation="create_demo_task",
        payload={"title": "Fictional Bluebird follow-up", "system": "mock"},
    ),
    "fictional.owner",
    ["DecisionOwner"],
)
action_approval = service.request_approval(
    decision.id,
    ApprovalRequest(
        target_type="action",
        target_id=action.id,
        payload=action.payload,
        required_approver_ids=["fictional.approver"],
    ),
    "fictional.owner",
    ["DecisionOwner"],
)
service.act_on_approval(
    action_approval.id,
    ApprovalAction(decision="approve", payload_hash=action_approval.payload_hash),
    "fictional.approver",
    ["Approver"],
)
service.transition(decision.id, TransitionRequest(target_state=State.IN_EXECUTION), "fictional.owner", ["DecisionOwner"])
result = service.execute_mock(
    action.id,
    ExecuteRequest(idempotency_key="fictional-bluebird-action-001", payload_hash=action.payload_hash),
    "fictional.executor",
    ["Executor"],
)
service.transition(decision.id, TransitionRequest(target_state=State.CLOSED), "fictional.owner", ["DecisionOwner"])

print("FICTIONAL DEMO — no enterprise system was contacted")
print(f"Decision: {decision.id}")
print(f"Final state: {service.repo.decision(decision.id).state.value}")
print(f"Decision approval hash: {decision_approval.payload_hash}")
print(f"Action result: {result}")
print(f"Audit events: {len(service.repo.audits)}")
print("\n--- DECISION BRIEF ---\n")
print(service.decision_brief(decision.id))
