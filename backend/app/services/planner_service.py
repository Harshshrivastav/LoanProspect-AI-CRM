"""
Planner Service — generates and revises plans using Gemini.
Uses LiteLLM with structured JSON output formatting.
"""

import json
import uuid
from typing import Any, Dict, List
import litellm

from app.config import settings
from app.db.database import get_db_context
from app.db.models import Plan, ExecutionStep
from app.utils.logger import get_logger

logger = get_logger(__name__)

# System instructions detailing tools and output schema
PLANNER_SYSTEM_PROMPT = """You are the Lead CRM Planning & Strategy Agent for LoanProspect AI.
Your goal is to parse a bank manager's high-level request, determine what customer data needs to be fetched, analyzed, ranked, or acted upon, and compile a robust, step-by-step sequential execution plan.

You have access to the following backend tools:
1. `list_customers_brief`: Returns a summary list of all customers (customer_id, full_name, KYC, marketing consent). Input: none.
2. `fetch_customer_profile`: Fetches detailed financial status, accounts, active product holdings, and RM signals. Input: customer_id (string).
3. `fetch_transaction_summary`: Returns income, expense totals, and category breakdowns. Input: customer_id (string).
4. `detect_life_event_spends`: Scans transactions for medical, education, wedding, travel, or renovation spends. Input: customer_id (string).
5. `calculate_cashflow_trend`: Analyzes month-over-month inflow/outflow trends. Input: customer_id (string).
6. `compute_loan_readiness_score`: Calculates deterministic loan readiness score (0-100) and risk factors. Input: customer_id (string).
7. `rank_personal_loan_prospects`: Generates a ranked list of all personal loan prospects. Input: none.
8. `get_prospect_explanation`: Generates a friendly, human-readable scoring narrative. Input: customer_id (string).
9. `generate_whatsapp_message`: Drafts a hyper-personalized outreach WhatsApp message. Input: customer_id (string), product_type (default: 'personal_loan'), tone (default: 'friendly'). *Requires Human Review (hitl)*.
10. `validate_compliance`: Validates compliance check for customer marketing consent, KYC, and safety. Input: customer_id (string).
11. `get_compliance_summary`: Returns compliance metrics summary. Input: none.
12. `get_customer_risk_summary`: Compiles debt burden and risk indicators. Input: customer_id (string).
13. `create_campaign_payload`: Saves campaign to DB. Input: campaign_name, segment_name, target_count.
14. `get_campaign_status_summary`: Returns a summary of campaigns. Input: none.
15. `get_top_prospect_ids_for_campaign`: Selects top N prospect IDs. Input: campaign_id (string), top_n (integer).
16. `get_audit_trail`: Fetches security audit logs. Input: none.

Rules for Plan Formulation:
1. **Chain-of-Thought (CoT) First**: Before writing any step, explain the thought process, what data it depends on, and why it is necessary.
2. **Decouple Message Gen from Approval**: Any step calling `generate_whatsapp_message` MUST set `hitl_required = true` so the bank manager can review, edit, and preview.
3. **Sequential Arguments**: Steps must pass output variables of previous steps (e.g. dynamic parameters) using the format $step<number>.output.<variable> (for example, "$step1.output.customer_ids" or "$step2.output.top_customer_id").
4. **Step-by-step Progression**: Do not try to bunch unrelated tasks. Proceed sequentially.

You must return a valid JSON object matching this schema EXACTLY:
{
  "rationale": "High-level planning thought process explaining the strategy.",
  "steps": [
    {
      "step_number": 1,
      "description": "Short description of what this step does",
      "rationale": "Chain-of-thought logic explaining why this tool is selected",
      "tool_name": "name_of_tool_to_call",
      "tool_args": {
        "argument_name": "argument_value" // Can be hardcoded or dynamic e.g. "$step1.output.customer_id"
      },
      "max_retries": 3,
      "hitl_required": false
    }
  ]
}
"""

import time

