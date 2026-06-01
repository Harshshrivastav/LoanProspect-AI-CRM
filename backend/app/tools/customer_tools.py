from app.db.database import get_db_context
from app.db.repositories import customer_repo
from app.utils.helpers import fmt_inr, mask_email, mask_phone
from app.utils.logger import get_logger
from crewai.tools import tool

logger = get_logger(__name__)


@tool("fetch_customer_profile")
def fetch_customer_profile(customer_id: str) -> str:
    """
    Fetches complete customer profile including KYC details, account summary,
    product holdings, and detected loan signals. Use this before analyzing a customer.
    Input: customer_id (e.g. 'CUST001') or a customer name (fuzzy matching supported).
    """
    try:
        with get_db_context() as db:
            customer = customer_repo.get_customer_by_id(db, customer_id)
            
            # ── Semantic / Fuzzy Search Fallback with Human-In-The-Loop ──
            if not customer:
                # Step 1: Try SQL LIKE search (substring match)
                matches = customer_repo.search_customers(db, customer_id)
                if matches:
                    top = matches[0]
                    is_close_match = (
                        customer_id.lower() in top.full_name.lower() or
                        top.full_name.lower() in customer_id.lower()
                    )
                    if is_close_match:
                        customer = top
                        logger.info(f"fetch_customer_profile: Auto-resolved name query '{customer_id}' to ID '{customer.customer_id}'")
                
                # Step 2: If LIKE didn't work, try Levenshtein fuzzy match
                if not customer:
                    fuzzy_results = customer_repo.fuzzy_search_customers(db, customer_id, min_score=0.45, top_n=5)
                    
                    if fuzzy_results:
                        best_customer, best_score = fuzzy_results[0]
                        
                        # Auto-resolve for very high confidence single match
                        if best_score >= 0.80 and (len(fuzzy_results) == 1 or fuzzy_results[1][1] < 0.60):
                            customer = best_customer
                            logger.info(
                                f"fetch_customer_profile: Fuzzy auto-resolved '{customer_id}' → "
                                f"'{customer.full_name}' ({customer.customer_id}) with score {best_score}"
                            )
                        else:
                            # HITL: Present ranked disambiguation options
                            from app.agents.crews import get_current_session_id, session_stream_registry
                            import queue
                            import json
                            
                            session_id = get_current_session_id()
                            if session_id and session_id in session_stream_registry:
                                registry = session_stream_registry[session_id]
                                eq = registry["event_queue"]
                                fq = registry["feedback_queue"]
                                
                                # Build ranked options from all fuzzy matches
                                options = []
                                for cust, score in fuzzy_results:
                                    pct = int(score * 100)
                                    options.append(f"Proceed with {cust.customer_id} ({cust.full_name}) — {pct}% match")
                                options.append("Cancel search")
                                
                                candidates_str = ", ".join(
                                    f"**{c.full_name}** ({int(s*100)}%)" for c, s in fuzzy_results[:3]
                                )
                                msg = (
                                    f"I couldn't find an exact match for '{customer_id}'. "
                                    f"Here are the closest matches I found: {candidates_str}. "
                                    f"Which customer would you like to proceed with?"
                                )
                                
                                eq.put(
                                    json.dumps({
                                        "type": "human_feedback",
                                        "message": msg,
                                        "options": options
                                    }) + "\n"
                                )
                                
                                logger.info(f"fetch_customer_profile: Fuzzy HITL — {len(fuzzy_results)} candidates for '{customer_id}' in session {session_id}")
                                try:
                                    response = fq.get(timeout=300)
                                    user_choice = response[0] if isinstance(response, tuple) else response
                                    logger.info(f"fetch_customer_profile: HITL response: '{user_choice}'")
                                    
                                    if user_choice == "Cancel search":
                                        return f"Search for customer '{customer_id}' was cancelled by the user."
                                    
                                    # Parse which option was selected
                                    for cust, score in fuzzy_results:
                                        opt_label = f"Proceed with {cust.customer_id} ({cust.full_name})"
                                        if user_choice.startswith(opt_label):
                                            customer = cust
                                            break
                                    
                                    if not customer:
                                        # Fallback: if parsing fails, use the best match
                                        customer = best_customer
                                except queue.Empty:
                                    logger.warning(f"fetch_customer_profile: HITL timeout for '{customer_id}'")
                                    return f"Timeout waiting for user response on fuzzy search for '{customer_id}'."
                            else:
                                # Standalone/offline: auto-pick best fuzzy match
                                customer = best_customer
                                logger.info(f"fetch_customer_profile: Offline fuzzy-resolved '{customer_id}' → '{customer.full_name}'")
                    else:
                        return f"Customer '{customer_id}' not found, and no close matches were discovered."

            accounts = customer_repo.get_customer_accounts(db, customer.customer_id)
            products = customer_repo.get_product_holdings(db, customer.customer_id)
            signals = customer_repo.get_loan_signals(db, customer.customer_id)

            account = accounts[0] if accounts else None
            product_names = [
                p.product_type.replace("_", " ").title() for p in products if p.product_status == "active"
            ]
            signal_types = [s.signal_type.replace("_", " ").title() for s in signals]

            consent_label = "✅ Given (Outreach Eligible)" if customer.consent_marketing else "🚫 Denied (Outreach Blocked)"

            lines = [
                f"### 👤 Customer Profile: **{customer.full_name}** (`{customer_id}`)",
                "",
                "| Demographics & Settings | Profile Details |",
                "|:---|:---|",
                f"| **Age / Gender** | {customer.age} / {customer.gender} |",
                f"| **Location** | {customer.city} |",
                f"| **Occupation** | {customer.occupation} ({customer.employment_type}) |",
                f"| **Annual Income** | **{fmt_inr(customer.annual_income)}** |",
                f"| **Credit Score Proxy** | **{customer.credit_score_proxy}** |",
                f"| **Account Tenure** | {customer.account_tenure_months} months |",
                f"| **Risk Segment** | **{customer.risk_segment.upper()}** |",
                f"| **KYC Status** | `{customer.kyc_status.upper()}` |",
                f"| **Marketing Consent** | {consent_label} |",
                f"| **Contact Info** | 📞 {mask_phone(customer.phone)} <br> 📧 {mask_email(customer.email)} |",
                "",
                "#### 🏦 Financial Relationship Summary",
                "| Financial Metric | Value |",
                "|:---|:---|",
                f"| **Account Balance** | **{fmt_inr(account.current_balance) if account else 'N/A'}** |",
                f"| **Average Monthly Balance** | **{fmt_inr(account.avg_monthly_balance) if account else 'N/A'}** |",
                f"| **Monthly Income/Outflow** | 📥 {fmt_inr(account.monthly_inflow) if account else 'N/A'} / 📤 {fmt_inr(account.monthly_outflow) if account else 'N/A'} |",
                "",
                f"* **Active Products Held:** {', '.join(product_names) if product_names else '*None*'}",
                f"* **Detected Loan Signals:** {', '.join(signal_types) if signal_types else '*None detected*'}",
            ]
            logger.info(f"fetch_customer_profile called for {customer_id}")
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"fetch_customer_profile error: {e}")
        return f"Error fetching profile for {customer_id}: {str(e)}"


