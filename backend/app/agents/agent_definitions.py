"""
CrewAI Agent Definitions
All 6 agents are defined here and reused across crews.
Backed by Gemini via LiteLLM (model="gemini/gemini-2.5-flash").
"""


from app.config import settings
from app.tools.audit_tools import get_audit_trail, log_audit_event
from app.tools.campaign_tools import (
    create_campaign_payload,
    get_campaign_status_summary,
    get_top_prospect_ids_for_campaign,
)
from app.tools.compliance_tools import get_compliance_summary, validate_compliance
from app.tools.customer_tools import (
    fetch_customer_profile,
    get_customer_risk_summary,
    list_customers_brief,
)
from app.tools.outreach_tools import generate_bulk_messages, generate_whatsapp_message
from app.tools.scoring_tools import (
    compute_loan_readiness_score,
    get_prospect_explanation,
    rank_personal_loan_prospects,
)
from app.tools.transaction_tools import (
    calculate_cashflow_trend,
    detect_life_event_spends,
    fetch_transaction_summary,
    find_high_value_spending_customers,
)
from crewai import LLM, Agent


def _make_llm() -> LLM:
    model_name = f"gemini/{settings.gemini_model}"
    if "2.5" in settings.gemini_model:
        model_name = "gemini/gemini-2.0-flash"
    return LLM(
        model=model_name,
        api_key=settings.gemini_api_key,
        temperature=0.3,
        is_litellm=True,
        max_tokens=2000,
    )



def get_prospect_discovery_agent() -> Agent:
    return Agent(
        role="Prospect Discovery Specialist",
        goal=(
            "Scan the customer portfolio to find the most likely personal loan prospects "
            "based on behavioral signals and financial patterns."
        ),
        backstory=(
            "You are a senior data analyst at Loan It with 10 years of experience identifying "
            "high-intent loan prospects from transaction patterns. You specialize in detecting "
            "life events, spending anomalies, and financial readiness signals."
        ),
        tools=[
            list_customers_brief,
            rank_personal_loan_prospects,
            fetch_customer_profile,
            find_high_value_spending_customers,
            generate_whatsapp_message,
            generate_bulk_messages,
            log_audit_event,
        ],
        llm=_make_llm(),
        verbose=settings.agent_verbose,
        max_iter=settings.max_agent_iterations,
        allow_delegation=False,
    )


def get_evidence_aggregation_agent() -> Agent:
    return Agent(
        role="Evidence Aggregation Analyst",
        goal=(
            "Collect and summarize all behavioral evidence for a specific customer — "
            "transactions, life events, cashflow trends, and product gaps."
        ),
        backstory=(
            "You are a meticulous financial analyst who builds comprehensive evidence dossiers "
            "on banking customers. You fetch all relevant data from transactions, products, "
            "and behavioral patterns to create a complete picture for credit decisions."
        ),
        tools=[
            fetch_customer_profile,
            fetch_transaction_summary,
            detect_life_event_spends,
            calculate_cashflow_trend,
            get_customer_risk_summary,
            find_high_value_spending_customers,
            list_customers_brief,
            rank_personal_loan_prospects,
            generate_whatsapp_message,
            generate_bulk_messages,
            log_audit_event,
        ],
        llm=_make_llm(),
        verbose=settings.agent_verbose,
        max_iter=settings.max_agent_iterations,
        allow_delegation=False,
    )


def get_loan_readiness_agent() -> Agent:
    return Agent(
        role="Loan Readiness Assessor",
        goal=(
            "Produce a precise loan readiness score and detailed recommendation for a customer "
            "based on evidence collected."
        ),
        backstory=(
            "You are a credit assessment specialist at Loan It. You combine deterministic "
            "scoring rules with evidence analysis to produce loan readiness scores, "
            "conversion predictions, and next-best-action recommendations."
        ),
        tools=[
            compute_loan_readiness_score,
            get_prospect_explanation,
            fetch_customer_profile,
            list_customers_brief,
            rank_personal_loan_prospects,
            log_audit_event,
        ],
        llm=_make_llm(),
        verbose=settings.agent_verbose,
        max_iter=settings.max_agent_iterations,
        allow_delegation=False,
    )


def get_outreach_writer_agent() -> Agent:
    return Agent(
        role="Personalized Outreach Writer",
        goal=(
            "Write highly personalized, compliant WhatsApp messages that reference the "
            "customer's specific behavioral triggers and financial situation. "
            "YOU MUST ALWAYS use the 'generate_whatsapp_message' tool (or 'generate_bulk_messages') "
            "to generate outreach messages; NEVER write or output the message yourself."
        ),
        backstory=(
            "You are Loan It's elite relationship communication specialist. "
            "You craft personalized messages that feel human and relevant, "
            "referencing actual customer behavior without sounding automated. "
            "You always personalize based on life events and financial signals. "
            "You understand that you must NEVER generate or output an outreach message directly in your thoughts "
            "or final response; you must ALWAYS delegate message generation to the 'generate_whatsapp_message' tool. "
            "This is mandatory to trigger the compliance check and open the review sidebar for Relationship Manager approval."
        ),
        tools=[
            generate_whatsapp_message,
            generate_bulk_messages,
            fetch_customer_profile,
            rank_personal_loan_prospects,
            find_high_value_spending_customers,
            list_customers_brief,
            log_audit_event,
        ],
        llm=_make_llm(),
        verbose=settings.agent_verbose,
        max_iter=settings.max_agent_iterations,
        allow_delegation=False,
    )


def get_compliance_agent() -> Agent:
    return Agent(
        role="Compliance & Risk Validator",
        goal=(
            "Validate all outreach for regulatory compliance: marketing consent, KYC status, "
            "message safety, and risk assessment."
        ),
        backstory=(
            "You are Loan It's compliance officer specializing in digital outreach regulations. "
            "You ensure all customer communications meet RBI guidelines, marketing consent "
            "requirements, and internal risk policies before any message is sent."
        ),
        tools=[
            validate_compliance,
            get_compliance_summary,
            get_customer_risk_summary,
            log_audit_event,
        ],
        llm=_make_llm(),
        verbose=settings.agent_verbose,
        max_iter=settings.max_agent_iterations,
        allow_delegation=False,
    )


def get_campaign_coordinator_agent() -> Agent:
    return Agent(
        role="Campaign Coordinator",
        goal=(
            "Build targeted campaign batches, identify the right customer segments, "
            "manage campaign execution state, and summarize campaign intelligence."
        ),
        backstory=(
            "You are Loan It's campaign strategy manager. You identify the best customer "
            "cohorts for campaigns, create structured campaign payloads, and coordinate "
            "multi-customer outreach at scale while maintaining quality."
        ),
        tools=[
            get_top_prospect_ids_for_campaign,
            create_campaign_payload,
            get_campaign_status_summary,
            rank_personal_loan_prospects,
            find_high_value_spending_customers,
            generate_whatsapp_message,
            generate_bulk_messages,
            log_audit_event,
        ],
        llm=_make_llm(),
        verbose=settings.agent_verbose,
        max_iter=settings.max_agent_iterations,
        allow_delegation=False,
    )
