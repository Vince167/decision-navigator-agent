from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .models import (
    ActionCreate,
    ApprovalAction,
    ApprovalRequest,
    DecisionCreate,
    DecisionPatch,
    EvidenceCreate,
    ExecuteRequest,
    Option,
    TransitionRequest,
)
from .repository import NotFoundError, Repository
from .service import DecisionService, DomainError

app = FastAPI(
    title="Decision Navigator MVP API",
    version="0.1.0",
    description="Bounded decision preparation with deterministic state, approval, and mock-execution controls.",
)
service = DecisionService(Repository())


class Actor(BaseModel):
    actor_id: str
    roles: list[str]


class EvidenceStatus(BaseModel):
    status: str


def actor(
    x_actor_id: Annotated[str, Header(alias="X-Actor-Id")],
    x_actor_roles: Annotated[str, Header(alias="X-Actor-Roles")],
) -> Actor:
    return Actor(actor_id=x_actor_id, roles=[x.strip() for x in x_actor_roles.split(",") if x.strip()])


@app.exception_handler(DomainError)
async def domain_error(_, exc: DomainError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=exc.status, content={"error": exc.code, "message": exc.message})


@app.exception_handler(NotFoundError)
async def not_found(_, exc: NotFoundError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=404, content={"error": "NOT_FOUND", "message": str(exc)})


@app.get("/health", operation_id="get_health")
def health():
    return {
        "status": "ok",
        "mode": "local-mock",
        "enterprise_connections": False,
        "features": {"A-F": True, "G-I": False},
    }


@app.post("/decisions", status_code=201, operation_id="create_decision")
def create_decision(body: DecisionCreate, a: Annotated[Actor, Depends(actor)]):
    return service.create_decision(body, a.actor_id, a.roles)


@app.get("/decisions/{decision_id}", operation_id="get_decision")
def get_decision(decision_id: str):
    return service.repo.decision(decision_id)


@app.patch("/decisions/{decision_id}", operation_id="update_decision")
def update_decision(decision_id: str, body: DecisionPatch, a: Annotated[Actor, Depends(actor)]):
    return service.update_decision(decision_id, body, a.actor_id, a.roles)


@app.put("/decisions/{decision_id}/options/{option_id}", operation_id="upsert_option")
def upsert_option(decision_id: str, option_id: str, body: Option, a: Annotated[Actor, Depends(actor)]):
    if body.id != option_id:
        raise HTTPException(status_code=422, detail="path option_id must match body.id")
    return service.upsert_option(decision_id, body, a.actor_id, a.roles)


@app.post("/decisions/{decision_id}/evidence", status_code=201, operation_id="add_evidence")
def add_evidence(decision_id: str, body: EvidenceCreate, a: Annotated[Actor, Depends(actor)]):
    return service.add_evidence(decision_id, body, a.actor_id, a.roles)


@app.post("/evidence/{evidence_id}/status", operation_id="verify_evidence")
def verify_evidence(evidence_id: str, body: EvidenceStatus, a: Annotated[Actor, Depends(actor)]):
    return service.verify_evidence(evidence_id, body.status, a.actor_id, a.roles)


@app.get("/decisions/{decision_id}/readiness", operation_id="assess_readiness")
def assess_readiness(decision_id: str):
    return service.assess_readiness(decision_id)


@app.post("/decisions/{decision_id}/transitions", operation_id="transition_state")
def transition(decision_id: str, body: TransitionRequest, a: Annotated[Actor, Depends(actor)]):
    return service.transition(decision_id, body, a.actor_id, a.roles)


@app.post("/decisions/{decision_id}/actions", status_code=201, operation_id="create_action")
def create_action(decision_id: str, body: ActionCreate, a: Annotated[Actor, Depends(actor)]):
    return service.create_action(decision_id, body, a.actor_id, a.roles)


@app.post("/decisions/{decision_id}/approvals", status_code=201, operation_id="request_approval")
def request_approval(decision_id: str, body: ApprovalRequest, a: Annotated[Actor, Depends(actor)]):
    return service.request_approval(decision_id, body, a.actor_id, a.roles)


@app.post("/approvals/{approval_id}/decision", operation_id="record_approval")
def act_on_approval(approval_id: str, body: ApprovalAction, a: Annotated[Actor, Depends(actor)]):
    return service.act_on_approval(approval_id, body, a.actor_id, a.roles)


@app.post("/actions/{action_id}/execute-mock", operation_id="execute_action_mock")
def execute_mock(action_id: str, body: ExecuteRequest, a: Annotated[Actor, Depends(actor)]):
    return service.execute_mock(action_id, body, a.actor_id, a.roles)


@app.get("/decisions/{decision_id}/brief", response_class=PlainTextResponse, operation_id="generate_decision_brief")
def decision_brief(decision_id: str):
    return service.decision_brief(decision_id)


@app.get("/decisions/{decision_id}/audit", operation_id="get_audit_log")
def audit(decision_id: str, a: Annotated[Actor, Depends(actor)]):
    service._require(a.roles, "audit")
    return [item for item in service.repo.audits if item.decision_id == decision_id]
