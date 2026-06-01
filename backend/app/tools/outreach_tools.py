"""
Outreach message generation tools.
LLM calls use LiteLLM directly (same backend that CrewAI uses) so the model
accessed is gemini/gemini-1.5-flash without touching the google-genai SDK.
"""

from app.config import settings
from app.db.database import get_db_context
from app.db.repositories import campaign_repo, customer_repo
from app.tools.scoring_tools import _score_customer
from app.utils.helpers import fmt_inr
from app.utils.logger import get_logger
from crewai.tools import tool

logger = get_logger(__name__)


def _call_llm_for_message(prompt: str) -> str | None:
    """
    Calls the LLM via LiteLLM (CrewAI's underlying transport) to generate text.
    Returns None on failure so callers can use the fallback.
    """
    try:
        import litellm

        model_name = (
            "gemini/gemini-2.0-flash"
            if "2.5" in settings.gemini_model
            else f"gemini/{settings.gemini_model}"
        )
        response = litellm.completion(
            model=model_name,
            api_key=settings.gemini_api_key,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.75,
        )
        text = response.choices[0].message.content
        return text.strip() if text else None
    except Exception as e:
        logger.warning(f"LLM call failed, will use fallback: {e}")
        print(f"LLM Call Exception: {e}")  # Temporary debug print
        return None


def _fallback_message(name: str, signal: str, product_type: str) -> str:
    """Rule-based fallback when the LLM is unavailable."""
    first = name.split()[0]
    product_label = product_type.replace("_", " ").title()
    return (
        f"Hi {first}! 👋\n\n"
        f"Hope everything's going well. As your relationship manager at Loan It, "
        f"I've been keeping an eye on your account and noticed some financial activity "
        f"that made me think of reaching out.\n\n"
        f"We currently have some excellent {product_label} offers — competitive interest "
        f"rates, flexible tenure, and quick disbursal. It might be a great fit for your "
        f"current needs.\n\n"
        f"Would you like me to share more details or set up a quick call?\n\n"
        f"Warm regards,\nYour Relationship Manager, Loan It"
    )


