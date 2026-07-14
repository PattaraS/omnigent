"""Local Python tool: validate and mask a Singapore NRIC / FIN.

Auto-discovered by Omnigent from tools/python/. The module-level `@tool`
function is registered under its own name, so `nric_validate` here becomes the
tool `nric_validate`. The runtime infers the schema from the type hints and
docstring below.

Pure standard library, no network. This is the offline, in-repo realization of
the "identity directory" capability the slides sketch as an MCP server
(`nric_directory`, `npx @gov/nric-mcp`): a real government deployment would
plug in its own MCP-backed directory, but the demo owns the whole thing so it
runs on a venue network with no egress.

The checksum below is Singapore's published NRIC/FIN algorithm. It only proves
a number is *well-formed* — it never asserts the identity exists or belongs to
the caller. The tool returns a MASKED id (last 4 shown) so a full national id
never has to be echoed back to a citizen or written to a transcript.
"""

from __future__ import annotations

import re

from omnigent_client import tool

# Digit weights applied left-to-right to the 7 numeric digits.
_WEIGHTS = (2, 7, 6, 5, 4, 3, 2)

# Check-letter tables, indexed by (weighted_sum % 11).
_CHECK_LETTERS = {
    # Citizens / PRs: S (born before 2000) and T (2000 onward).
    "ST": "JZIHGFEDCBA",
    # Foreign identification numbers: F and G (long-term pass holders).
    "FG": "XWUTRQPNMLK",
}

# Leading letter -> human-readable holder class.
_PREFIX_CLASS = {
    "S": "citizen_or_pr",  # issued before 2000
    "T": "citizen_or_pr",  # issued 2000 onward
    "F": "foreigner",  # foreign id issued before 2000
    "G": "foreigner",  # foreign id issued 2000 onward
}

_SHAPE = re.compile(r"^[STFG]\d{7}[A-Z]$")


def _mask(nric: str) -> str:
    """Mask all but the last 4 characters, e.g. `S1234567D` -> `*****567D`."""
    return "*" * (len(nric) - 4) + nric[-4:]


@tool
def nric_validate(raw: str) -> dict:
    """Validate a Singapore NRIC/FIN and return a masked, classified result.

    Checks the number against Singapore's published NRIC/FIN checksum. A valid
    number is well-formed only — this never asserts the person exists or that
    the caller owns the id. The returned id is always MASKED (last 4 shown); the
    full id is not echoed back.

    :param raw: The id as the citizen typed it, in any spacing/case
        (e.g. "S1234567D", "s1234567d", "T0123456 A").
    :returns: A dict with:
        - masked: masked id ("*****567D") or None if not derivable,
        - valid: bool (passes the checksum),
        - holder: "citizen_or_pr" | "foreigner" | "unknown",
        - reason: short explanation when invalid, else "".
    """
    cleaned = re.sub(r"[\s-]", "", raw or "").upper()

    if not _SHAPE.match(cleaned):
        return {
            "masked": None,
            "valid": False,
            "holder": "unknown",
            "reason": "Not a well-formed id (expect 1 letter + 7 digits + 1 letter).",
        }

    prefix = cleaned[0]
    digits = cleaned[1:8]
    given_check = cleaned[8]

    weighted = sum(int(digits[i]) * _WEIGHTS[i] for i in range(7))
    if prefix in ("T", "G"):
        weighted += 4  # offset for numbers issued 2000 onward

    table = _CHECK_LETTERS["ST" if prefix in ("S", "T") else "FG"]
    expected_check = table[weighted % 11]

    if given_check != expected_check:
        return {
            "masked": _mask(cleaned),
            "valid": False,
            "holder": _PREFIX_CLASS.get(prefix, "unknown"),
            "reason": "Checksum letter does not match — likely a typo.",
        }

    return {
        "masked": _mask(cleaned),
        "valid": True,
        "holder": _PREFIX_CLASS.get(prefix, "unknown"),
        "reason": "",
    }
