"""Local Python tool: normalize and validate Singapore phone numbers.

Auto-discovered by Omnigent from tools/python/. Each module-level function
decorated with `@tool` is registered; the tool name is the function name, so
`phone_normalize` here becomes the tool `phone_normalize`. The runtime infers
the tool schema from the type hints and docstring below.

Pure standard library, no network — safe to run anywhere and on a venue
network with no egress.
"""

from __future__ import annotations

import re

from omnigent_client import tool


@tool
def phone_normalize(raw: str) -> dict:
    """Normalize a Singapore phone number to canonical E.164 form.

    An explicit international prefix ("+") must be Singapore's "+65"; a
    foreign country code (e.g. "+66") is rejected rather than reinterpreted.
    Bare local forms drop an optional "65" country code or a leading "0"
    trunk prefix. The remaining national number must be exactly 8 digits and
    is classified by its leading digit.

    :param raw: The phone number as the user typed it, in any format
        (e.g. "9123 4567", "(+65) 8123-4567", "+65 6 234 5678").
    :returns: A dict with:
        - e164: canonical "+65XXXXXXXX" (or None if not derivable),
        - valid: bool,
        - type: "mobile" | "landline" | "voip" | "unknown",
        - reason: short explanation when invalid, else "".
    """
    raw_str = raw or ""
    has_plus = "+" in raw_str
    digits = re.sub(r"[^\d]", "", raw_str)

    if has_plus:
        # An explicit "+" is an E.164 country code — it must be Singapore's.
        if not digits.startswith("65"):
            return {
                "e164": None,
                "valid": False,
                "type": "unknown",
                "reason": "Country code is not Singapore (+65); this is not an SG number.",
            }
        digits = digits[2:]
    elif digits.startswith("65") and len(digits) == 10:
        # Bare "65…" (no "+") is an optional country code only at full length.
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 9:
        digits = digits[1:]

    if len(digits) != 8:
        return {
            "e164": None,
            "valid": False,
            "type": "unknown",
            "reason": f"Expected 8 national digits, got {len(digits)}.",
        }

    lead = digits[0]
    number_type = {
        "8": "mobile",
        "9": "mobile",
        "6": "landline",
        "3": "voip",
    }.get(lead, "unknown")

    if number_type == "unknown":
        return {
            "e164": None,
            "valid": False,
            "type": "unknown",
            "reason": f"Leading digit {lead} is not a valid SG prefix (expect 8/9/6/3).",
        }

    return {
        "e164": f"+65{digits}",
        "valid": True,
        "type": number_type,
        "reason": "",
    }