@tool("generate_whatsapp_message")
def generate_whatsapp_message(
    customer_id: str,
    product_type: str = "personal_loan",
    tone: str = "friendly",
) -> str:
    """
    Generates a personalized WhatsApp message for a customer for a given product.
    Uses behavioral signals to craft a natural, non-templated message.
    Input: customer_id, product_type (default: personal_loan), tone (default: friendly)
    """
    try:
        # Load customer data and score inside separate sessions
        with get_db_context() as db:
            customer = customer_repo.get_customer_by_id(db, customer_id)
            if not customer:
                # Step 1: SQL LIKE substring match
                matches = customer_repo.search_customers(db, customer_id)
                if matches:
                    customer = matches[0]
                    customer_id = customer.customer_id
                    logger.info(
                        f"generate_whatsapp_message: LIKE-resolved '{customer_id}' to '{customer.full_name}'"
                    )
                else:
                    # Step 2: Levenshtein fuzzy match
                    fuzzy_results = customer_repo.fuzzy_search_customers(
                        db, customer_id, min_score=0.45, top_n=3
                    )
                    if fuzzy_results:
                        best_customer, best_score = fuzzy_results[0]
                        customer = best_customer
                        customer_id = customer.customer_id
                        logger.info(
                            f"generate_whatsapp_message: Fuzzy-resolved '{customer_id}' → "
                            f"'{customer.full_name}' ({customer.customer_id}) score={best_score}"
                        )
                    else:
                        return f"Customer '{customer_id}' not found."
            # Snapshot all needed attributes
            full_name = customer.full_name
            age = customer.age
            city = customer.city
            occupation = customer.occupation
            employment_type = customer.employment_type
            annual_income = customer.annual_income
            phone = customer.phone
            email = customer.email

        score = _score_customer(customer_id)
        signal_text = (
            ", ".join(score.positive_signals[:3])
            if score.positive_signals
            else "long-standing banking relationship"
        )
        fit_factors = (
            ", ".join(score.loan_fit_factors[:2])
            if score.loan_fit_factors
            else "stable financial profile"
        )
        product_label = product_type.replace("_", " ").title()

        prompt = f"""You are an elite Relationship Manager at an Indian private bank writing a WhatsApp message.

CLIENT PROFILE:
- Name: {full_name} (use FIRST NAME only)
- Age: {age}, City: {city}
- Occupation: {occupation} ({employment_type})
- Annual Income: {fmt_inr(annual_income)}
- Key Financial Signals: {signal_text}
- Loan Fit Context: {fit_factors}

PRODUCT TO OFFER: {product_label}
TONE: {tone}

Write a personalized, warm WhatsApp message (MAX 80 words, NO exceptions):
1. Address by FIRST NAME only — never "Dear"
2. Reference one specific behavioral insight naturally; never say "loan signal" explicitly
3. Position the product as a natural solution to their situation
4. Sound human and genuine, not automated or corporate
5. End with: "Warm regards, Your Relationship Manager, Loan It"
6. No markdown, no bullet points — flowing conversational text only

Output ONLY the message text. Zero preamble or explanation."""

        msg = _call_llm_for_message(prompt) or _fallback_message(
            full_name, signal_text, product_type
        )

        # Check if we have active stream registry and feedback queues for HITL
        import json
        import queue

        from app.agents.crews import get_current_session_id, session_stream_registry

        session_id = get_current_session_id()
        if session_id and session_id in session_stream_registry:
            registry = session_stream_registry[session_id]
            eq = registry["event_queue"]
            fq = registry["feedback_queue"]

            # Emit outreach review feedback prompt to event stream
            eq.put(
                json.dumps(
                    {
                        "type": "human_feedback",
                        "feedback_type": "outreach_review",
                        "message": f"Review drafted outreach message for {full_name}.",
                        "draft": msg,
                        "customer_name": full_name,
                        "phone": phone,
                        "options": ["Approve Draft", "Dismiss Draft"],
                    }
                )
                + "\n"
            )

            logger.info(
                f"generate_whatsapp_message: Pausing thread, waiting for RM review in session {session_id}"
            )
            try:
                # Pause thread up to 30 minutes
                response = fq.get(timeout=1800)
                option, edited_content = (
                    response if isinstance(response, tuple) else (response, None)
                )
                logger.info(
                    f"generate_whatsapp_message: Resumed thread, user choice: '{option}'"
                )

                if option == "Approve Draft":
                    if edited_content:
                        msg = edited_content
                else:
                    return f"Outreach message generation for {full_name} ({customer_id}) was cancelled/dismissed by the Relationship Manager."
            except queue.Empty:
                logger.warning(
                    f"generate_whatsapp_message: Timeout waiting for review in session {session_id}"
                )
                return f"Timeout waiting for Relationship Manager approval on outreach message for {full_name} ({customer_id})."

        # Persist approved outreach record
        with get_db_context() as db:
            outreach = campaign_repo.create_outreach(
                db,
                customer_id=customer_id,
                message=msg,
                channel="whatsapp",
            )
            outreach_id = outreach.outreach_id

        result = (
            f"### 💬 Personalized Outreach Draft\n\n"
            f"**Recipient:** **{full_name}** (`{customer_id}`)\n\n"
            f"--- \n\n"
            f"{msg}\n\n"
            f"--- \n\n"
            f"| Propensity Analytics | Diagnostic Value |\n"
            f"|:---|:---|\n"
            f"| **Propensity Score** | **{score.readiness_score}/100** ({score.conversion_band.upper()}) |\n"
            f"| **Primary Behavioral Trigger** | {score.positive_signals[0] if score.positive_signals else 'N/A'} |\n"
            f"| **Outreach Reference ID** | `{outreach_id}` |\n"
            f"| **Verification State** | ✅ **Approved by RM & Saved** |"
        )
        logger.info(
            f"generate_whatsapp_message: drafted outreach {outreach_id} for {customer_id}"
        )
        return result
    except Exception as e:
        logger.error(f"generate_whatsapp_message error: {e}")
        return f"Error generating message for {customer_id}: {str(e)}"


@tool("generate_bulk_messages")
def generate_bulk_messages(
    customer_ids_csv: str,
    product_type: str = "personal_loan",
) -> str:
    """
    Generates personalized messages for multiple customers (max 5 at once).
    Input: customer_ids_csv (comma-separated IDs e.g. 'CUST001,CUST002,CUST005'),
           product_type (default: personal_loan)
    """
    ids = [x.strip() for x in customer_ids_csv.split(",") if x.strip()][:5]
    if not ids:
        return "Error: No valid customer IDs provided."

    product_label = product_type.replace("_", " ").title()
    results: list[str] = [
        f"### 🚀 Bulk Outreach Dispatcher — **{product_label}**\n",
        f"> **Total Targets:** `{len(ids)}` customer profile(s) queued for generation\n",
        "---",
    ]

    for cid in ids:
        # Call the underlying function directly (both are in the same module)
        result = generate_whatsapp_message(
            customer_id=cid,
            product_type=product_type,
        )
        results.append(result)
        results.append("\n---\n")

    logger.info(f"generate_bulk_messages: processed {len(ids)} customers")
    return "\n".join(results)
