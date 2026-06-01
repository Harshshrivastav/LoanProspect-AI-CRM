"""
Executor Service — runs plan steps sequentially using CrewAI's specialized Agents.
Handles parameter resolution, real-time thought-streaming, retries, and dynamic re-planning.
"""

import json
import re
import time
import queue
import threading
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db_context
from app.db.models import Plan, ExecutionStep
from app.utils.logger import get_logger

# Import CrewAI classes
from crewai import Crew, Process, Task

# Import all tools to construct a map
from app.tools.customer_tools import list_customers_brief, fetch_customer_profile, get_customer_risk_summary
from app.tools.transaction_tools import calculate_cashflow_trend, detect_life_event_spends, fetch_transaction_summary
from app.tools.scoring_tools import compute_loan_readiness_score, get_prospect_explanation, rank_personal_loan_prospects
from app.tools.outreach_tools import generate_whatsapp_message, generate_bulk_messages
from app.tools.compliance_tools import validate_compliance, get_compliance_summary
from app.tools.campaign_tools import create_campaign_payload, get_campaign_status_summary, get_top_prospect_ids_for_campaign
from app.tools.audit_tools import get_audit_trail, log_audit_event

logger = get_logger(__name__)

# Global registry to manage plan execution event/feedback queues
# Maps plan_id -> { "event_queue": event_queue, "feedback_queue": feedback_queue }
plan_stream_registry = {}

# Map tool names to their objects
TOOL_MAP = {
    "list_customers_brief": list_customers_brief,
    "fetch_customer_profile": fetch_customer_profile,
    "get_customer_risk_summary": get_customer_risk_summary,
    "calculate_cashflow_trend": calculate_cashflow_trend,
    "detect_life_event_spends": detect_life_event_spends,
    "fetch_transaction_summary": fetch_transaction_summary,
    "compute_loan_readiness_score": compute_loan_readiness_score,
    "get_prospect_explanation": get_prospect_explanation,
    "rank_personal_loan_prospects": rank_personal_loan_prospects,
    "generate_whatsapp_message": generate_whatsapp_message,
    "generate_bulk_messages": generate_bulk_messages,
    "validate_compliance": validate_compliance,
    "get_compliance_summary": get_compliance_summary,
    "create_campaign_payload": create_campaign_payload,
    "get_campaign_status_summary": get_campaign_status_summary,
    "get_top_prospect_ids_for_campaign": get_top_prospect_ids_for_campaign,
    "get_audit_trail": get_audit_trail,
    "log_audit_event": log_audit_event
}

def get_tool_fn(tool_name: str) -> Optional[Any]:
    """Resolves tool name to executable function (unwrapping CrewAI decorator if needed)."""
    tool_obj = TOOL_MAP.get(tool_name)
    if not tool_obj:
        return None
    if hasattr(tool_obj, "func") and tool_obj.func:
        return tool_obj.func
    if hasattr(tool_obj, "_run"):
        return tool_obj._run
    return tool_obj


def get_agent_for_tool(tool_name: str) -> Any:
    """Resolves which specialized CrewAI Agent should run the step's tool."""
    from app.agents.agent_definitions import (
        get_prospect_discovery_agent,
        get_evidence_aggregation_agent,
        get_loan_readiness_agent,
        get_outreach_writer_agent,
        get_compliance_agent,
        get_campaign_coordinator_agent
    )
    name = tool_name.lower()
    if any(k in name for k in ["prospect", "list_customers", "find_high_value"]):
        return get_prospect_discovery_agent()
    elif any(k in name for k in ["transaction", "life_event", "cashflow", "risk_summary"]):
        return get_evidence_aggregation_agent()
    elif any(k in name for k in ["readiness", "score", "explanation"]):
        return get_loan_readiness_agent()
    elif any(k in name for k in ["whatsapp", "outreach", "bulk_message"]):
        return get_outreach_writer_agent()
    elif any(k in name for k in ["compliance"]):
        return get_compliance_agent()
    elif any(k in name for k in ["campaign"]):
        return get_campaign_coordinator_agent()
    else:
        return get_prospect_discovery_agent()


from app.services.memory_store import MemoryStore