def call_gemini_with_retry(messages: list, response_format: dict = None, temperature: float = 0.2, max_attempts: int = 5) -> Any:
    """
    Invokes LiteLLM completion with rate limit (429 / RESOURCE_EXHAUSTED) resilience.
    If rate-limited, sleeps and retries with exponential backoff.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            kwargs = {
                "model": f"gemini/{settings.gemini_model}",
                "api_key": settings.gemini_api_key,
                "messages": messages,
                "temperature": temperature
            }
            if response_format:
                kwargs["response_format"] = response_format
                
            response = litellm.completion(**kwargs)
            return response
        except Exception as e:
            err_msg = str(e)
            is_rate_limit = any(x in err_msg.lower() for x in ["429", "rate limit", "resource_exhausted", "quota", "limit"])
            
            if is_rate_limit and attempt < max_attempts:
                sleep_sec = attempt * 10 + 5
                logger.warning(f"Gemini API rate limit hit. Sleeping for {sleep_sec}s and retrying (Attempt {attempt}/{max_attempts})... Error: {err_msg}")
                time.sleep(sleep_sec)
            else:
                logger.error(f"Gemini API call failed on attempt {attempt}: {err_msg}")
                raise e

import re
from app.services.memory_store import MemoryStore

def is_simple_query(query: str) -> bool:
    """
    Classifies a query as simple vs complex using robust, optimized heuristics.
    Simple queries execute instantly via direct crew routing, bypassing plan reviews.
    """
    q = query.lower()
    
    # Complex indicators: multiple tasks or portfolio/campaign-wide inquiries
    complex_words = [
        "campaign", "bulk", "outreach", "prospects", "whatsapp messages", 
        "rank", "list all", "personal loan prospects", "personal loan candidates", 
        "compliance blocks", "compliance check on", "life events", "cashflow trend"
    ]
    if any(word in q for word in complex_words):
        return False
        
    # Heuristics: if it contains a single customer reference and is short, it is simple
    customer_ids = re.findall(r"CUST\d{3}", q, re.IGNORECASE)
    if len(customer_ids) == 1 and len(q) < 120:
        return True
        
    # Single name queries are often simple
    names_indicators = ["details of", "kyc of", "credit score of", "balance of", "fetch profile", "who is"]
    if any(ind in q for ind in names_indicators) and len(q) < 90:
        return True
        
    # Default is complex for robust multi-agent sequencing
    return False


def synthesize_answer(original_query: str, memory: MemoryStore) -> str:
    """
    Synthesizes the final unified relationship-manager-facing answer using Gemini.
    Incorporates the accumulated insights, logs, and findings stored in memory.
    """
    logger.info(f"Synthesizing final answer for query: '{original_query}'")
    
    context = memory.get_context_for_planner()
    
    prompt = f"""You are the Lead RM Advisor for LoanProspect AI. 
The bank relationship manager originally requested:
"{original_query}"

An orchestrator has executed a step-by-step sequential tool strategy to answer this request.
Here is the complete execution memory and findings:
{context}

Please synthesize a comprehensive, cohesive, professional, and visually stunning relationship manager response in Markdown.

RULES:
1. Ground your answer strictly in the facts and customer findings present in the memory context. Do not make up any customer names, loan scores, balances, or transaction details.
2. Use professional corporate banking vocabulary.
3. Structure your response beautifully with Markdown:
   - Use bold headers and clean bullet points.
   - If customer IDs are listed with readiness scores or risk factors, present them in a clear markdown table.
   - Use alerts or high-density warning callouts for KYC pending issues or compliance marketing consent blocks.
4. If WhatsApp outreach drafts were generated or approved, list them clearly with metadata.
5. Conclude with clear, actionable next steps for the Relationship Manager.

