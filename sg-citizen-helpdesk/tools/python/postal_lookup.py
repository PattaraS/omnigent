"""Local Python tool: validate a Singapore postal code and locate its district.

Auto-discovered by Omnigent from tools/python/. The `@tool` function registers
as the tool `postal_lookup`. Schema is inferred from the type hints and
docstring.

Pure standard library, no network. Singapore postal codes are 6 digits; the
first two are the "postal sector", which maps to one of the 28 postal
districts (and a broad region). The sector -> district table below is the
authoritative SingPost / URA mapping, shipped inline so the bundle routes a
citizen case to the right regional office with no live address service. A
production deployment would swap this for the authoritative OneMap / SLA lookup
behind an MCP server; the interface stays the same.
"""

from __future__ import annotations

import re

from omnigent_client import tool

# District number -> (sectors, area name, broad region). Sectors are the
# leading two digits of the 6-digit postal code. This is the full official
# SingPost/URA list of postal districts (D01-D28).
_DISTRICTS = [
    (1, ["01", "02", "03", "04", "05", "06"], "Raffles Place / Marina", "Central"),
    (2, ["07", "08"], "Anson / Tanjong Pagar", "Central"),
    (3, ["14", "15", "16"], "Queenstown / Tiong Bahru", "Central"),
    (4, ["09", "10"], "Telok Blangah / HarbourFront", "Central"),
    (5, ["11", "12", "13"], "Pasir Panjang / Clementi", "West"),
    (6, ["17"], "High Street / Beach Road", "Central"),
    (7, ["18", "19"], "Middle Road / Golden Mile", "Central"),
    (8, ["20", "21"], "Little India", "Central"),
    (9, ["22", "23"], "Orchard / River Valley", "Central"),
    (10, ["24", "25", "26", "27"], "Bukit Timah / Holland / Tanglin", "Central"),
    (11, ["28", "29", "30"], "Novena / Thomson", "Central"),
    (12, ["31", "32", "33"], "Balestier / Toa Payoh", "Central"),
    (13, ["34", "35", "36", "37"], "Macpherson / Braddell", "Central"),
    (14, ["38", "39", "40", "41"], "Geylang / Eunos", "East"),
    (15, ["42", "43", "44", "45"], "Katong / Joo Chiat / Marine Parade", "East"),
    (16, ["46", "47", "48"], "Bedok / Upper East Coast", "East"),
    (17, ["49", "50", "81"], "Loyang / Changi", "East"),
    (18, ["51", "52"], "Tampines / Pasir Ris", "East"),
    (19, ["53", "54", "55", "82"], "Serangoon Garden / Hougang / Punggol", "North-East"),
    (20, ["56", "57"], "Bishan / Ang Mo Kio", "Central"),
    (21, ["58", "59"], "Upper Bukit Timah / Ulu Pandan", "West"),
    (22, ["60", "61", "62", "63", "64"], "Jurong", "West"),
    (23, ["65", "66", "67", "68"], "Bukit Panjang / Choa Chu Kang", "West"),
    (24, ["69", "70", "71"], "Lim Chu Kang / Tengah", "West"),
    (25, ["72", "73"], "Kranji / Woodlands", "North"),
    (26, ["77", "78"], "Upper Thomson / Springleaf", "North"),
    (27, ["75", "76"], "Yishun / Sembawang", "North"),
    (28, ["79", "80"], "Seletar", "North-East"),
]

# Flatten to sector -> (district, area, region) for O(1) lookup.
_SECTOR_TO_DISTRICT = {
    sector: (district, area, region)
    for district, sectors, area, region in _DISTRICTS
    for sector in sectors
}


@tool
def postal_lookup(raw: str) -> dict:
    """Validate a Singapore 6-digit postal code and locate its district.

    Strips spacing, checks the code is exactly 6 digits, and maps the leading
    two-digit postal sector to a district, area, and region for case routing.
    Purely offline — no live address service is contacted.

    :param raw: The postal code as the citizen typed it (e.g. "018989",
        "01 8989", "S018989").
    :returns: A dict with:
        - postal: the 6-digit code (or None if not derivable),
        - valid: bool,
        - district: district number 1-28 (or None if the sector is unassigned),
        - area: area name (or None),
        - region: "Central" | "East" | "West" | "North" | "North-East"
          (or None),
        - reason: short explanation when invalid or unknown, else "".
    """
    digits = re.sub(r"[^\d]", "", raw or "")

    if len(digits) != 6:
        return {
            "postal": None,
            "valid": False,
            "district": None,
            "area": None,
            "region": None,
            "reason": f"Expected 6 digits, got {len(digits)}.",
        }

    sector = digits[:2]
    match = _SECTOR_TO_DISTRICT.get(sector)
    if match is None:
        return {
            "postal": digits,
            "valid": True,
            "district": None,
            "area": None,
            "region": None,
            "reason": f"Sector {sector} is not an assigned Singapore postal sector.",
        }

    district, area, region = match
    return {
        "postal": digits,
        "valid": True,
        "district": district,
        "area": area,
        "region": region,
        "reason": "",
    }