def resolve_dynamic_value(val: Any, plan_id: str, db: Session, memory: Optional[MemoryStore] = None) -> Any:
    """
    Resolves a dynamic parameter like '$step1.output.customer_ids'.
    If the value is a string referencing a previous step, looks it up in memory first,
    falling back to SQLite if needed.
    """
    if not isinstance(val, str) or not val.startswith("$step"):
        return val
        
    if memory:
        res = memory.resolve_dynamic_notation(val)
        if res != val:
            return res
            
    # Fallback to database resolution
    match = re.match(r"\$step(\d+)(?:\.output(?:\.(\w+))?)?", val)
    if not match:
        return val
        
    ref_step_num = int(match.group(1))
    key_name = match.group(2)
    
    ref_step = db.query(ExecutionStep).filter(
        ExecutionStep.plan_id == plan_id,
        ExecutionStep.step_number == ref_step_num
    ).first()
    
    if not ref_step or not ref_step.tool_result:
        logger.warning(f"Could not resolve dynamic reference {val}: Step {ref_step_num} not found or has no result.")
        return val
        
    result_text = ref_step.tool_result
    
    try:
        data = json.loads(result_text)
        if isinstance(data, dict):
            if key_name and key_name in data:
                return data[key_name]
            return data
    except (json.JSONDecodeError, TypeError):
        pass
        
    customer_ids = list(set(re.findall(r"CUST\d{3}", result_text)))
    if customer_ids:
        if key_name == "customer_ids_csv":
            return ",".join(customer_ids)
        if key_name == "customer_ids":
            return customer_ids
        return customer_ids[0]
        
    return result_text


def resolve_arguments(tool_args_str: str, plan_id: str, db: Session, memory: Optional[MemoryStore] = None) -> Dict[str, Any]:
    """Resolves all dynamic and static arguments for a tool call, using memory context if available."""
    try:
        args = json.loads(tool_args_str)
    except Exception:
        args = {}
        
    resolved = {}
    for k, v in args.items():
        if isinstance(v, list):
            resolved[k] = [resolve_dynamic_value(item, plan_id, db, memory) for item in v]
        elif isinstance(v, dict):
            resolved[k] = {subkey: resolve_dynamic_value(subval, plan_id, db, memory) for subkey, subval in v.items()}
        else:
            resolved[k] = resolve_dynamic_value(v, plan_id, db, memory)
            
    return resolved


