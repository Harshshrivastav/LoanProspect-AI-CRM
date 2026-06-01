"""
Planner-Executor API Router — handles plan generation, step execution streams, and human approval checkpoints.
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.database import get_db_context
from app.db.models import Plan, ExecutionStep
from app.services.planner_service import generate_plan
from app.services.executor_service import run_executor_loop_generator
from app.utils.logger import get_logger

router = APIRouter(prefix="/chat/planner", tags=["planner"])
logger = get_logger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────

class PlannerRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ApproveStepRequest(BaseModel):
    plan_id: str
    step_number: int
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/plan", response_model=dict)
def create_agentic_plan(req: PlannerRequest):
    """
    Submits bank manager query, invokes Planner to generate structured sequential steps,
    saves the plan in SQLite, and returns the steps list.
    """
    try:
        plan_data = generate_plan(req.message, req.session_id)
        return plan_data
    except Exception as e:
        logger.error(f"Failed to create agentic plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan/{plan_id}", response_model=dict)
def get_plan_status(plan_id: str):
    """Returns the full plan state and sequential steps timeline."""
    with get_db_context() as db:
        plan = db.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        steps = [{
            "step_id": s.step_id,
            "step_number": s.step_number,
            "description": s.description,
            "rationale": s.rationale,
            "tool_name": s.tool_name,
            "status": s.status,
            "retry_count": s.retry_count,
            "max_retries": s.max_retries,
            "hitl_required": s.hitl_required,
            "hitl_approved": s.hitl_approved,
            "hitl_payload_draft": s.hitl_payload_draft,
            "tool_result": s.tool_result
        } for s in plan.steps]
        
        return {
            "plan_id": plan.plan_id,
            "session_id": plan.session_id,
            "original_query": plan.original_query,
            "status": plan.status,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "steps": steps
        }


@router.get("/stream/{plan_id}")
def stream_plan_execution(plan_id: str):
    """
    Event-Loop Executor Stream. Executes steps sequentially, resolving args,
    verifying outputs, performing retries, pausing for HITL review, and
    re-planning dynamically on errors. Streams progress events over SSE.
    """
    logger.info(f"Starting executor event stream for plan: {plan_id}")
    return StreamingResponse(
        run_executor_loop_generator(plan_id),
        media_type="text/event-stream"
    )


@router.post("/approve")
def approve_hitl_step(req: ApproveStepRequest):
    """
    Called when RM edits/customizes a draft message and approves sending.
    Sets 'hitl_approved = True', saves the customized message draft, and resumes loop.
    """
    logger.info(f"Approving HITL checkpoint for plan {req.plan_id}, step {req.step_number}")
    
    with get_db_context() as db:
        plan = db.get(Plan, req.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        step = db.query(ExecutionStep).filter(
            ExecutionStep.plan_id == req.plan_id,
            ExecutionStep.step_number == req.step_number
        ).first()
        
        if not step:
            raise HTTPException(status_code=404, detail=f"Step {req.step_number} not found")
            
        step.hitl_approved = True
        step.hitl_payload_draft = req.message
        step.status = "pending"  # Reset status so executor will run this step
        plan.status = "running"
        db.commit()
        
    # Resume loop instantly if active SSE stream is listening
    from app.services.executor_service import plan_stream_registry
    if req.plan_id in plan_stream_registry:
        plan_stream_registry[req.plan_id]["feedback_queue"].put(("Approve", req.message))
        
    return {"status": "approved", "message": "Step approved. Executor queue resumed."}
