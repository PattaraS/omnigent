"""Local Python tool: triage a citizen request to the right agency and queue.

Auto-discovered by Omnigent from tools/python/. The `@tool` function registers
as the tool `case_triage`. Schema is inferred from the type hints and
docstring.

Pure standard library, no network. This is deliberately a transparent,
rules-based classifier, not a model call: on a government screen the routing
logic must be inspectable and reproducible. The keyword tables below decide
which agency queue a request belongs to and how urgent it is. A real
deployment would tune these tables (or back them with a case-management
system); the tool contract stays the same.
"""

from __future__ import annotations

from omnigent_client import tool

# Agency queue -> trigger keywords. First matching category (in this order)
# wins, so put the most specific / highest-consequence categories first.
_CATEGORY_KEYWORDS = [
    (
        "housing",  # HDB
        "HDB Branch",
        ["hdb", "bto", "flat", "rental flat", "lease", "resale", "town council"],
    ),
    (
        "transport",  # LTA — checked before tax so "road tax" routes here, not to IRAS
        "LTA Feedback",
        ["lta", "coe", "road tax", "season parking", "erp", "bus", "mrt"],
    ),
    (
        "tax",  # IRAS
        "IRAS e-Services",
        ["income tax", "property tax", "stamp duty", "gst", "iras", "tax"],
    ),
    (
        "immigration",  # ICA
        "ICA Counter",
        ["passport", "ica", "re-entry", "long-term pass", "citizenship", "nric"],
    ),
    (
        "health",  # MOH / HPB
        "MOH Careline",
        ["chas", "medisave", "healthier sg", "subsidy", "polyclinic", "vaccination"],
    ),
    (
        "cdc",  # community
        "CDC Vouchers",
        ["cdc", "voucher", "community", "assistance scheme", "comcare"],
    ),
]

# Urgency keywords bump priority regardless of category.
_URGENT_KEYWORDS = [
    "urgent",
    "emergency",
    "deadline",
    "today",
    "cannot log in",
    "locked out",
    "overdue",
    "penalty",
    "expired",
    "expiring",
]


@tool
def case_triage(text: str) -> dict:
    """Classify a citizen request into an agency queue with a priority.

    Runs a transparent keyword match over the request text: the first matching
    category decides the agency and queue, and any urgency keyword raises the
    priority. Deterministic and inspectable — no model call.

    :param text: The citizen's free-text request or question.
    :returns: A dict with:
        - category: "housing" | "tax" | "immigration" | "transport"
          | "health" | "cdc" | "general",
        - queue: the destination queue name,
        - priority: "high" | "normal",
        - matched: the keywords that drove the decision (for the audit trail).
    """
    lowered = (text or "").lower()

    category = "general"
    queue = "General Enquiries"
    matched: list[str] = []

    for cat, cat_queue, keywords in _CATEGORY_KEYWORDS:
        hits = [kw for kw in keywords if kw in lowered]
        if hits:
            category = cat
            queue = cat_queue
            matched = hits
            break

    urgent_hits = [kw for kw in _URGENT_KEYWORDS if kw in lowered]
    priority = "high" if urgent_hits else "normal"
    matched = matched + urgent_hits

    return {
        "category": category,
        "queue": queue,
        "priority": priority,
        "matched": matched,
    }
