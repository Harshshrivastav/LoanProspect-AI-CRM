"""
Chat API — powers the Agentic Conversation Workspace.
Uses CrewAI's StreamingConversationCrew with NDJSON streaming over StreamingResponse.

Each streamed line is one JSON object (NDJSON format):
  {"type": "status",      "message": "...", "agent": "..."}
  {"type": "agent_start", "agent": "...", "task": "..."}
  {"type": "tool_call",   "tool": "...", "input": "..."}
  {"type": "tool_result", "tool": "...", "output": "..."}
  {"type": "agent_done",  "agent": "...", "result": "..."}
  {"type": "chunk",       "text": "..."}
  {"type": "done",        "steps": [...], "final_answer": "..."}
  {"type": "error",       "error": "..."}
"""

import json
import time
from pydantic import BaseModel

import litellm
from app.agents.crews import StreamingConversationCrew
from app.config import settings
from app.schemas.chat import ChatRequest, CreateSessionRequest, RenameSessionRequest
from app.services.chat_service import (
    archive_session,
    create_session,
    delete_session,
    get_all_sessions,
    get_session_messages,
    pin_session,
    rename_session,
    save_message,
)
from app.utils.logger import get_logger
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


def _generate_suggestions(user_query: str, assistant_response: str) -> list[dict]:
    """Uses Gemini to generate 4 contextual next-step suggestions based on the
    user's query and the agent's final response. Returns a list of dicts with
    emoji, label, description, and query fields."""
    prompt = f"""You are a smart CRM assistant advisor. The user (a bank relationship manager) just asked:
"{user_query}"

And the AI assistant responded with:
\"\"\"
{assistant_response[:2000]}
\"\"\"

Based on what the user asked and the response they received, generate exactly 4 contextual "next step" suggestions that the manager would most likely want to do next.

CRITICAL REQUIREMENT:
The queries you suggest MUST map directly to the system's actual tools and supported capabilities. Do NOT suggest actions we cannot perform (such as calling, emailing, booking meetings, or modifying customer accounts).

Our supported capabilities and query patterns are:
1. Individual Customer Deep-Dive:
   - "Fetch profile of CUSTXYZ" (to check financial details)
   - "Fetch transactions for CUSTXYZ" (to analyze inflows/outflows)
   - "Detect life events for CUSTXYZ" (to check medical, wedding, renovation, or education spends)
   - "Calculate cashflow trend for CUSTXYZ" (to check monthly cash trajectory)
   - "Compute loan readiness score for CUSTXYZ" (to check score 0-100)
   - "Get scoring explanation for CUSTXYZ" (to get friendly score narrative)
   - "Get risk summary for CUSTXYZ" (to check debt burden & risk segment)
2. Compliance Check:
   - "Run compliance check on CUSTXYZ" (to check consent, KYC, and safety)
   - "Show compliance metrics summary" (to get portfolio compliance rates)
3. Personalized Outreach (WhatsApp):
   - "Draft WhatsApp message for CUSTXYZ" (Hyper-personalized text draft)
   - "Draft WhatsApp messages for top prospects" (Batch outreach draft)
4. Portfolio Scanning & Discovery:
   - "Rank all prospects for a personal loan" (Propensity scan)
   - "Search for customers with high-value spending patterns" (e.g. search for medical or education spends > 50,000)
   - "List all portfolio customers" (Brief portfolio scan)
5. Campaign Execution:
   - "Create campaign named [name] for top [count] prospects" (e.g. "Create campaign named Premium Outbound for top 5 prospects")
   - "Show campaign status summary"
6. Auditing:
   - "Show recent security audit logs"

RULES:
- Each suggestion query MUST strictly follow one of these query patterns. DO NOT make up generic, unsupported tasks (such as calling, emailing, booking meetings, or modifying customer accounts).
- If the response includes a specific customer (e.g., CUST005), customize the suggestion queries for that specific customer ID (e.g., "Draft WhatsApp message for CUST005" or "Compute loan readiness score for CUST005").
- Each suggestion needs: emoji (single emoji), label (3-5 words max), description (1 short sentence explaining the action), query (the exact message the user would type).

Return a JSON array of exactly 4 objects. Return ONLY the JSON array, nothing else."""

    try:
        model_name = "gemini/gemini-2.0-flash" if "2.5" in settings.gemini_model else f"gemini/{settings.gemini_model}"
        response = litellm.completion(
            model=model_name,
            api_key=settings.gemini_api_key,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        # Handle both {"suggestions": [...]} and plain [...] formats
        if isinstance(parsed, dict):
            suggestions = parsed.get("suggestions", parsed.get("next_steps", list(parsed.values())[0] if parsed else []))
        elif isinstance(parsed, list):
            suggestions = parsed
        else:
            raise ValueError("Unexpected format")

        if suggestions and isinstance(suggestions, list) and len(suggestions) >= 2:
            # Validate each item has required keys
            valid = []
            for s in suggestions[:4]:
                if isinstance(s, dict) and all(k in s for k in ("emoji", "label", "description", "query")):
                    valid.append(s)
            if len(valid) >= 2:
                return valid
    except Exception as e:
        logger.warning(f"Dynamic suggestion generation failed: {e}")

    return []


@router.get("/sessions", response_model=list[dict])
def list_sessions():
    """Returns all non-archived chat sessions."""
    return get_all_sessions()


@router.post("/sessions", response_model=dict)
def start_session(req: CreateSessionRequest):
    """Creates a new chat session."""
    return create_session(req.title, req.customer_context)


@router.get("/sessions/{session_id}/messages", response_model=list[dict])
def list_messages(session_id: str):
    """Returns all messages for a session in order."""
    return get_session_messages(session_id)


@router.delete("/sessions/{session_id}")
def delete_chat_session(session_id: str):
    """Permanently deletes a chat session and all messages."""
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success"}


@router.patch("/sessions/{session_id}/rename", response_model=dict)
def rename_chat_session(session_id: str, req: RenameSessionRequest):
    """Renames a session."""
    session = rename_session(session_id, req.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/sessions/{session_id}/pin", response_model=dict)
def pin_chat_session(session_id: str, pinned: bool = True):
    """Pins or unpins a session."""
    session = pin_session(session_id, pinned)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/sessions/{session_id}/archive", response_model=dict)
def archive_chat_session(session_id: str):
    """Soft deletes a session."""
    session = archive_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


from app.services.planner_service import is_simple_query, generate_plan
from app.services.executor_service import run_unified_executor_loop_generator
from app.schemas.chat import ApprovePlanRequest
from app.db.database import get_db_context
from app.db.models import Plan, ExecutionStep

@router.post("/stream")
def stream_agent_conversation(req: ChatRequest):
    """
    Primary agentic chat loop endpoint. Evaluates query complexity:
    - Simple queries: Run direct conversational crew immediately.
    - Complex queries: Generate step-by-step plan, yield plan JSON, and pause for approval.
    """
    logger.info(f"stream_agent_conversation: message='{req.message}' | mode='{req.mode}'")
    
    # 1. Build chronological message thread history context
    history_context = ""
    if req.session_id:
        import re
        past_msgs = get_session_messages(req.session_id)
        
        if past_msgs:
            customer_ids = list(dict.fromkeys(re.findall(r'CUST\d{3,}', " ".join(m.get("content", "") for m in past_msgs), re.IGNORECASE)))
            customer_names = re.findall(r'Customer Profile:\s*\*?\*?([A-Z][a-z]+ [A-Z][a-z]+)', " ".join(m.get("content", "") for m in past_msgs))
            
            last_customer_id = customer_ids[-1] if customer_ids else None
            last_customer_name = customer_names[-1] if customer_names else None
            
            thread = []
            for m in past_msgs[-5:]:
                thread.append(f"{m.get('role', '').upper()}: {m.get('content', '')}")
            
            lines = [
                "=== CONVERSATION MEMORY ===",
                f"LAST CUSTOMER DISCUSSED: {last_customer_id.upper()} ({last_customer_name})" if last_customer_id and last_customer_name else f"LAST CUSTOMER DISCUSSED: {last_customer_id.upper()}" if last_customer_id else "",
                f"ALL CUSTOMERS MENTIONED IN SESSION: {', '.join(c.upper() for c in customer_ids)}" if len(customer_ids) > 1 else "",
                "",
                "CHRONOLOGICAL CONVERSATION THREAD (LAST 5 MESSAGES):",
                *thread,
                "=== END MEMORY ==="
            ]
            history_context = "\n".join(filter(None, lines))

    # Save user query
    if req.session_id:
        save_message(req.session_id, "user", req.message)

    # 2. Heuristic smart routing for complexity classification
    is_simple = (req.mode == "direct") or (req.mode == "auto" and is_simple_query(req.message))
    
    if is_simple:
        logger.info("Routing query to Direct execution crew (Simple query classification)")
        crew = StreamingConversationCrew()

        def generate():
            full_response: list[str] = []
            agent_steps = []
            agent_thoughts = []
            agent_plan = []
            try:
                for event_str in crew.run_streaming(
                    user_message=req.message,
                    session_id=req.session_id,
                    customer_context=req.customer_context,
                    history_context=history_context,
                ):
                    if event_str:
                        yield event_str
                        try:
                            data = json.loads(event_str.strip())
                            if data.get("type") == "chunk":
                                full_response.append(data.get("text", ""))
                            elif data.get("type") == "done":
                                full_response.append(data.get("final_answer", ""))
                            elif data.get("type") == "plan":
                                agent_plan = data.get("steps", [])
                            elif data.get("type") == "thought":
                                agent_thoughts.append({
                                    "text": data.get("text", ""),
                                    "ts": int(time.time() * 1000)
                                })
                            elif data.get("type") == "tool_call":
                                agent_steps.append({
                                    "tool": data.get("tool"),
                                    "input": data.get("input"),
                                    "observation": None,
                                    "ts": int(time.time() * 1000)
                                })
                            elif data.get("type") == "tool_result":
                                for step in reversed(agent_steps):
                                    if step.get("tool") == data.get("tool"):
                                        step["observation"] = data.get("output")
                                        break
                        except Exception:
                            pass
            finally:
                final_text = "".join(full_response)
                suggestions = []
                if final_text:
                    try:
                        suggestions = _generate_suggestions(req.message, final_text)
                        if suggestions:
                            yield json.dumps({"type": "suggestions", "suggestions": suggestions}) + "\n"
                    except Exception as e:
                        logger.warning(f"Suggestion generation failed: {e}")

                if req.session_id and full_response:
                    payload = {
                        "plan": agent_plan,
                        "steps": agent_steps,
                        "thoughts": agent_thoughts,
                        "suggestions": suggestions,
                    }
                    save_message(req.session_id, "assistant", final_text, agent_steps=payload)

        return StreamingResponse(generate(), media_type="application/x-ndjson")

    else:
        logger.info("Routing query to Complex Plan-then-Execute orchestration loop")
        
        def generate_planning_stream():
            try:
                yield json.dumps({"type": "status", "message": "Analyzing request — decomposing into sub-tasks...", "phase": "planning"}) + "\n"
                
                # Generate Plan via PlannerService
                plan_data = generate_plan(req.message, req.session_id, history_context)
                
                yield json.dumps({
                    "type": "plan",
                    "plan_id": plan_data["plan_id"],
                    "complexity": "complex",
                    "steps": plan_data["steps"],
                    "requires_approval": True
                }) + "\n"
                
            except Exception as e:
                logger.error(f"Failed to compile agent plan: {e}")
                yield json.dumps({"type": "error", "error": f"Planning formulation failed: {str(e)}"}) + "\n"
                
        return StreamingResponse(generate_planning_stream(), media_type="application/x-ndjson")


@router.get("/stream/{plan_id}")
def stream_plan_execution(plan_id: str):
    """
    Event-Loop Executor Stream. Runs sequential steps with dynamic memory logging,
    compaction summaries, and loop transitions. Streams progress events over SSE.
    """
    logger.info(f"Initiating consolidated executor stream for plan: {plan_id}")
    return StreamingResponse(
        run_unified_executor_loop_generator(plan_id),
        media_type="text/event-stream"
    )


@router.post("/sessions/{session_id}/approve-plan")
def approve_plan(session_id: str, req: ApprovePlanRequest):
    """
    Approves the plan generated by the LLM and schedules sequential execution.
    Optionally accepts edited steps lists from the Relationship Manager.
    """
    logger.info(f"approve_plan: session_id={session_id}, plan_id={req.plan_id}, approved={req.approved}")
    
    with get_db_context() as db:
        plan = db.get(Plan, req.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        if not req.approved:
            plan.status = "failed"
            db.commit()
            return {"status": "rejected", "message": "Plan rejected."}
            
        plan.status = "running"
        
        if req.edited_steps:
            # Sync edited steps into database execution_steps table
            db.query(ExecutionStep).filter(ExecutionStep.plan_id == req.plan_id).delete()
            import uuid
            for step in req.edited_steps:
                step_model = ExecutionStep(
                    step_id=str(uuid.uuid4()),
                    plan_id=req.plan_id,
                    step_number=step["step_number"],
                    description=step["description"],
                    rationale=step.get("rationale", "User customized step"),
                    tool_name=step["tool_name"],
                    tool_args=json.dumps(step.get("tool_args", {})),
                    status="pending",
                    max_retries=step.get("max_retries", 3),
                    hitl_required=step.get("hitl_required", False)
                )
                db.add(step_model)
                
        db.commit()
        
    return {"status": "success", "plan_id": req.plan_id}


class FeedbackRequest(BaseModel):
    option: str
    edited_content: str | None = None


@router.post("/sessions/{session_id}/feedback")
def submit_agent_feedback(session_id: str, req: FeedbackRequest):
    """
    Unified feedback endpoint. Submits human-in-the-loop approvals/edits
    to either active direct conversation streams or active sequential plan loops.
    """
    logger.info(f"submit_agent_feedback: session_id={session_id}, option='{req.option}'")
    
    # 1. Check direct conversational crews
    from app.agents.crews import session_stream_registry
    registry = session_stream_registry.get(session_id)
    if registry:
        fq = registry.get("feedback_queue")
        if fq:
            fq.put((req.option, req.edited_content))
            return {"status": "success", "message": "Feedback submitted to active conversation stream."}
            
    # 2. Check unified sequential plan executor loops
    from app.services.executor_service import plan_stream_registry
    target_plan_id = None
    with get_db_context() as db:
        for pid in list(plan_stream_registry.keys()):
            plan = db.get(Plan, pid)
            if plan and plan.session_id == session_id:
                target_plan_id = pid
                break
                
    if target_plan_id:
        with get_db_context() as db:
            step = db.query(ExecutionStep).filter(
                ExecutionStep.plan_id == target_plan_id,
                ExecutionStep.status == "running",
                ExecutionStep.hitl_required == True
            ).first()
            if step:
                step.hitl_approved = True
                step.hitl_payload_draft = req.edited_content
                step.status = "pending"
                plan_model = db.get(Plan, target_plan_id)
                plan_model.status = "running"
                db.commit()
                
        plan_stream_registry[target_plan_id]["feedback_queue"].put((req.option, req.edited_content))
        return {"status": "success", "message": "Feedback submitted to active plan executor queue."}
        
    raise HTTPException(status_code=404, detail="No active running stream found for this session.")


