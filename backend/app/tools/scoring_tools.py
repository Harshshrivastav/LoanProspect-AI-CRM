"""
Loan readiness scoring engine.

Scoring dimensions (total = 100 points):
  1. Salary stability     0-20  — consistent monthly salary credits
  2. Income level         0-15  — annual income bracket
  3. Life-event signals   0-25  — detected medical / education / travel / home spends
  4. Balance health       0-15  — avg monthly balance relative to income
  5. No personal loan     0-10  — no active personal loan in portfolio
  6. Spending trend       0-10  — rising debit over last 3m vs prior 3m
  7. Tenure               0-10  — account tenure in months
  8. Credit behavior      0-5   — EMI-to-income ratio (lower = better)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.db.database import get_db_context
from app.db.repositories import customer_repo, transaction_repo
from app.utils.helpers import fmt_inr
from app.utils.logger import get_logger
from crewai.tools import tool

logger = get_logger(__name__)

# Life-event keywords used to detect intent in transaction categories / signal types.
_LIFE_KEYWORDS = {
    "medical",
    "healthcare",
    "hospital",
    "health",
    "home_renovation",
    "renovation",
    "home improvement",
    "education",
    "school",
    "college",
    "tuition",
    "wedding",
    "marriage",
    "travel",
    "holiday",
    "vacation",
    "vehicle",
    "automobile",
    "car",
}


@dataclass
class ProspectScore:
    customer_id: str
    full_name: str
    readiness_score: int  # 0-100
    conversion_band: str  # "high" | "medium" | "low"
    confidence: float  # 0.0-1.0
    positive_signals: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    recommendation_reason: str = ""
    next_best_action: str = ""
    suggested_product: str = "personal_loan"
    recommended_channel: str = "whatsapp"
    loan_fit_factors: list[str] = field(default_factory=list)
    score_breakdown: dict = field(default_factory=dict)


# Dynamic underwriting & campaign factors updated from CRM cockpit
_DYNAMIC_FACTORS = {
    "campaign_focus": "general",
    "risk_appetite": "moderate"
}

def set_dynamic_factors(focus: str, risk: str):
    global _DYNAMIC_FACTORS
    _DYNAMIC_FACTORS["campaign_focus"] = focus
    _DYNAMIC_FACTORS["risk_appetite"] = risk
    logger.info(f"Dynamic Factors Updated: Campaign Focus = {focus}, Risk Appetite = {risk}")

def _score_customer(customer_id: str) -> ProspectScore:

    """
    Internal deterministic scoring function.
    Called by @tool wrappers and service layer.
    All DB I/O is done inside a single get_db_context() block;
    only plain Python types leave the session.
    """
    with get_db_context() as db:
        customer = customer_repo.get_customer_by_id(db, customer_id)
        if not customer:
            return ProspectScore(
                customer_id=customer_id,
                full_name="Unknown",
                readiness_score=0,
                conversion_band="low",
                confidence=0.0,
                risk_flags=["Customer not found in database"],
            )

        # ── Snapshot all ORM attributes to plain Python values ──────────────
        cid = customer.customer_id
        full_name = customer.full_name
        annual_income = customer.annual_income or 0.0
        employment_type = customer.employment_type or ""
        tenure = customer.account_tenure_months or 0
        risk_segment = (customer.risk_segment or "medium").lower()
        consent_ok = customer.consent_marketing
        kyc_status = (customer.kyc_status or "unverified").lower()

        accounts = customer_repo.get_customer_accounts(db, customer_id)
        products = customer_repo.get_product_holdings(db, customer_id)
        signals = customer_repo.get_loan_signals(db, customer_id)

        # Account snapshot
        account = accounts[0] if accounts else None
        avg_monthly_balance = account.avg_monthly_balance if account else 0.0

        # Product snapshot: (product_type, status, outstanding, emi)
        product_data = [
            (
                (p.product_type or "").lower(),
                (p.product_status or "").lower(),
                p.outstanding_amount or 0.0,
                p.emi_amount or 0.0,
            )
            for p in products
        ]

        # Signal snapshot
        signal_types = [(s.signal_type or "").lower() for s in signals]
        has_signals = len(signals) > 0

        # Transaction data (plain dicts from repo — already safe)
        tx_summary_90 = transaction_repo.get_transaction_summary(
            db, customer_id, days=90
        )
        txns_180 = transaction_repo.get_transactions_by_customer(
            db, customer_id, days=180
        )

        # Snapshot 180-day txns to tuples inside session
        txn_tuples = [(t.txn_date, t.txn_type, t.amount) for t in txns_180]

    # ── All computation now uses plain Python types only ────────────────────
    monthly_income = annual_income / 12 if annual_income else 1.0
    score_breakdown: dict[str, str] = {}
    positive_signals: list[str] = []
    risk_flags: list[str] = []
    loan_fit_factors: list[str] = []

    # ── Extract dynamic campaign factors into local vars ──────────────────
    focus = _DYNAMIC_FACTORS["campaign_focus"]
    risk_appetite = _DYNAMIC_FACTORS["risk_appetite"]

    # ── 1. Salary stability (0-20) ──────────────────────────────────────────
    salary_months = tx_summary_90.get("salary_months", 0)
    if salary_months >= 3:
        s1 = 20
        positive_signals.append(
            f"Regular salary credits detected ({salary_months} months)"
        )
        loan_fit_factors.append("Stable salaried income history")
    elif salary_months == 2:
        s1 = 12
        positive_signals.append(f"Salary credited for {salary_months} months")
    elif salary_months == 1:
        s1 = 6
    else:
        s1 = 0
        if employment_type.lower() == "salaried":
            risk_flags.append(
                "No salary credits detected in last 90 days despite salaried status"
            )
    score_breakdown["Salary Stability"] = f"{s1}/20"

    # ── 2. Income level (0-15) ──────────────────────────────────────────────
    if annual_income >= 1_500_000:
        s2 = 15
        positive_signals.append(f"High annual income: {fmt_inr(annual_income)}")
        loan_fit_factors.append(f"Annual income {fmt_inr(annual_income)}")
    elif annual_income >= 1_000_000:
        s2 = 12
        positive_signals.append(f"Good annual income: {fmt_inr(annual_income)}")
        loan_fit_factors.append(f"Annual income {fmt_inr(annual_income)}")
    elif annual_income >= 700_000:
        s2 = 9
        loan_fit_factors.append(f"Annual income {fmt_inr(annual_income)}")
    elif annual_income >= 500_000:
        s2 = 6
    elif annual_income >= 300_000:
        s2 = 3
    else:
        s2 = 0
        risk_flags.append(f"Low annual income: {fmt_inr(annual_income)}")
    score_breakdown["Income Level"] = f"{s2}/15"

    # ── 3. Life-event signals (0-25) ────────────────────────────────────────
    # Check existing loan signals
    detected_events: set[str] = set()
    for st in signal_types:
        for kw in _LIFE_KEYWORDS:
            if kw in st:
                detected_events.add(st.replace("_", " ").title())
                break

    # Check transaction categories (last 90 days)
    by_category = tx_summary_90.get("by_category", {})
    for cat, data in by_category.items():
        cat_lower = cat.lower()
        for kw in _LIFE_KEYWORDS:
            if kw in cat_lower and data.get("total", 0) >= 10_000:
                detected_events.add(cat.replace("_", " ").title())
                break

    num_events = len(detected_events)
    s3 = min(25, num_events * 9)  # 9 pts per event, capped at 25

    if detected_events:
        events_str = ", ".join(list(detected_events)[:3])
        positive_signals.append(f"Life-event spending detected: {events_str}")
        loan_fit_factors.append(f"Active spending signals: {events_str}")
    else:
        risk_flags.append(
            "No life-event spending signals detected in recent transactions"
        )
    score_breakdown["Life Event Signals"] = f"{s3}/25"

    # ── 4. Balance health (0-15) ────────────────────────────────────────────
    months_of_income = avg_monthly_balance / monthly_income if monthly_income > 0 else 0
    if months_of_income >= 3:
        s4 = 15
        positive_signals.append(
            f"Strong avg balance: {fmt_inr(avg_monthly_balance)} (≥3× monthly income)"
        )
    elif months_of_income >= 2:
        s4 = 12
        positive_signals.append(f"Good avg balance: {fmt_inr(avg_monthly_balance)}")
    elif months_of_income >= 1:
        s4 = 8
    elif months_of_income >= 0.5:
        s4 = 4
    else:
        s4 = 0
        risk_flags.append(f"Low avg monthly balance: {fmt_inr(avg_monthly_balance)}")
    score_breakdown["Balance Health"] = f"{s4}/15"

    # ── 5. No active personal loan (0-10) ───────────────────────────────────
    has_active_personal_loan = any(
        "personal" in ptype and pstatus == "active"
        for ptype, pstatus, _, _ in product_data
    )
    if not has_active_personal_loan:
        s5 = 10
        positive_signals.append("No existing personal loan — fresh product opportunity")
        loan_fit_factors.append("Eligible for first personal loan")
    else:
        s5 = 0
        risk_flags.append("Already holds an active personal loan")
    score_breakdown["No Existing Personal Loan"] = f"{s5}/10"

    # ── 6. Spending trend — rising debit (0-10) ─────────────────────────────
    cutoff_3m = date.today() - timedelta(days=90)
    recent_debits = sum(
        amt for dt, tt, amt in txn_tuples if tt == "debit" and dt >= cutoff_3m
    )
    prior_debits = sum(
        amt for dt, tt, amt in txn_tuples if tt == "debit" and dt < cutoff_3m
    )
    if prior_debits > 0:
        spend_growth = (recent_debits - prior_debits) / prior_debits
        if spend_growth > 0.20:
            s6 = 10
            positive_signals.append(
                f"Spending rising {spend_growth * 100:.0f}% — indicates active financial needs"
            )
        elif spend_growth > 0.05:
            s6 = 6
        elif spend_growth >= -0.10:
            s6 = 3
        else:
            s6 = 0
    else:
        s6 = 5  # neutral if no prior-period data
    score_breakdown["Spending Trend"] = f"{s6}/10"

    # ── 7. Account tenure (0-10) ─────────────────────────────────────────────
    if tenure >= 36:
        s7 = 10
        positive_signals.append(f"Long-standing customer ({tenure} months tenure)")
    elif tenure >= 24:
        s7 = 8
    elif tenure >= 12:
        s7 = 5
    elif tenure >= 6:
        s7 = 2
    else:
        s7 = 0
        risk_flags.append(f"Short account tenure: {tenure} months")
    score_breakdown["Account Tenure"] = f"{s7}/10"

    # ── 8. Credit behavior — EMI burden (0-5) ────────────────────────────────
    total_emi = sum(emi for _, _, _, emi in product_data)
    emi_ratio = (total_emi / monthly_income * 100) if monthly_income > 0 else 0
    if emi_ratio <= 20:
        s8 = 5
        positive_signals.append(f"Low EMI burden ({emi_ratio:.0f}% of monthly income)")
    elif emi_ratio <= 30:
        s8 = 3
    elif emi_ratio <= 40:
        s8 = 1
    else:
        s8 = 0
        risk_flags.append(f"High EMI burden: {emi_ratio:.0f}% of monthly income")
    score_breakdown["Credit Behavior (EMI)"] = f"{s8}/5"

    # ── Raw total ────────────────────────────────────────────────────────────
    raw_total = s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8

    # Apply Dynamic Campaign Focus boosts
    if focus == "renovation":
        has_reno = any("renovation" in st.lower() or "renovation" in cat.lower() 
                       for st in signal_types for cat in by_category.keys())
        if has_reno:
            raw_total += 12
            positive_signals.append("🔥 Dynamic Campaign Boost: Active renovation signals detected (+12 pts)")
    elif focus == "medical":
        has_med = any("medical" in st.lower() or "medical" in cat.lower() or "hospital" in st.lower() or "hospital" in cat.lower()
                      for st in signal_types for cat in by_category.keys())
        if has_med:
            raw_total += 15
            positive_signals.append("🔥 Dynamic Campaign Boost: Emergency medical spends identified (+15 pts)")
    elif focus == "festive":
        raw_total += 8
        positive_signals.append("🎁 Festive Season General Boost: Seasonal shopping lift applied (+8 pts)")

    # ── Compliance and Appetite penalties ─────────────────────────────────────────────────
    if not consent_ok:
        raw_total = max(0, raw_total - 15)
        risk_flags.append("🚫 No marketing consent — outreach blocked")
    if kyc_status != "verified":
        raw_total = max(0, raw_total - 10)
        risk_flags.append(f"🚫 KYC not verified (status: {kyc_status})")
    
    # Risk Appetite weighting
    if risk_appetite == "conservative":
        if risk_segment == "high":
            raw_total = max(0, raw_total - 20)
            risk_flags.append("🚫 Conservative Risk Guidelines: Heavier penalty applied to High Risk segment (-20 pts)")
        else:
            raw_total = max(0, raw_total - 5)
        if emi_ratio > 30:
            raw_total = max(0, raw_total - 15)
            risk_flags.append(f"🚫 Conservative Risk Guidelines: Heavier penalty for debt load (EMI: {emi_ratio:.0f}% of income)")
    elif risk_appetite == "aggressive":
        if risk_segment == "high":
            raw_total = max(0, raw_total - 5)
            risk_flags.append("⚡ Aggressive Appetite Boost: Reduced penalty for High Risk segment")
        else:
            raw_total = min(100, raw_total + 5)
    else: # moderate
        if risk_segment == "high":
            raw_total = max(0, raw_total - 10)
            risk_flags.append("🔴 High risk segment classification")

    total = min(100, max(0, raw_total))

    # ── Conversion band ──────────────────────────────────────────────────────
    if total >= 70:
        band = "high"
    elif total >= 45:
        band = "medium"
    else:
        band = "low"

    # ── Confidence (data completeness proxy) ─────────────────────────────────
    completeness_points = sum(
        [
            1 if account else 0,
            1 if salary_months > 0 else 0,
            1 if detected_events else 0,
            1 if len(txn_tuples) >= 10 else 0,
            1 if has_signals else 0,
        ]
    )
    confidence = round(
        min(0.99, 0.40 + (completeness_points / 5) * 0.50 + (total / 500)), 2
    )

    # ── Dynamic Product recommendation ──
    suggested_prod = "personal_loan"
    if focus == "renovation":
        suggested_prod = "home_renovation_loan"
    elif focus == "medical":
        suggested_prod = "medical_emergency_loan"
    elif focus == "festive":
        suggested_prod = "festive_personal_loan"

    # ── Recommendation text ──────────────────────────────────────────────────
    if band == "high":
        rec = (
            f"{full_name} is a strong {suggested_prod.replace('_', ' ')} prospect (score {total}/100). "
            "Multiple positive financial signals detected — immediate outreach recommended."
        )
        nba = "Send personalized WhatsApp message → Schedule RM call within 48 hours"
    elif band == "medium":
        rec = (
            f"{full_name} shows moderate {suggested_prod.replace('_', ' ')} readiness (score {total}/100). "
            "Nurture with informational content before product pitch."
        )
        nba = "Send soft-touch WhatsApp → Follow up in 7 days"
    else:
        rec = (
            f"{full_name} is a low-priority prospect (score {total}/100). "
            "Re-evaluate after 30 days or when new signals emerge."
        )
        nba = "Monitor for life-event signals → Re-score next cycle"

    return ProspectScore(
        customer_id=cid,
        full_name=full_name,
        readiness_score=total,
        conversion_band=band,
        confidence=confidence,
        positive_signals=positive_signals,
        risk_flags=risk_flags,
        recommendation_reason=rec,
        next_best_action=nba,
        suggested_product=suggested_prod,
        recommended_channel="whatsapp",
        loan_fit_factors=loan_fit_factors,
        score_breakdown=score_breakdown,
    )



# ── Tool wrappers ─────────────────────────────────────────────────────────────


@tool("compute_loan_readiness_score")
def compute_loan_readiness_score(customer_id: str) -> str:
    """
    Computes a 0-100 loan readiness score for a specific customer using
    deterministic rules: salary stability, income, life events, balance, tenure.
    Input: customer_id (e.g. 'CUST001')
    """
    try:
        score = _score_customer(customer_id)
        band_emoji = "🔥 **HIGH**" if score.conversion_band == "high" else ("⚡ **MEDIUM**" if score.conversion_band == "medium" else "🔵 **LOW**")
        
        pos_list = "\n".join(f"- ✅ {s}" for s in score.positive_signals) if score.positive_signals else "- *(No positive signals detected)*"
        risk_list = "\n".join(f"- ⚠️ {f}" for f in score.risk_flags) if score.risk_flags else "- ✅ *None*"
        
        breakdown_rows = "\n".join(f"| {k} | **{v}** |" for k, v in score.score_breakdown.items())
        
        lines = [
            f"### 📊 Loan Readiness Score: **{score.full_name}** (`{score.customer_id}`)",
            "",
            "| Parameter | Value |",
            "|:---|:---|",
            f"| **Readiness Score** | **{score.readiness_score}/100** |",
            f"| **Conversion Band** | {band_emoji} |",
            f"| **Confidence Level** | **{score.confidence * 100:.0f}%** |",
            "",
            "#### 🟢 Positive Signals",
            pos_list,
            "",
            "#### 🔴 Risk Flags",
            risk_list,
            "",
            "#### 📋 Recommendation & Next Steps",
            f"> 💡 **Recommendation:** {score.recommendation_reason}",
            "> ",
            f"> ⚡ **Next Best Action:** {score.next_best_action}",
            "",
            "#### ⚙️ Score Breakdown",
            "| Diagnostic Dimension | Score Contribution |",
            "|:---|:---:|",
            breakdown_rows,
        ]
        logger.info(
            f"compute_loan_readiness_score: {customer_id} → {score.readiness_score}/100 ({score.conversion_band})"
        )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"compute_loan_readiness_score error: {e}")
        return f"Error scoring customer {customer_id}: {str(e)}"


@tool("rank_personal_loan_prospects")
def rank_personal_loan_prospects(limit: int = 20) -> str:
    """
    Scans all customers, scores each one for personal loan readiness,
    and returns the top N ranked prospects with scores and key signals.
    Input: limit (default 20)
    """
    try:
        with get_db_context() as db:
            customers = customer_repo.get_all_customers(db, skip=0, limit=500)
            customer_ids = [c.customer_id for c in customers]
 
        scored: list[ProspectScore] = []
        for cid in customer_ids:
            try:
                scored.append(_score_customer(cid))
            except Exception as err:
                logger.warning(f"Skipping {cid} during ranking: {err}")

        scored.sort(key=lambda x: x.readiness_score, reverse=True)
        top = scored[:limit]

        lines = [
            f"### 🎯 Top Ranked Personal Loan Prospects (Showing {len(top)})",
            "",
            "| # | Customer ID | Name | Readiness Score | Intent Band | Primary Behavioral Signal |",
            "|---|:---|:---|:---:|:---:|:---|",
        ]
        for i, s in enumerate(top, 1):
            key_signal = s.positive_signals[0] if s.positive_signals else "—"
            band_emoji = "🔥 HIGH" if s.conversion_band == "high" else ("⚡ MEDIUM" if s.conversion_band == "medium" else "🔵 LOW")
            lines.append(
                f"| **{i}** | `{s.customer_id}` | **{s.full_name}** | **{s.readiness_score}/100** | {band_emoji} | {key_signal} |"
            )

        high = sum(1 for s in scored if s.conversion_band == "high")
        medium = sum(1 for s in scored if s.conversion_band == "medium")
        low = sum(1 for s in scored if s.conversion_band == "low")

        lines += [
            "",
            f"> 📊 **Portfolio Summary**: 🔥 High Intent: **{high}** | ⚡ Medium Intent: **{medium}** | 🔵 Low Intent: **{low}** | Total scored: **{len(scored)}**",
        ]
        logger.info(
            f"rank_personal_loan_prospects: scored {len(scored)} customers, showing top {len(top)}"
        )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"rank_personal_loan_prospects error: {e}")
        return f"Error ranking prospects: {str(e)}"


@tool("get_prospect_explanation")
def get_prospect_explanation(customer_id: str) -> str:
    """
    Returns a detailed, human-readable explanation of why a customer
    is (or isn't) a strong personal loan prospect.
    Input: customer_id
    """
    try:
        score = _score_customer(customer_id)
        strength_word = (
            "STRONG 🔥"
            if score.conversion_band == "high"
            else ("MODERATE ⚡" if score.conversion_band == "medium" else "WEAK 🔵")
        )
        band_emoji = "🔥 **HIGH**" if score.conversion_band == "high" else ("⚡ **MEDIUM**" if score.conversion_band == "medium" else "🔵 **LOW**")
        
        pos_list = "\n".join(f"- ✅ {s}" for s in score.positive_signals) if score.positive_signals else "- *(No positive signals detected)*"
        risk_list = "\n".join(f"- ⚠️ {f}" for f in score.risk_flags) if score.risk_flags else "- ✅ *No significant risk factors*"
        fit_list = "\n".join(f"- 📊 {f}" for f in score.loan_fit_factors) if score.loan_fit_factors else "- *(No strong product-fit factors identified)*"
        
        breakdown_rows = "\n".join(f"| {k} | **{v}** |" for k, v in score.score_breakdown.items())

        lines = [
            f"### 💡 Prospect Intelligence Explanation: **{score.full_name}** (`{score.customer_id}`)",
            "",
            f"This profile demonstrates a **{strength_word}** propensity for a personal loan.",
            "",
            "| Dimension | Metric Value |",
            "|:---|:---|",
            f"| **Overall Score** | **{score.readiness_score}/100** |",
            f"| **Conversion Band** | {band_emoji} |",
            f"| **Confidence Level** | **{score.confidence * 100:.0f}%** |",
            "",
            "#### 🚀 Key Positive Drivers",
            pos_list,
            "",
            "#### ⚠️ Risk & Blocker Flags",
            risk_list,
            "",
            "#### 📈 Product Fit Factors",
            fit_list,
            "",
            "#### 📋 Recommendation & Next Steps",
            f"> 💡 **Recommendation:** {score.recommendation_reason}",
            "> ",
            f"> ⚡ **Next Best Action:** {score.next_best_action}",
            "",
            "#### ⚙️ Score Breakdown",
            "| Diagnostic Dimension | Score Contribution |",
            "|:---|:---:|",
            breakdown_rows,
        ]
        logger.info(
            f"get_prospect_explanation: {customer_id} → {score.readiness_score}/100 ({score.conversion_band})"
        )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_prospect_explanation error: {e}")
        return f"Error generating explanation for {customer_id}: {str(e)}"
