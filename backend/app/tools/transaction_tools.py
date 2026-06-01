from app.db.database import get_db_context
from app.db.repositories import transaction_repo
from app.utils.helpers import fmt_inr
from app.utils.logger import get_logger
from crewai.tools import tool

logger = get_logger(__name__)

# Categories mapped to human-readable life-event labels.
_LIFE_EVENT_MAP: dict[str, str] = {
    "medical": "Medical / Healthcare",
    "healthcare": "Medical / Healthcare",
    "hospital": "Medical / Healthcare",
    "home_renovation": "Home Renovation",
    "renovation": "Home Renovation",
    "home improvement": "Home Renovation",
    "home": "Home Renovation",
    "education": "Education",
    "school": "Education",
    "college": "Education",
    "tuition": "Education",
    "wedding": "Wedding / Marriage",
    "marriage": "Wedding / Marriage",
    "travel": "Travel / Vacation",
    "holiday": "Travel / Vacation",
    "vacation": "Travel / Vacation",
    "vehicle": "Vehicle Purchase",
    "automobile": "Vehicle Purchase",
    "car": "Vehicle Purchase",
}


@tool("fetch_transaction_summary")
def fetch_transaction_summary(customer_id: str, days: int = 90) -> str:
    """
    Summarizes transaction patterns for a customer over the past N days.
    Returns income/expense totals, top spending categories, and recent large transactions.
    Input: customer_id, days (default 90)
    """
    try:
        with get_db_context() as db:
            summary = transaction_repo.get_transaction_summary(
                db, customer_id, days=days
            )

        # summary is a plain dict — safe to use outside the session
        by_cat = summary.get("by_category", {})
        top_cats = sorted(by_cat.items(), key=lambda x: x[1]["total"], reverse=True)[:6]
        large_txns = summary.get("large_txns", [])[:5]

        net = summary["total_credit"] - summary["total_debit"]
        net_label = f"+{fmt_inr(net)}" if net >= 0 else fmt_inr(net)

        lines = [
            f"### 📊 Transaction Summary: `{customer_id}` (last {days} days)",
            "",
            "| Cashflow Parameter | Amount / Indicator |",
            "|:---|:---|",
            f"| **Total Credits (Inflows)** | **{fmt_inr(summary['total_credit'])}** |",
            f"| **Total Debits (Outflows)** | **{fmt_inr(summary['total_debit'])}** |",
            f"| **Net Cashflow Balance** | **{net_label}** |",
            f"| **Consistent Salary Months** | `{summary['salary_months']}` salary credits detected |",
            "",
            "#### 📂 Top Spending Categories",
            "| Spending Category | Total Value | Transactions Count |",
            "|:---|:---:|:---:|",
        ]
        for cat, data in top_cats:
            lines.append(
                f"| {cat.replace('_', ' ').title()} | **{fmt_inr(data['total'])}** | {data['count']} |"
            )

        if large_txns:
            lines += [
                "",
                "#### 🚨 Large Transactions (> ₹50,000)",
                "| Date | Type | Category | Amount | Merchant / Description |",
                "|---|---|---|:---:|:---|",
            ]
            for t in large_txns:
                merchant = t.get("merchant_name") or t.get("description") or "N/A"
                lines.append(
                    f"| {t['txn_date']} | `{t['txn_type'].upper()}` | {t['category'].replace('_', ' ').title()} | **{fmt_inr(t['amount'])}** | {merchant} |"
                )

        logger.info(f"fetch_transaction_summary called for {customer_id}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"fetch_transaction_summary error: {e}")
        return f"Error fetching transactions for {customer_id}: {str(e)}"


@tool("detect_life_event_spends")
def detect_life_event_spends(customer_id: str) -> str:
    """
    Detects significant life-event spending signals: medical, home renovation,
    education, wedding, and travel. These are strong personal loan intent signals.
    Input: customer_id
    """
    try:
        with get_db_context() as db:
            txns = transaction_repo.get_transactions_by_customer(
                db, customer_id, days=180
            )
            # Process ORM objects inside the session while they are live
            detected: dict[str, float] = {}
            txn_count = 0
            for txn in txns:
                if txn.txn_type != "debit":
                    continue
                txn_count += 1
                cat_lower = (txn.category or "").lower()
                for keyword, display_name in _LIFE_EVENT_MAP.items():
                    if keyword in cat_lower:
                        detected[display_name] = (
                            detected.get(display_name, 0.0) + txn.amount
                        )
                        break

        if not detected:
            return (
                f"### 🔔 Life Event Signals: `{customer_id}`\n\n"
                f"Scanned `{txn_count}` debit transactions over the past 180 days. "
                "No significant life-event spending detected. "
                "Monitor for future spends in medical, education, travel, or home categories."
            )

        lines = [
            f"### 🔔 Life Event Spending Signals: `{customer_id}`",
            "",
            f"Detected **{len(detected)}** active life-event categories over 180 days — indicating strong personal loan intent.",
            "",
            "| Life Event Category | Total Spend | Intent Strength |",
            "|:---|:---:|:---:|",
        ]
        for event, total in sorted(detected.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {event} | **{fmt_inr(total)}** | 🔥 **Strong** |")

        lines += [
            "",
            "> ⚡ **Strategic Recommendation:** Prioritize this customer for personalized high-intent outreach."
        ]
        logger.info(
            f"detect_life_event_spends: found {len(detected)} signals for {customer_id}"
        )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"detect_life_event_spends error: {e}")
        return f"Error detecting life events for {customer_id}: {str(e)}"


@tool("calculate_cashflow_trend")
def calculate_cashflow_trend(customer_id: str) -> str:
    """
    Calculates month-over-month cashflow trend over last 6 months.
    Shows if spending is rising (loan intent signal).
    Input: customer_id
    """
    try:
        with get_db_context() as db:
            txns = transaction_repo.get_transactions_by_customer(
                db, customer_id, days=180
            )
            # Aggregate per month inside the session
            monthly: dict[str, dict[str, float]] = {}
            for txn in txns:
                key = txn.txn_date.strftime("%Y-%m")
                if key not in monthly:
                    monthly[key] = {"credit": 0.0, "debit": 0.0}
                if txn.txn_type == "credit":
                    monthly[key]["credit"] += txn.amount
                else:
                    monthly[key]["debit"] += txn.amount

        if not monthly:
            return (
                f"### 📈 Cashflow Trend: `{customer_id}`\n\n"
                "No transaction data available for the last 6 months."
            )

        sorted_months = sorted(monthly.keys())

        lines = [
            f"### 📈 Cashflow Trend Summary: `{customer_id}` (last 6 months)",
            "",
            "| Month | Inflow (Credits) | Outflow (Debits) | Net Cashflow | Monthly Trend |",
            "|---|:---:|:---:|:---:|:---:|",
        ]
        prev_net: float | None = None
        for month in sorted_months:
            data = monthly[month]
            net = data["credit"] - data["debit"]
            if prev_net is not None:
                if net > prev_net * 1.05:
                    trend = "📈 Rising"
                elif net < prev_net * 0.95:
                    trend = "📉 Falling"
                else:
                    trend = "➡️ Stable"
            else:
                trend = "—"
            lines.append(
                f"| `{month}` | {fmt_inr(data['credit'])} | "
                f"{fmt_inr(data['debit'])} | **{fmt_inr(net)}** | {trend} |"
            )
            prev_net = net

        # Compute spend growth: last half vs first half
        if len(sorted_months) >= 2:
            mid = len(sorted_months) // 2
            first_half_debits = [monthly[m]["debit"] for m in sorted_months[:mid]]
            second_half_debits = [monthly[m]["debit"] for m in sorted_months[mid:]]
            avg_first = sum(first_half_debits) / max(1, len(first_half_debits))
            avg_second = sum(second_half_debits) / max(1, len(second_half_debits))
            spend_growth = (
                ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0.0
            )

            if spend_growth > 15:
                assessment = "⚡ **Strongly rising spends** (High-intent loan trigger)"
            elif spend_growth > 5:
                assessment = "ℹ️ **Moderate spend increase** (Worth monitoring)"
            else:
                assessment = "✅ **Stable or declining spends** (Lower urgency)"

            lines += [
                "",
                "#### 📊 Trend Diagnostic Indicators",
                "| Trend Assessment Parameter | Diagnostic Value |",
                "|:---|:---|",
                f"| **Average Spend (First Half)** | {fmt_inr(avg_first)} |",
                f"| **Average Spend (Second Half)** | {fmt_inr(avg_second)} |",
                f"| **Spend Growth (Recent vs Prior)** | **{spend_growth:+.1f}%** |",
                f"| **Spends Assessment** | {assessment} |",
            ]

        logger.info(f"calculate_cashflow_trend called for {customer_id}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"calculate_cashflow_trend error: {e}")
        return f"Error calculating cashflow trend for {customer_id}: {str(e)}"


@tool("find_high_value_spending_customers")
def find_high_value_spending_customers(category: str = None, min_amount: float = 100000.0, days: int = 180) -> str:
    """
    Scans the entire database across all customers to find those with debit transactions
    exceeding min_amount (default 100,000) within the past N days.
    Input parameters:
      - category: filter by transaction category (e.g. 'medical', 'education', 'wedding', 'renovation', 'travel') or None to scan all.
      - min_amount: minimum transaction value (e.g. 100000.0)
      - days: number of historical days to scan (default 180)
    """
    try:
        from app.db.models import Transaction, Customer
        from datetime import date, timedelta
        
        cutoff = date.today() - timedelta(days=days)
        with get_db_context() as db:
            query = db.query(Transaction).filter(
                Transaction.txn_type == "debit",
                Transaction.amount >= min_amount,
                Transaction.txn_date >= cutoff
            )
            
            if category:
                cat_lower = category.lower()
                query = query.filter(Transaction.category.ilike(f"%{cat_lower}%"))
                
            txns = query.all()
            
            # Group by customer to aggregate spends
            customer_spends = {}
            for t in txns:
                cust = db.query(Customer).filter(Customer.customer_id == t.customer_id).first()
                cust_name = cust.full_name if cust else "Unknown"
                
                if t.customer_id not in customer_spends:
                    customer_spends[t.customer_id] = {
                        "name": cust_name,
                        "total_amount": 0.0,
                        "transactions": []
                    }
                customer_spends[t.customer_id]["total_amount"] += t.amount
                customer_spends[t.customer_id]["transactions"].append({
                    "amount": t.amount,
                    "category": t.category
                })
                
        if not customer_spends:
            return (
                f"### 🔍 Broad Spending Scan\n\n"
                f"Scanned all customer transactions for debits over the past {days} days.\n"
                f"- Category filter: `{category or 'ALL'}`\n"
                f"- Minimum threshold: **{fmt_inr(min_amount)}**\n\n"
                f"❌ **No customers matched these criteria.**"
            )
            
        lines = [
            f"### 🔍 Broad Spending Scan Results (Past {days} days)",
            f"Found **{len(customer_spends)}** customers matching criteria: debits ≥ **{fmt_inr(min_amount)}** in `{category or 'ALL'}` categories.",
            "",
            "| # | Customer ID | Name | Matching Spend Amount | Top Signal Category | Transaction Count |",
            "|---|:---|:---|:---:|:---|:---:|",
        ]
        
        for idx, (cid, data) in enumerate(sorted(customer_spends.items(), key=lambda x: x[1]["total_amount"], reverse=True), 1):
            top_cat = data["transactions"][0]["category"].replace("_", " ").title() if data["transactions"] else "General"
            lines.append(
                f"| **{idx}** | `{cid}` | **{data['name']}** | **{fmt_inr(data['total_amount'])}** | `{top_cat}` | {len(data['transactions'])} |"
            )
            
        lines += [
            "",
            "> 💡 **Actionable Recommendation:** Click the customer names to view their full live dossiers or execute campaign outreach."
        ]
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"find_high_value_spending_customers error: {e}")
        return f"Error executing broad scan: {str(e)}"

