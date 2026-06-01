import json
from datetime import date, datetime


def fmt_inr(amount: float) -> str:
    """Format as Indian currency: ₹1,25,000"""
    if amount is None:
        return "₹0"
    amount_int = int(round(float(amount)))
    negative = amount_int < 0
    s = str(abs(amount_int))

    if len(s) <= 3:
        formatted = s
    else:
        # Rightmost 3 digits form the first group
        last3 = s[-3:]
        rest = s[:-3]
        # Remaining digits are split into groups of 2 from the right;
        # the leftmost group may be 1 or 2 digits.
        groups: list[str] = []
        while rest:
            groups.append(rest[-2:] if len(rest) >= 2 else rest[-1:])
            rest = rest[:-2] if len(rest) > 2 else ""
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    return ("-₹" if negative else "₹") + formatted


def days_ago(d: date) -> int:
    """Return the number of days between *d* and today."""
    today = date.today()
    if isinstance(d, datetime):
        d = d.date()
    return (today - d).days


def safe_json(obj) -> str:
    """JSON-serialize *obj*, converting date/datetime values to ISO strings."""

    def _default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, default=_default)


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate *text* to *max_len* characters, appending '...' if shortened."""
    if not text or len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def compute_months_between(start: date, end: date) -> int:
    """Return the whole number of months between two dates."""
    return (end.year - start.year) * 12 + (end.month - start.month)


def mask_phone(phone: str) -> str:
    """Mask a phone number: 98XXXXX901 (first 2 + Xs for middle + last 3)."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 4:
        return "X" * len(digits)
    if len(digits) >= 10:
        return digits[:2] + "X" * (len(digits) - 5) + digits[-3:]
    return digits[:1] + "X" * (len(digits) - 2) + digits[-1:]


def mask_email(email: str) -> str:
    """Mask an email address: a***@gmail.com"""
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    prefix = local[0] if local else ""
    return f"{prefix}***@{domain}"