@tool("list_customers_brief")
def list_customers_brief(limit: int = 20) -> str:
    """
    Returns a brief list of all customers with their key attributes.
    Use this to get an overview of the customer portfolio.
    Input: limit (default 20)
    """
    try:
        with get_db_context() as db:
            customers = customer_repo.get_all_customers(db, skip=0, limit=limit)
            lines = [
                f"### 📋 Customer Brief Summary (Showing {len(customers)} customers)",
                "",
                "| Customer ID | Full Name | Location | Occupation | Annual Income | Risk Segment | Consent |",
                "|---|:---|:---|:---|:---|:---:|:---:|",
            ]
            for c in customers:
                consent_icon = "✅" if c.consent_marketing else "🚫"
                lines.append(
                    f"| `{c.customer_id}` | **{c.full_name}** | {c.city} | "
                    f"{c.occupation} ({c.employment_type}) | **{fmt_inr(c.annual_income)}** | "
                    f"**{c.risk_segment.upper()}** | {consent_icon} |"
                )
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"list_customers_brief error: {e}")
        return f"Error listing customers: {str(e)}"


@tool("get_customer_risk_summary")
def get_customer_risk_summary(customer_id: str) -> str:
    """
    Returns a brief risk assessment summary for a customer.
    Input: customer_id
    """
    try:
        with get_db_context() as db:
            customer = customer_repo.get_customer_by_id(db, customer_id)
            if not customer:
                return f"Customer {customer_id} not found."

            products = customer_repo.get_product_holdings(db, customer_id)
            total_debt = sum(
                p.outstanding_amount for p in products if p.outstanding_amount
            )
            total_emi = sum(p.emi_amount for p in products if p.emi_amount)
            monthly_income = (
                customer.annual_income / 12 if customer.annual_income else 1.0
            )
            emi_ratio = (total_emi / monthly_income * 100) if monthly_income > 0 else 0

            risk_items: list[str] = []
            if not customer.consent_marketing:
                risk_items.append("- 🚫 **No marketing consent** — Outreach blocked under RBI rules")
            if emi_ratio > 50:
                risk_items.append(f"- ⚠️ **High EMI burden** — ({emi_ratio:.0f}% of monthly income)")
            if customer.risk_segment == "high":
                risk_items.append("- 🔴 **High risk segment** — Requires senior Relationship Manager sign-off")
            if customer.kyc_status != "verified":
                risk_items.append(f"- ⚠️ **Unverified KYC** — (Current status: `{customer.kyc_status}`)")

            risk_flags_str = "\n".join(risk_items) if risk_items else "- ✅ **No major risk flags detected**"

            lines = [
                f"### ⚠️ Risk Summary: **{customer.full_name}** (`{customer_id}`)",
                "",
                "| Risk Metric / Indicator | Value / Status |",
                "|:---|:---|",
                f"| **Risk Segment** | **{customer.risk_segment.upper()}** |",
                f"| **Credit Score Proxy** | **{customer.credit_score_proxy}** |",
                f"| **Total Outstanding Debt** | **{fmt_inr(total_debt)}** |",
                f"| **Total Monthly EMIs** | **{fmt_inr(total_emi)}** |",
                f"| **EMI to Income Ratio** | **{emi_ratio:.1f}%** |",
                "",
                "#### 🚩 Detected Compliance & Risk Flags",
                risk_flags_str
            ]
            return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_customer_risk_summary error: {e}")
        return f"Error fetching risk summary for {customer_id}: {str(e)}"
