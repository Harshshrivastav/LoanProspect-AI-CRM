"""
CrewAI Crew Definitions
Three main crews:
1. ProspectAnalysisCrew — analyzes a single customer (used by client portal)
2. BulkOutreachCrew     — generates campaign messages for multiple customers
3. ConversationCrew     — drives the agentic chat workspace
"""

import json
import queue
import threading
import time

import litellm
from app.agents.agent_definitions import (
    get_campaign_coordinator_agent,
    get_compliance_agent,
    get_evidence_aggregation_agent,
    get_loan_readiness_agent,
    get_outreach_writer_agent,
    get_prospect_discovery_agent,
)
from app.config import settings
from app.utils.logger import get_logger
from crewai import Crew, Process, Task

logger = get_logger(__name__)

# Registries to support Human-in-the-Loop (HITL) blocking feedback inside tools
# Maps thread ID -> session ID
thread_session_registry = {}
# Maps session ID -> { "event_queue": event_queue, "feedback_queue": feedback_queue }
session_stream_registry = {}
# Thread-local storage fallback
thread_context = threading.local()


def get_current_session_id() -> str | None:
    tid = threading.get_ident()
    if tid in thread_session_registry:
        return thread_session_registry[tid]
    # Fallback 1: If there's exactly one active session in the stream registry (typical for single-user dev), use it
    if len(session_stream_registry) == 1:
        return list(session_stream_registry.keys())[0]
    # Fallback 2: Check all values in the thread session registry
    if thread_session_registry:
        return list(thread_session_registry.values())[-1]
    return getattr(thread_context, "session_id", None)


# ── Crew 1: Prospect Analysis (single customer) ───────────────────────────────