Provide ONLY the synthesized Markdown response."""

    try:
        response = call_gemini_with_retry(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to synthesize final response: {e}")
        # Return fallback local synthesis based on tool logs
        summary_parts = []
        for log in memory.entries.get("tool_logs", []):
            if log.get("status") == "success":
                summary_parts.append(f"- **Step {log.get('step')} ({log.get('tool')})**: Done.")
        return f"### Strategy Execution Completed\n\nI have successfully executed the action plan to satisfy your request.\n\n**Key Actions Performed**:\n" + "\n".join(summary_parts)


def generate_plan(original_query: str, session_id: str | None = None, history_context: str | None = None) -> Dict[str, Any]:
    """
    Parses original user request, calls Gemini to build a structured execution plan,
    saves the plan to the SQLite database, and returns the plan structure.
    """
    logger.info(f"Generating plan for request: '{original_query}'")
    
    system_content = PLANNER_SYSTEM_PROMPT
    if history_context:
        system_content += f"\n\nHere is the recent conversation history in this session to ground your plan:\n{history_context}"
    
    try:
        response = call_gemini_with_retry(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"Create an execution plan to satisfy this request: '{original_query}'"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        
        raw_text = response.choices[0].message.content
        logger.debug(f"Planner raw output: {raw_text}")
        
        plan_data = json.loads(raw_text)
    except Exception as e:
        logger.error(f"Planner LLM call failed or failed to parse JSON: {e}")
        # Fallback basic plan
        plan_data = {
            "rationale": f"Fallback plan due to planner error: {str(e)}",
            "steps": [
                {
                    "step_number": 1,
                    "description": "List prospects as safe fallback",
                    "rationale": "Fallback planning step due to LLM error",
                    "tool_name": "rank_personal_loan_prospects",
                    "tool_args": {},
                    "max_retries": 2,
                    "hitl_required": False
                }
            ]
        }

    # Save to SQLite db
    plan_id = str(uuid.uuid4())
    with get_db_context() as db:
        plan_model = Plan(
            plan_id=plan_id,
            session_id=session_id,
            original_query=original_query,
            status="running"
        )
        db.add(plan_model)
        db.flush()
        
        for step in plan_data.get("steps", []):
            step_model = ExecutionStep(
                step_id=str(uuid.uuid4()),
                plan_id=plan_id,
                step_number=step["step_number"],
                description=step["description"],
                rationale=step["rationale"],
                tool_name=step["tool_name"],
                tool_args=json.dumps(step.get("tool_args", {})),
                status="pending",
                max_retries=step.get("max_retries", 3),
                hitl_required=step.get("hitl_required", False)
            )
            db.add(step_model)
            
        db.flush()
        
    logger.info(f"Plan saved to DB with ID: {plan_id} ({len(plan_data.get('steps', []))} steps)")
    plan_data["plan_id"] = plan_id
    plan_data["status"] = "running"
    return plan_data


def replan_failed_step(plan_id: str, failed_step_number: int, error_msg: str) -> List[Dict[str, Any]]:
    """
    Called when a step fails after all retries are exhausted. Re-invokes Gemini to plan
    a corrected set of steps bypassing or fixing the failure, deletes remaining pending steps,
    and appends the new ones to the plan.
    """
    logger.warning(f"Re-planning plan {plan_id} at failed step {failed_step_number} due to error: {error_msg}")
    
    with get_db_context() as db:
        plan = db.get(Plan, plan_id)
        if not plan:
            logger.error(f"Plan {plan_id} not found during re-planning")
            return []
        
        original_query = plan.original_query
        
        # Load completed/failed steps to give context to the Planner
        past_steps = []
        for step in plan.steps:
            if step.step_number <= failed_step_number:
                past_steps.append({
                    "step_number": step.step_number,
                    "tool_name": step.tool_name,
                    "status": step.status,
                    "result_summary": str(step.tool_result)[:200]
                })

    replan_prompt = f"""We are executing the following user goal: '{original_query}'

Below is the execution history of steps that have already run:
{json.dumps(past_steps, indent=2)}

CRITICAL ERROR: Step {failed_step_number} failed after all retries. Error message: "{error_msg}"

Please re-plan the remaining steps to achieve the original goal. 
Avoid the tool that failed, choose alternate parameters, or add diagnostic/fallback steps as appropriate. 
Output ONLY the remaining steps starting from step_number {failed_step_number + 1}. Do not repeat completed steps.
Format your response exactly matching the original JSON schema.
"""

    try:
        response = call_gemini_with_retry(
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": replan_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        plan_data = json.loads(response.choices[0].message.content)
        new_steps = plan_data.get("steps", [])
    except Exception as e:
        logger.error(f"Re-planner LLM call failed: {e}")
        # Simplest fallback: single audit logs diagnostic step
        new_steps = [
            {
                "step_number": failed_step_number + 1,
                "description": "Log error details to audit trail",
                "rationale": "Fallback diagnostic step due to re-planner error",
                "tool_name": "get_audit_trail",
                "tool_args": {},
                "max_retries": 1,
                "hitl_required": False
            }
        ]

    # Save re-planned steps in DB
    with get_db_context() as db:
        # Delete pending steps that are > failed_step_number
        db.query(ExecutionStep).filter(
            ExecutionStep.plan_id == plan_id,
            ExecutionStep.step_number > failed_step_number,
            ExecutionStep.status == "pending"
        ).delete()
        
        # Append new steps, ensuring sequential numbering starting from failed_step_number + 1
        current_num = failed_step_number + 1
        for step in new_steps:
            step_model = ExecutionStep(
                step_id=str(uuid.uuid4()),
                plan_id=plan_id,
                step_number=current_num,
                description=step["description"],
                rationale=step["rationale"],
                tool_name=step["tool_name"],
                tool_args=json.dumps(step.get("tool_args", {})),
                status="pending",
                max_retries=step.get("max_retries", 3),
                hitl_required=step.get("hitl_required", False)
            )
            db.add(step_model)
            current_num += 1
            
        db.commit()
        
    logger.info(f"Successfully re-planned and appended {len(new_steps)} new steps to plan {plan_id}")
    return new_steps