def execute_plan_step_crewai(plan_id: str, step_number: int, event_queue: queue.Queue, memory: Optional[MemoryStore] = None) -> Dict[str, Any]:
    """
    Executes a plan step using the specialized CrewAI Agent.
    Streams intermediate thoughts/tool calls to the event_queue.
    Handles retries and triggers dynamic re-planning on final failures.
    """
    from app.services.planner_service import replan_failed_step

    logger.info(f"Executor: Executing step {step_number} of plan {plan_id} via CrewAI")
    
    with get_db_context() as db:
        plan = db.get(Plan, plan_id)
        if not plan:
            return {"status": "error", "message": "Plan not found"}
            
        step = db.query(ExecutionStep).filter(
            ExecutionStep.plan_id == plan_id,
            ExecutionStep.step_number == step_number
        ).first()
        
        if not step:
            return {"status": "error", "message": f"Step {step_number} not found"}
            
        step.status = "running"
        plan.status = "running"
        db.commit()
        
        # Resolve dynamic arguments
        resolved_args = resolve_arguments(step.tool_args, plan_id, db, memory)
        
        # Fetch matching specialized Agent
        agent = get_agent_for_tool(step.tool_name)
        
        # Define step callback to capture agent's dynamic thoughts and sub-step tool calls
        def step_callback(agent_output):
            try:
                if hasattr(agent_output, "thought") and agent_output.thought:
                    event_queue.put(json.dumps({
                        "type": "thought",
                        "text": str(agent_output.thought),
                        "step_number": step_number
                    }) + "\n")
                if hasattr(agent_output, "tool") and agent_output.tool:
                    event_queue.put(json.dumps({
                        "type": "tool_call",
                        "tool": str(agent_output.tool),
                        "input": str(agent_output.tool_input) if hasattr(agent_output, "tool_input") else "",
                        "step_number": step_number
                    }) + "\n")
                if hasattr(agent_output, "result") and agent_output.result:
                    event_queue.put(json.dumps({
                        "type": "tool_result",
                        "tool": str(agent_output.tool) if hasattr(agent_output, "tool") else "tool",
                        "output": str(agent_output.result)[:1000],
                        "step_number": step_number
                    }) + "\n")
            except Exception as ex:
                logger.debug(f"step_callback error: {ex}")
                
        agent.step_callback = step_callback
        
        args_str = json.dumps(resolved_args)
        
        task = Task(
            description=(
                f"You are executing Step {step_number} of an RM portfolio strategy plan.\n"
                f"Goal: {step.description}\n"
                f"Required Action: Call the tool '{step.tool_name}' with arguments: {args_str}.\n"
                f"Execute the tool exactly and output its full findings. "
                f"If name matching is needed, resolve details dynamically. "
                f"Your output must be the precise findings of the tool call."
            ),
            expected_output=f"Full data/response from execution of step {step_number}.",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        success = False
        result = None
        error_msg = ""
        
        for attempt in range(1, step.max_retries + 1):
            try:
                logger.info(f"Running CrewAI (Attempt {attempt}/{step.max_retries})")
                res_obj = crew.kickoff()
                result = str(res_obj)
                
                if result.startswith("Error") or "failed to execute" in result.lower():
                    raise ValueError(result)
                    
                success = True
                break
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Attempt {attempt} failed: {error_msg}")
                step.retry_count = attempt
                db.commit()
                
                event_queue.put(json.dumps({
                    "type": "status",
                    "message": f"Step {step_number} attempt {attempt} failed: {error_msg[:120]}... Retrying...",
                    "agent": agent.role
                }) + "\n")
                time.sleep(attempt * 0.5)
                
        if success:
            step.status = "success"
            step.tool_result = result
            db.commit()
            return {"status": "success", "result": result}
        else:
            step.status = "failed"
            step.tool_result = f"Error after {step.max_retries} attempts: {error_msg}"
            db.commit()
            
            # Trigger Gemini to replan remaining steps
            new_steps = replan_failed_step(plan_id, step_number, error_msg)
            return {
                "status": "failed_replanned", 
                "error": error_msg,
                "new_steps_count": len(new_steps)
            }


def run_executor_loop_generator(plan_id: str):
    """
    SSE Generator that runs the plan steps sequentially.
    Runs inside a background worker thread to prevent ASGI deadlocks,
    yielding real-time status updates, sub-steps, thoughts, and outputs.
    """
    event_queue = queue.Queue()
    feedback_queue = queue.Queue()
    
    plan_stream_registry[plan_id] = {
        "event_queue": event_queue,
        "feedback_queue": feedback_queue
    }
    
    yield f"data: {json.dumps({'type': 'status', 'message': 'Initiating Glacier Autopilot Sequential Executor...'})}\n\n"
    
    def _run_executor():
        try:
            while True:
                # 1. Look up the next step from DB
                with get_db_context() as db:
                    plan = db.get(Plan, plan_id)
                    if not plan:
                        event_queue.put(json.dumps({'type': 'error', 'error': 'Plan not found'}) + "\n")
                        break
                        
                    steps = db.query(ExecutionStep).filter(
                        ExecutionStep.plan_id == plan_id
                    ).order_by(ExecutionStep.step_number.asc()).all()
                    
                    next_step = None
                    for s in steps:
                        if s.status != "success":
                            next_step = s
                            break
                            
                    if not next_step:
                        plan.status = "completed"
                        db.commit()
                        
                        final_res = steps[-1].tool_result if steps else "Completed"
                        event_queue.put(json.dumps({
                            'type': 'done', 
                            'final_answer': final_res, 
                            'steps': [{'step_number': s.step_number, 'tool_name': s.tool_name, 'status': s.status} for s in steps]
                        }) + "\n")
                        break
                        
                    current_step_number = next_step.step_number
                    step_id = next_step.step_id
                    tool_name = next_step.tool_name
                    description = next_step.description
                    rationale = next_step.rationale
                    hitl_required = next_step.hitl_required
                    hitl_approved = next_step.hitl_approved
                    hitl_payload_draft = next_step.hitl_payload_draft
                    tool_args = next_step.tool_args
                
                # Check for Human-In-The-Loop Checkpoint
                if hitl_required and not hitl_approved:
                    # Update DB plan status to paused
                    with get_db_context() as db:
                        plan = db.get(Plan, plan_id)
                        plan.status = "paused_hitl"
                        db.commit()
                        
                    # Pre-draft message if generate_whatsapp_message to allow RM customization
                    if tool_name == "generate_whatsapp_message" and not hitl_payload_draft:
                        with get_db_context() as db:
                            resolved_args = resolve_arguments(tool_args, plan_id, db)
                            cid = resolved_args.get("customer_id")
                            if cid:
                                try:
                                    from app.tools.outreach_tools import generate_whatsapp_message as gen_msg
                                    draft_output = gen_msg.func(customer_id=cid)
                                    msg_match = re.search(r"--- \n\n(.*)\n\n---", draft_output, re.DOTALL)
                                    draft_text = msg_match.group(1).strip() if msg_match else draft_output
                                    
                                    # Save to step draft
                                    step_model = db.get(ExecutionStep, step_id)
                                    step_model.hitl_payload_draft = draft_text
                                    hitl_payload_draft = draft_text
                                    db.commit()
                                except Exception as ex:
                                    draft_text = f"Hi Customer, please review our pre-approved loan offers! Error drafting: {ex}"
                                    step_model = db.get(ExecutionStep, step_id)
                                    step_model.hitl_payload_draft = draft_text
                                    hitl_payload_draft = draft_text
                                    db.commit()
                                    
                    event_queue.put(json.dumps({
                        'type': 'paused_hitl',
                        'step_number': current_step_number,
                        'tool_name': tool_name,
                        'draft': hitl_payload_draft
                    }) + "\n")
                    
                    # BLOCK wait on feedback queue
                    try:
                        # Wait up to 30 mins
                        option, edited_content = feedback_queue.get(timeout=1800)
                        
                        # Save approval and reset status to run
                        with get_db_context() as db:
                            step_model = db.get(ExecutionStep, step_id)
                            step_model.hitl_approved = True
                            step_model.hitl_payload_draft = edited_content
                            step_model.status = "pending"
                            plan_model = db.get(Plan, plan_id)
                            plan_model.status = "running"
                            db.commit()
                            
                        event_queue.put(json.dumps({
                            'type': 'status',
                            'message': f"Step {current_step_number} approved by Relationship Manager. Resuming execution..."
                        }) + "\n")
                        continue
                    except queue.Empty:
                        event_queue.put(json.dumps({'type': 'error', 'error': 'HITL feedback timeout.'}) + "\n")
                        break
                        
                # Yield step start notification
                event_queue.put(json.dumps({
                    'type': 'step_start',
                    'step_number': current_step_number,
                    'tool_name': tool_name,
                    'description': description,
                    'rationale': rationale
                }) + "\n")
                
                # Run the step via CrewAI specialized agent
                exec_res = execute_plan_step_crewai(plan_id, current_step_number, event_queue)
                
                if exec_res["status"] == "success":
                    event_queue.put(json.dumps({
                        'type': 'step_success',
                        'step_number': current_step_number,
                        'result': str(exec_res['result'])
                    }) + "\n")
                elif exec_res["status"] == "failed_replanned":
                    event_queue.put(json.dumps({
                        'type': 'replanned',
                        'step_number': current_step_number,
                        'error': exec_res['error'],
                        'message': 'Step failed! Re-planner agent triggered. Dynamic plan branch updated.'
                    }) + "\n")
                else:
                    event_queue.put(json.dumps({
                        'type': 'error',
                        'error': exec_res.get('message', 'Execution error')
                    }) + "\n")
                    break
        except Exception as ex:
            logger.error(f"Executor thread crash: {ex}")
            event_queue.put(json.dumps({'type': 'error', 'error': str(ex)}) + "\n")
        finally:
            event_queue.put(None)
            
    thread = threading.Thread(target=_run_executor, daemon=True)
    thread.start()
    
    # Read from event queue and stream out SSE events
    try:
        while True:
            # Yield event to FastAPI SSE stream
            event = event_queue.get(timeout=2000)
            if event is None:
                break
            yield f"data: {event.strip()}\n\n"
    finally:
        if plan_id in plan_stream_registry:
            try:
                del plan_stream_registry[plan_id]
            except KeyError:
                pass


def run_unified_executor_loop_generator(plan_id: str):
    """
    SSE Generator that runs the plan steps sequentially with MemoryStore, LoopController, and Compaction.
    Yields real-time events in NDJSON/SSE format.
    """
    import queue
    import threading
    from app.services.memory_store import MemoryStore
    from app.services.loop_controller import LoopController
    from app.services.summariser import MemorySummariser
    from app.services.planner_service import synthesize_answer, replan_failed_step
    from app.api.chat import _generate_suggestions
    from app.services.chat_service import save_message
    
    event_queue = queue.Queue()
    feedback_queue = queue.Queue()
    
    plan_stream_registry[plan_id] = {
        "event_queue": event_queue,
        "feedback_queue": feedback_queue
    }
    
    yield f"data: {json.dumps({'type': 'status', 'message': 'Initiating Unified Agentic Executor Loop...', 'phase': 'execution'})}\n\n"
    
    def _run_unified_executor():
        try:
            # 1. Load plan from SQLite
            with get_db_context() as db:
                plan = db.get(Plan, plan_id)
                if not plan:
                    event_queue.put(json.dumps({'type': 'error', 'error': 'Plan not found'}) + "\n")
                    return
                session_id = plan.session_id
                original_query = plan.original_query
                
            # Initialize MemoryStore, LoopController, Summariser
            memory = MemoryStore(plan_id, session_id)
            memory.store("user_context", {"query": original_query})
            
            loop_ctrl = LoopController()
            summariser = MemorySummariser()
            
            while True:
                # 2. Fetch the next step in SQLite
                with get_db_context() as db:
                    steps = db.query(ExecutionStep).filter(
                        ExecutionStep.plan_id == plan_id
                    ).order_by(ExecutionStep.step_number.asc()).all()
                    
                    steps_data = [
                        {
                            "step_id": s.step_id,
                            "step_number": s.step_number,
                            "tool_name": s.tool_name,
                            "description": s.description,
                            "rationale": s.rationale,
                            "status": s.status,
                            "hitl_required": s.hitl_required,
                            "hitl_approved": s.hitl_approved,
                            "hitl_payload_draft": s.hitl_payload_draft,
                            "tool_args": s.tool_args,
                            "tool_result": s.tool_result
                        }
                        for s in steps
                    ]
                    
                    next_step = None
                    for s in steps_data:
                        if s["status"] != "success":
                            next_step = s
                            break
                            
                    if not next_step:
                        # Completed!
                        plan_model = db.get(Plan, plan_id)
                        plan_model.status = "completed"
                        db.commit()
                        break
                        
                    current_step_number = next_step["step_number"]
                    step_id = next_step["step_id"]
                    tool_name = next_step["tool_name"]
                    description = next_step["description"]
                    rationale = next_step["rationale"]
                    hitl_required = next_step["hitl_required"]
                    hitl_approved = next_step["hitl_approved"]
                    hitl_payload_draft = next_step["hitl_payload_draft"]
                    tool_args = next_step["tool_args"]
                    
                # Store plan in memory
                memory.store("plan", {"steps": [
                    {
                        "step_number": s["step_number"],
                        "tool_name": s["tool_name"],
                        "status": s["status"],
                        "description": s.get("description", ""),
                        "rationale": s.get("rationale", "")
                    }
                    for s in steps_data
                ]})

                # 3. Check for Human-In-The-Loop outreach approval
                if hitl_required and not hitl_approved:
                    with get_db_context() as db:
                        plan_model = db.get(Plan, plan_id)
                        plan_model.status = "paused_hitl"
                        db.commit()
                        
                    if tool_name == "generate_whatsapp_message" and not hitl_payload_draft:
                        with get_db_context() as db:
                            resolved_args = resolve_arguments(tool_args, plan_id, db, memory)
                            cid = resolved_args.get("customer_id")
                            if cid:
                                try:
                                    from app.tools.outreach_tools import generate_whatsapp_message as gen_msg
                                    draft_output = gen_msg.func(customer_id=cid)
                                    msg_match = re.search(r"--- \n\n(.*)\n\n---", draft_output, re.DOTALL)
                                    draft_text = msg_match.group(1).strip() if msg_match else draft_output
                                    
                                    step_model = db.get(ExecutionStep, step_id)
                                    step_model.hitl_payload_draft = draft_text
                                    hitl_payload_draft = draft_text
                                    db.commit()
                                except Exception as ex:
                                    draft_text = f"Hi Customer, please review our pre-approved loan offers! Error: {ex}"
                                    step_model = db.get(ExecutionStep, step_id)
                                    step_model.hitl_payload_draft = draft_text
                                    hitl_payload_draft = draft_text
                                    db.commit()
                                    
                    event_queue.put(json.dumps({
                        'type': 'paused_hitl',
                        'step_number': current_step_number,
                        'tool_name': tool_name,
                        'draft': hitl_payload_draft
                    }) + "\n")
                    
                    try:
                        option, edited_content = feedback_queue.get(timeout=1800)
                        with get_db_context() as db:
                            step_model = db.get(ExecutionStep, step_id)
                            step_model.hitl_approved = True
                            step_model.hitl_payload_draft = edited_content
                            step_model.status = "pending"
                            plan_model = db.get(Plan, plan_id)
                            plan_model.status = "running"
                            db.commit()
                            
                        event_queue.put(json.dumps({
                            'type': 'status',
                            'message': f"Step {current_step_number} approved by Relationship Manager. Resuming..."
                        }) + "\n")
                        continue
                    except queue.Empty:
                        event_queue.put(json.dumps({'type': 'error', 'error': 'HITL feedback timeout.'}) + "\n")
                        break
                        
                event_queue.put(json.dumps({
                    'type': 'step_start',
                    'step_number': current_step_number,
                    'tool_name': tool_name,
                    'description': description,
                    'rationale': rationale
                }) + "\n")
                
                # Run step
                exec_res = execute_plan_step_crewai(plan_id, current_step_number, event_queue, memory)
                
                # Store log in memory
                memory.store("tool_logs", {
                    "step": current_step_number,
                    "tool": tool_name,
                    "input": tool_args,
                    "output": exec_res.get("result", exec_res.get("error", "Error")),
                    "ts": time.time(),
                    "status": "success" if exec_res["status"] == "success" else "failed"
                })
                
                # Evaluate loop transitions
                decision, reason = loop_ctrl.evaluate({
                    "status": "success" if exec_res["status"] == "success" else "failed",
                    "output": exec_res.get("result", ""),
                    "retry_count": exec_res.get("retry_count", 0)
                }, memory)
                
                event_queue.put(json.dumps({
                    'type': 'loop_decision',
                    'step_number': current_step_number,
                    'decision': decision,
                    'reason': reason
                }) + "\n")
                
                if decision == "abort":
                    event_queue.put(json.dumps({'type': 'error', 'error': reason}) + "\n")
                    try:
                        with get_db_context() as db:
                            plan_model = db.get(Plan, plan_id)
                            if plan_model:
                                plan_model.status = "failed"
                            db.commit()
                            
                            steps = db.query(ExecutionStep).filter(ExecutionStep.plan_id == plan_id).order_by(ExecutionStep.step_number.asc()).all()
                            steps_data_list = [
                                {
                                    'step_number': s.step_number,
                                    'tool_name': s.tool_name,
                                    'status': s.status,
                                    'description': s.description,
                                    'rationale': s.rationale
                                }
                                for s in steps
                            ]
                        
                        fail_explanation = f"⚠️ **Autopilot Execution Aborted**\n\nExecution was aborted due to safety constraints or successive failures:\n> {reason}\n\nPlease review the thoughts trace or retry the strategy."
                        
                        payload = {
                            "plan": {
                                "plan_id": plan_id,
                                "status": "failed",
                                "steps": steps_data_list
                            },
                            "steps": memory.entries.get("tool_logs", []),
                            "thoughts": memory.entries.get("thoughts", []),
                        }
                        if session_id:
                            save_message(session_id, "assistant", fail_explanation, agent_steps=payload)
                    except Exception as save_err:
                        logger.error(f"Failed to save aborted assistant message: {save_err}")
                    break
                    
                if decision == "replan":
                    new_steps = replan_failed_step(plan_id, current_step_number, exec_res.get("error", "Step failure"))
                    event_queue.put(json.dumps({
                        'type': 'replanned',
                        'step_number': current_step_number,
                        'error': exec_res.get("error", ""),
                        'new_steps': [
                            {
                                'step_number': s.get("step_number"),
                                'tool_name': s.get("tool_name"),
                                'description': s.get("description", ""),
                                'rationale': s.get("rationale", "")
                            }
                            for s in new_steps
                        ]
                    }) + "\n")
                    continue
                    
                if exec_res["status"] == "success":
                    event_queue.put(json.dumps({
                        'type': 'step_success',
                        'step_number': current_step_number,
                        'result_summary': str(exec_res['result'])[:300] + ("..." if len(str(exec_res['result'])) > 300 else "")
                    }) + "\n")
                    
                    event_queue.put(json.dumps({
                        'type': 'memory_update',
                        'step_number': current_step_number,
                        'summary': f"Stored results of '{tool_name}' in transient memory store."
                    }) + "\n")
                    
                if summariser.should_summarise(memory):
                    summary_text = summariser.compact(memory)
                    event_queue.put(json.dumps({
                        'type': 'memory_summary',
                        'summary': summary_text
                    }) + "\n")
                    
            # Complete! Synthesize answer
            event_queue.put(json.dumps({'type': 'status', 'message': 'Strategy completed. Synthesizing final advice response...'}) + "\n")
            
            final_answer = synthesize_answer(original_query, memory)
            
            suggestions = []
            try:
                suggestions = _generate_suggestions(original_query, final_answer)
            except Exception as ex:
                logger.warning(f"Unified Executor: Failed to generate suggestions: {ex}")
                
            data_grid = None
            for log in memory.entries.get("tool_logs", []):
                if log.get("status") == "success" and log.get("output"):
                    out = log.get("output")
                    if out.startswith("[") or out.startswith("{"):
                        try:
                            parsed = json.loads(out)
                            if isinstance(parsed, list) and len(parsed) > 0:
                                data_grid = parsed[:20]
                                break
                        except Exception:
                            pass
                            
            if session_id:
                save_message(session_id, "assistant", final_answer, agent_steps=memory.to_json())
                
            event_queue.put(json.dumps({
                'type': 'done',
                'final_answer': final_answer,
                'suggestions': suggestions,
                'data_grid': data_grid,
                'steps': [
                    {'step_number': s["step_number"], 'tool_name': s["tool_name"], 'status': s["status"]}
                    for s in steps_data
                ]
            }) + "\n")
            
        except Exception as ex:
            logger.error(f"Unified Executor Loop crash: {ex}")
            try:
                error_msg = str(ex)
                steps_data_list = []
                with get_db_context() as db:
                    steps = db.query(ExecutionStep).filter(ExecutionStep.plan_id == plan_id).order_by(ExecutionStep.step_number.asc()).all()
                    steps_data_list = [
                        {
                            'step_number': s.step_number,
                            'tool_name': s.tool_name,
                            'status': s.status,
                            'description': s.description,
                            'rationale': s.rationale
                        }
                        for s in steps
                    ]
                
                thoughts_list = memory.entries.get("thoughts", [])
                fail_explanation = f"⚠️ **Autopilot Execution Failed**\n\nAn unexpected error occurred during execution:\n> {error_msg}\n\nPlease review the completed steps above and retry strategy execution when ready."
                
                payload = {
                    "plan": {
                        "plan_id": plan_id,
                        "status": "failed",
                        "steps": steps_data_list
                    },
                    "steps": memory.entries.get("tool_logs", []),
                    "thoughts": thoughts_list,
                }
                if session_id:
                    save_message(session_id, "assistant", fail_explanation, agent_steps=payload)
            except Exception as save_err:
                logger.error(f"Failed to save recovery assistant message: {save_err}")
                
            event_queue.put(json.dumps({'type': 'error', 'error': str(ex)}) + "\n")
        finally:
            event_queue.put(None)
            
    thread = threading.Thread(target=_run_unified_executor, daemon=True)
    thread.start()
    
    try:
        while True:
            event = event_queue.get(timeout=2000)
            if event is None:
                break
            yield f"data: {event.strip()}\n\n"
    finally:
        if plan_id in plan_stream_registry:
            try:
                del plan_stream_registry[plan_id]
            except KeyError:
                pass