def run_prospect_analysis_crew(customer_id: str) -> dict:
    """
    Runs a 4-agent pipeline to fully analyze one customer:
    Evidence Agent → Loan Readiness Agent → Compliance Agent → Outreach Writer Agent
    Returns a structured result dict.
    """
    evidence_agent = get_evidence_aggregation_agent()
    scoring_agent = get_loan_readiness_agent()
    compliance_agent = get_compliance_agent()
    outreach_agent = get_outreach_writer_agent()

    evidence_task = Task(
        description=(
            f"Collect complete behavioral evidence for customer {customer_id}. "
            f"Use fetch_customer_profile, fetch_transaction_summary, detect_life_event_spends, "
            f"and calculate_cashflow_trend. Summarize all findings."
        ),
        expected_output=(
            "A comprehensive evidence summary including: account balance, monthly cashflow, "
            "detected life events (medical/renovation/education/wedding), spending trend, "
            "products held, and key behavioral signals."
        ),
        agent=evidence_agent,
    )

    scoring_task = Task(
        description=(
            f"Using the evidence collected, compute the loan readiness score for customer {customer_id}. "
            f"Use compute_loan_readiness_score and get_prospect_explanation. "
            f"Provide the score, conversion band, all positive signals, risk flags, and next best action."
        ),
        expected_output=(
            "Loan readiness score (0-100), conversion band (high/medium/low), confidence level, "
            "list of positive signals, risk flags, recommendation reason, and next best action."
        ),
        agent=scoring_agent,
        context=[evidence_task],
    )

    compliance_task = Task(
        description=(
            f"Validate compliance for customer {customer_id}. "
            f"Use validate_compliance to check marketing consent, KYC status, and risk segment. "
            f"Report any blocks or warnings."
        ),
        expected_output=(
            "Compliance status (COMPLIANT/NON-COMPLIANT), any blocking issues, warnings, "
            "and whether outreach is permitted."
        ),
        agent=compliance_agent,
        context=[scoring_task],
    )

    outreach_task = Task(
        description=(
            f"If compliance check passed, generate a personalized WhatsApp message for customer {customer_id} "
            f"for a personal loan. Use generate_whatsapp_message. "
            f"Reference the customer's strongest behavioral signal naturally."
        ),
        expected_output=(
            "A personalized WhatsApp message (max 80 words) referencing the customer's behavioral triggers, "
            "plus the outreach_id and propensity score."
        ),
        agent=outreach_agent,
        context=[scoring_task, compliance_task],
    )

    crew = Crew(
        agents=[evidence_agent, scoring_agent, compliance_agent, outreach_agent],
        tasks=[evidence_task, scoring_task, compliance_task, outreach_task],
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = crew.kickoff(inputs={"customer_id": customer_id})
        return {
            "customer_id": customer_id,
            "status": "completed",
            "result": str(result),
            "tasks": {
                "evidence": str(evidence_task.output) if evidence_task.output else "",
                "scoring": str(scoring_task.output) if scoring_task.output else "",
                "compliance": str(compliance_task.output)
                if compliance_task.output
                else "",
                "outreach": str(outreach_task.output) if outreach_task.output else "",
            },
        }
    except Exception as e:
        logger.error(f"ProspectAnalysisCrew error: {e}")
        return {"customer_id": customer_id, "status": "error", "error": str(e)}


# ── Crew 2: Bulk Outreach / Campaign ─────────────────────────────────────────


def run_bulk_outreach_crew(
    campaign_name: str,
    product_type: str = "personal_loan",
    target_count: int = 5,
) -> dict:
    """
    Runs a 3-agent pipeline to create and prepare a campaign:
    Campaign Coordinator → Compliance Agent → Outreach Writer Agent
    """
    coordinator = get_campaign_coordinator_agent()
    compliance_agent = get_compliance_agent()
    outreach_agent = get_outreach_writer_agent()

    discover_task = Task(
        description=(
            f"Find the top {target_count} customers for a {product_type} campaign. "
            f"Use get_top_prospect_ids_for_campaign and rank_personal_loan_prospects. "
            f"Then create the campaign using create_campaign_payload with campaign_name='{campaign_name}'. "
            f"Return the list of target customer IDs."
        ),
        expected_output=f"Campaign created with {target_count} target customers. List of customer IDs included.",
        agent=coordinator,
    )

    validate_task = Task(
        description=(
            "For each target customer identified, run compliance validation using validate_compliance. "
            "Report which customers are compliant and which should be excluded."
        ),
        expected_output="List of compliant customer IDs approved for outreach.",
        agent=compliance_agent,
        context=[discover_task],
    )

    messages_task = Task(
        description=(
            f"Generate personalized {product_type} WhatsApp messages for all compliant customers. "
            f"Use generate_bulk_messages with the customer IDs from the compliance check. "
            f"Each message must reference a specific behavioral signal."
        ),
        expected_output=f"Personalized WhatsApp messages for all approved customers, with outreach IDs.",
        agent=outreach_agent,
        context=[validate_task],
    )

    crew = Crew(
        agents=[coordinator, compliance_agent, outreach_agent],
        tasks=[discover_task, validate_task, messages_task],
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = crew.kickoff()
        return {
            "campaign_name": campaign_name,
            "status": "completed",
            "result": str(result),
            "tasks": {
                "discovery": str(discover_task.output) if discover_task.output else "",
                "compliance": str(validate_task.output) if validate_task.output else "",
                "messages": str(messages_task.output) if messages_task.output else "",
            },
        }
    except Exception as e:
        logger.error(f"BulkOutreachCrew error: {e}")
        return {"status": "error", "error": str(e)}


# ── Crew 3: Streaming Conversation Crew ──────────────────────────────────────


class StreamingConversationCrew:
    """
    Powers the agentic conversation workspace.
    Uses CrewAI with a step_callback that emits NDJSON events to a queue,
    which the FastAPI SSE endpoint reads from to stream to the frontend.

    Event format (NDJSON, one JSON per line):
    {"type": "status",     "message": "...", "agent": "..."}
    {"type": "agent_start","agent": "...", "task": "..."}
    {"type": "tool_call",  "tool": "...", "input": "..."}
    {"type": "tool_result","tool": "...", "output": "..."}
    {"type": "agent_done", "agent": "...", "result": "..."}
    {"type": "chunk",      "text": "..."}
    {"type": "done",       "steps": [...], "final_answer": "..."}
    {"type": "error",      "error": "..."}
    """

    def __init__(self):
        self.event_queue: queue.Queue = queue.Queue()

    def _make_step_callback(self, steps_list: list = None) -> callable:
        """Creates a step_callback for CrewAI that queues NDJSON events.
        Emits rich thought explanations and tool selection reasoning."""
        q = self.event_queue
        _step_counter = {"n": 0}

        # Human-readable descriptions for each tool
        _TOOL_EXPLANATIONS = {
            "list_customers_brief": "Scanning the full customer portfolio to identify candidates",
            "fetch_customer_profile": "Pulling detailed financial profile, accounts, and product holdings",
            "fetch_transaction_summary": "Analyzing income, expenses, and transaction category breakdowns",
            "detect_life_event_spends": "Scanning for behavioral triggers — medical, education, wedding, renovation spends",
            "calculate_cashflow_trend": "Computing month-over-month cashflow trajectory and anomalies",
            "compute_loan_readiness_score": "Running the 8-dimension loan readiness scoring engine (0-100)",
            "get_prospect_explanation": "Generating a human-readable narrative explaining the prospect's score",
            "rank_personal_loan_prospects": "Ranking all customers by personal loan conversion propensity",
            "generate_whatsapp_message": "Composing a personalized WhatsApp outreach message",
            "generate_bulk_messages": "Batch-generating personalized outreach messages for multiple customers",
            "validate_compliance": "Verifying marketing consent, KYC status, and regulatory clearance",
            "get_compliance_summary": "Pulling compliance metrics across the portfolio",
            "get_customer_risk_summary": "Analyzing debt burden, EMI ratios, and risk indicators",
            "create_campaign_payload": "Creating a new campaign record in the CRM database",
            "get_campaign_status_summary": "Fetching current campaign pipeline status",
            "get_top_prospect_ids_for_campaign": "Selecting top prospect IDs for targeted campaign",
            "get_audit_trail": "Retrieving security and action audit logs",
            "log_audit_event": "Logging this action for audit trail compliance",
            "find_high_value_spending_customers": "Scanning entire customer base for high-value spending patterns",
        }

        def step_callback(agent_output):
            """Called by CrewAI after each agent step. Emits rich NDJSON events."""
            try:
                # Emit the agent's internal thought/reasoning
                if hasattr(agent_output, "thought") and agent_output.thought:
                    q.put(
                        json.dumps(
                            {"type": "thought", "text": str(agent_output.thought)}
                        )
                        + "\n"
                    )

                # Emit tool selection with a generative explanation
                if hasattr(agent_output, "tool") and agent_output.tool:
                    _step_counter["n"] += 1
                    tool_name = str(agent_output.tool)
                    tool_input = (
                        str(agent_output.tool_input)
                        if hasattr(agent_output, "tool_input")
                        else ""
                    )
                    explanation = _TOOL_EXPLANATIONS.get(
                        tool_name, f"Executing {tool_name}"
                    )

                    # Emit a thought explaining WHY this tool was selected
                    q.put(
                        json.dumps(
                            {
                                "type": "thought",
                                "text": f"Step {_step_counter['n']}: I'm selecting `{tool_name}` — {explanation}. {('Input: ' + tool_input[:80]) if tool_input else ''}",
                            }
                        )
                        + "\n"
                    )

                    q.put(
                        json.dumps(
                            {
                                "type": "tool_call",
                                "tool": tool_name,
                                "input": tool_input,
                                "step_number": _step_counter["n"],
                                "explanation": explanation,
                            }
                        )
                        + "\n"
                    )

                # Emit tool result
                if hasattr(agent_output, "result") and agent_output.result:
                    result_str = str(agent_output.result)
                    tool_name = (
                        str(agent_output.tool)
                        if hasattr(agent_output, "tool")
                        else "tool"
                    )

                    # Check for HITL required flag
                    if "[HITL_REQUIRED]" in result_str:
                        # Find the JSON array in the string or use default
                        options = ["Yes, proceed", "No, cancel"]
                        import re

                        match = re.search(r"\[HITL_REQUIRED\]\s*(.*)", result_str)
                        msg = match.group(1) if match else "Clarification required."
                        try:
                            # Try parsing options if provided like: [HITL_REQUIRED] message | ["opt1", "opt2"]
                            if "|" in msg:
                                parts = msg.split("|")
                                msg = parts[0].strip()
                                options = json.loads(parts[1].strip())
                        except:
                            pass

                        q.put(
                            json.dumps(
                                {
                                    "type": "human_feedback",
                                    "message": msg,
                                    "options": options,
                                }
                            )
                            + "\n"
                        )

                    # Generate a brief summary of what the result contains
                    result_preview = result_str[:300]
                    if steps_list is not None:
                        steps_list.append(
                            {
                                "tool": tool_name,
                                "input": tool_input if "tool_input" in locals() else "",
                                "observation": result_preview,
                                "ts": int(time.time() * 1000),
                            }
                        )
                    q.put(
                        json.dumps(
                            {
                                "type": "tool_result",
                                "tool": tool_name,
                                "output": result_preview,
                                "step_number": _step_counter["n"],
                            }
                        )
                        + "\n"
                    )
            except Exception as ex:
                logger.debug(f"step_callback error: {ex}")

        return step_callback

    def _make_task_callback(self) -> callable:
        """Returns a callback invoked when each CrewAI task completes."""
        q = self.event_queue

        def task_callback(task_output):
            try:
                # Try to extract the actual agent name from the task
                agent_name = "Agent"
                if hasattr(task_output, "agent") and task_output.agent:
                    agent_name = str(task_output.agent)
                elif hasattr(task_output, "task") and hasattr(
                    task_output.task, "agent"
                ):
                    agent_name = (
                        str(task_output.task.agent.role)
                        if hasattr(task_output.task.agent, "role")
                        else "Agent"
                    )

                result_text = (
                    str(task_output.raw)[:400]
                    if hasattr(task_output, "raw")
                    else str(task_output)[:400]
                )

                q.put(
                    json.dumps(
                        {
                            "type": "agent_done",
                            "agent": agent_name,
                            "result": result_text,
                        }
                    )
                    + "\n"
                )
            except Exception:
                pass

        return task_callback

    def run_streaming(
        self,
        user_message: str,
        session_id: str = None,
        customer_context: str = None,
        history_context: str = None,
    ):
        """
        Runs the conversation crew in a background thread and yields NDJSON event
        strings.  The caller reads from self.event_queue via this generator.
        """
        # Register session stream and feedback queues
        steps = []
        if session_id:
            session_stream_registry[session_id] = {
                "event_queue": self.event_queue,
                "feedback_queue": queue.Queue(),
            }

        # Emit initial status event
        self.event_queue.put(
            json.dumps(
                {
                    "type": "status",
                    "message": "Analyzing your request...",
                    "agent": "Orchestrator",
                }
            )
            + "\n"
        )

        # Route the message to the most relevant agents
        relevant_agents, _ = self._route_message(user_message, customer_context)

        # Generate a DYNAMIC plan using Gemini based on the actual user query
        plan_steps = self._generate_dynamic_plan(user_message, relevant_agents)

        self.event_queue.put(json.dumps({"type": "plan", "steps": plan_steps}) + "\n")

        # Attach step callbacks to all agents
        step_cb = self._make_step_callback(steps)
        for agent in relevant_agents:
            agent.step_callback = step_cb

        context_hint = (
            f"Customer context: {customer_context}. " if customer_context else ""
        )
        history_hint = (
            f"\n--- Conversation History Context ---\n{history_context}\n--- End History ---\n\n"
            if history_context
            else ""
        )

        task = Task(
            description=(
                f"{context_hint}{history_hint}User request: {user_message}\n\n"
                f"CRITICAL — CONVERSATION MEMORY & PRONOUN RESOLUTION:\n"
                f"- If the user references a specific position or index (e.g. 'the second person', 'the third candidate', 'the first one', 'last one', 'the Nth highest-ranked prospect') from a list or table in the conversation history context, "
                f"look at the previous assistant messages in the chronological thread. Find the customer ID at that corresponding rank/position (e.g., if previous message showed Rank 2: CUST005 Vikram Singh, then 'second person' is CUST005). "
                f"If the reference is to 'the Nth highest-ranked prospect', parse the list of customer IDs available from previous tool outputs (e.g., from 'rank_personal_loan_prospects') and select the customer ID at that specific rank.\n"
                f"Use that resolved customer ID in your tool calls.\n"
                f"- If the user says 'he', 'she', 'him', 'her', 'this customer', 'them', 'that person', 'the same one', or any pronoun referring to a customer, "
                f"look at the CONVERSATION MEMORY block above for 'LAST CUSTOMER DISCUSSED'. Use that customer ID directly in your tool calls. "
                f"DO NOT ask the user to repeat the customer ID. Resolve it from memory.\n"
                f"- If no memory context exists and you cannot determine which customer, provide clickable options in your response "
                f"like: 'Did you mean **Aarav Sharma (CUST001)**?' based on recently discussed customers.\n\n"
                f"CRITICAL — MESSAGE WRITING / DRAFTING MANDATE:\n"
                f"- If the user asks you to write, draft, generate, redraft, compose, or send a WhatsApp or outreach message for ANY customer, "
                f"YOU MUST ALWAYS call the 'generate_whatsapp_message' tool (which takes a SINGLE customer_id: string) "
                f"or 'generate_bulk_messages' (which takes a comma-separated string of customer_ids_csv: string, e.g., 'CUST001,CUST002') to generate the message.\n"
                f"- NEVER write, draft, or output the message yourself in your thoughts or direct final response. You MUST delegate this entirely by invoking the 'generate_whatsapp_message' tool.\n"
                f"- This is absolutely mandatory because the tool triggers a strict, audited compliance flow and opens the Human-in-the-Loop review sidebar for the RM. Writing it directly bypasses compliance and is a severe regulatory violation.\n"
                f"- If you only have the customer's name, first look up or resolve their SINGLE customer ID from memory, and then call 'generate_whatsapp_message' with that ID.\n\n"
                f"Use your available tools to fully answer the request. "
                f"Be specific and data-driven. Show your reasoning. "
                f"If asked to search, scan, or filter customers based on broad spending criteria (like medical or education spends exceeding a certain amount), use the find_high_value_spending_customers tool to scan the entire customer base. "
                f"If asked about a specific customer, fetch their profile and transactions first. "
                f"If asked to generate messages, use the outreach tools. "
                f"Always log your action using log_audit_event.\n\n"
                f"CRITICAL FORMATTING REQUIREMENT:\n"
                f"- ALWAYS format lists, details, and tables as clean, valid GFM Markdown tables (using standard pipes and dashes: |---|).\n"
                f"- Use 🔥 HIGH, ⚡ MEDIUM, 🔵 LOW intent bands and emoji markers where appropriate.\n"
                f"- Use bold headings, list items (- item), and blockquotes (>) instead of raw spaces, terminal alignments, or ASCII divider lines (e.g., ==== or ---- or ────).\n"
                f"- Let the frontend render semantic HTML tables and premium callouts natively."
            ),
            expected_output=(
                "A comprehensive, data-driven response to the RM's request. "
                "Include specific customer names, scores, amounts, and actionable recommendations in gorgeous, styled GFM Markdown."
            ),
            agent=relevant_agents[0],
            callback=self._make_task_callback(),
        )

        crew = Crew(
            agents=relevant_agents[:3],  # cap at 3 agents
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            step_callback=step_cb,
            task_callback=self._make_task_callback(),
        )

        # steps list is declared at parent scope

        def _run_crew():
            tid = threading.get_ident()
            if session_id:
                thread_session_registry[tid] = session_id
                thread_context.session_id = session_id
            try:
                self.event_queue.put(
                    json.dumps(
                        {
                            "type": "agent_start",
                            "agent": relevant_agents[0].role,
                            "task": "Processing your request...",
                        }
                    )
                    + "\n"
                )
                result = crew.kickoff(
                    inputs={
                        "query": user_message,
                        "customer_context": customer_context or "",
                    }
                )
                final = str(result)
                # Stream the final answer in chunks with small delays to make it feel real and premium
                chunk_size = 15
                for i in range(0, len(final), chunk_size):
                    chunk = final[i : i + chunk_size]
                    self.event_queue.put(
                        json.dumps({"type": "chunk", "text": chunk}) + "\n"
                    )
                    time.sleep(0.01)  # 10ms delay to simulate real-time token streaming
                self.event_queue.put(
                    json.dumps(
                        {
                            "type": "done",
                            "steps": steps,
                            "final_answer": final,
                        }
                    )
                    + "\n"
                )
            except Exception as e:
                logger.error(f"StreamingConversationCrew error: {e}")
                self.event_queue.put(
                    json.dumps({"type": "error", "error": str(e)}) + "\n"
                )
            finally:
                if session_id:
                    try:
                        del thread_session_registry[tid]
                    except KeyError:
                        pass
                self.event_queue.put(None)  # sentinel — signals end of stream

        thread = threading.Thread(target=_run_crew, daemon=True)
        thread.start()

        # Yield events from queue until sentinel, cleaning up session registry at the end.
        # Use a generous HITL timeout (2000s) so that when a tool is blocked on fq.get(timeout=1800)
        # the outer loop does NOT time out and kill the SSE stream before user reviews the draft.
        HITL_WAIT_TIMEOUT = (
            2000  # seconds – must be > fq.get(timeout=1800) in outreach_tools
        )
        try:
            while True:
                try:
                    event = self.event_queue.get(timeout=HITL_WAIT_TIMEOUT)
                    if event is None:
                        break
                    # Skip internal heartbeat events – they just keep the loop alive
                    if (
                        event.strip() == json.dumps({"type": "heartbeat"}) + "\n"
                        or json.loads(event.strip()).get("type") == "heartbeat"
                    ):
                        continue
                    yield event
                except queue.Empty:
                    yield (
                        json.dumps(
                            {
                                "type": "error",
                                "error": "Agent timeout – no response in 30 minutes.",
                            }
                        )
                        + "\n"
                    )
                    break
                except Exception:
                    pass
        finally:
            if session_id and session_id in session_stream_registry:
                try:
                    del session_stream_registry[session_id]
                except KeyError:
                    pass

    def _route_message(self, message: str, customer_context: str = None) -> tuple:
        """Routes a user message to the most relevant set of agents (max 3)."""
        msg_lower = message.lower()

        agents = []
        desc = []

        # Evidence + scoring for customer analysis (includes pronouns for follow-ups)
        if any(
            kw in msg_lower
            for kw in [
                "analyze",
                "analyse",
                "profile",
                "transaction",
                "customer",
                "score",
                "readiness",
                "cust",
                " he ",
                " she ",
                " him ",
                " her ",
                " them ",
                "this customer",
                "that person",
                "the same",
                "prospect",
            ]
        ):
            agents.extend(
                [get_evidence_aggregation_agent(), get_loan_readiness_agent()]
            )
            desc.append("customer analysis and scoring")

        # Outreach for message generation
        if any(
            kw in msg_lower
            for kw in ["message", "whatsapp", "outreach", "write", "generate", "send"]
        ):
            agents.extend([get_outreach_writer_agent(), get_compliance_agent()])
            desc.append("outreach message generation")

        # Campaign tools
        if any(
            kw in msg_lower
            for kw in ["campaign", "prospect", "top", "rank", "list", "batch"]
        ):
            agents.extend(
                [get_campaign_coordinator_agent(), get_prospect_discovery_agent()]
            )
            desc.append("campaign and prospect discovery")

        # Default: prospect discovery + evidence
        if not agents:
            agents = [get_prospect_discovery_agent(), get_evidence_aggregation_agent()]
            desc = ["general analysis"]

        # Deduplicate while preserving order
        seen: set = set()
        unique: list = []
        for a in agents:
            if a.role not in seen:
                seen.add(a.role)
                unique.append(a)

        return unique[:3], desc

    def _generate_dynamic_plan(self, user_message: str, agents: list) -> list[str]:
        """Uses Gemini to generate a dynamic, query-specific execution plan.
        Falls back to a basic plan on error."""
        agent_roles = [a.role for a in agents[:3]] if agents else ["Analyst"]
        agent_tools = []
        for a in agents[:3]:
            if hasattr(a, "tools") and a.tools:
                agent_tools.extend(
                    [t.name if hasattr(t, "name") else str(t) for t in a.tools[:5]]
                )

        prompt = f"""You are a CRM strategy planner. A bank relationship manager just asked:
"{user_message}"

Available agents: {", ".join(agent_roles)}
Available tools: {", ".join(set(agent_tools[:12]))}

Generate exactly 3-5 specific analytical steps the agents will take to answer this query.
Each step should be a short, specific action description (max 15 words).
Be specific to the EXACT query — don't use generic boilerplate.

Return a JSON array of strings. Example:
["Rank all 75 customers by personal loan readiness score", "Extract top 5 high-intent prospects with scores above 80", "Generate personalized WhatsApp messages for each top prospect"]

Return ONLY the JSON array, nothing else."""

        try:
            model_name = (
                "gemini/gemini-2.0-flash"
                if "2.5" in settings.gemini_model
                else f"gemini/{settings.gemini_model}"
            )
            response = litellm.completion(
                model=model_name,
                api_key=settings.gemini_api_key,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)
            # Handle both {"steps": [...]} and plain [...] formats
            if isinstance(parsed, dict):
                steps = parsed.get(
                    "steps",
                    parsed.get("plan", list(parsed.values())[0] if parsed else []),
                )
            elif isinstance(parsed, list):
                steps = parsed
            else:
                raise ValueError("Unexpected format")

            if steps and isinstance(steps, list) and len(steps) >= 2:
                return [str(s) for s in steps[:6]]
        except Exception as e:
            logger.warning(f"Dynamic plan generation failed, using fallback: {e}")

        # Fallback: generate a basic but still query-aware plan
        short_query = user_message[:60]
        return [
            f"Analyzing query: '{short_query}'",
            f"Routing to {agent_roles[0]} for data extraction",
            "Processing analytical evaluations and scoring",
            "Compiling data-driven response with recommendations",
        ]
