"""Offline sanity checks for the SG Citizen Helpdesk demo bundle.

Runs with no provider and no network: it unit-tests the local tools and
confirms the bundle's files are present and the YAML parses. Run before the
demo:

    python3 validate.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).parent


def _load_tool(name: str):
    """Load a tools/python/<name>.py module, stubbing the @tool decorator."""
    # The tool modules import `from omnigent_client import tool`; offline we
    # only need the decorator to be an identity function.
    if "omnigent_client" not in sys.modules:
        stub = types.ModuleType("omnigent_client")
        stub.tool = lambda fn: fn  # type: ignore[attr-defined]
        sys.modules["omnigent_client"] = stub

    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "python" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _check_phone() -> bool:
    p = _load_tool("phone_normalize")
    cases = [
        ("9123 4567", "+6591234567", True, "mobile"),
        ("(+65) 8123-4567", "+6581234567", True, "mobile"),
        ("+65 6 234 5678", "+6562345678", True, "landline"),
        ("3123 4567", "+6531234567", True, "voip"),
        ("091234567", "+6591234567", True, "mobile"),
        ("71234567", None, False, "unknown"),
        ("1234", None, False, "unknown"),
        # Explicit "+" must be Singapore's +65: a foreign country code is
        # rejected, not reinterpreted as a bare SG national number.
        ("+66829999", None, False, "unknown"),
        ("+6591234567", "+6591234567", True, "mobile"),
    ]
    ok = True
    for raw, e164, valid, typ in cases:
        got = p.phone_normalize(raw)
        if (got["e164"], got["valid"], got["type"]) != (e164, valid, typ):
            print(f"FAIL phone: {raw!r} -> {got}")
            ok = False
    print(f"phone_normalize: {len(cases)} cases checked")
    return ok


def _check_nric() -> bool:
    n = _load_tool("nric_validate")
    # (raw, expected masked, valid, holder). Check letters computed from the
    # published NRIC/FIN checksum; the raw ids are synthetic test vectors.
    cases = [
        ("S1234567D", "*****567D", True, "citizen_or_pr"),
        ("T1234567J", "*****567J", True, "citizen_or_pr"),
        ("F1234567N", "*****567N", True, "foreigner"),
        ("G1234567X", "*****567X", True, "foreigner"),
        ("s1234567d", "*****567D", True, "citizen_or_pr"),  # case-insensitive
        ("S1234567A", "*****567A", False, "citizen_or_pr"),  # wrong check letter
        ("S12345", None, False, "unknown"),  # too short
        ("X1234567D", None, False, "unknown"),  # bad prefix
    ]
    ok = True
    for raw, masked, valid, holder in cases:
        got = n.nric_validate(raw)
        if (got["masked"], got["valid"], got["holder"]) != (masked, valid, holder):
            print(f"FAIL nric: {raw!r} -> {got}")
            ok = False
        # A full id must never leak: the raw digits must not appear verbatim.
        if got["masked"] and raw.upper().replace(" ", "") in str(got):
            print(f"FAIL nric leaked full id: {raw!r} -> {got}")
            ok = False
    print(f"nric_validate: {len(cases)} cases checked")
    return ok


def _check_postal() -> bool:
    p = _load_tool("postal_lookup")
    # (raw, valid, district, region).
    cases = [
        ("018989", True, 1, "Central"),
        ("01 8989", True, 1, "Central"),  # spacing stripped
        ("520123", True, 18, "East"),  # sector 52 -> Tampines / Pasir Ris
        ("640001", True, 22, "West"),  # sector 64 -> Jurong
        ("750123", True, 27, "North"),  # sector 75 -> Yishun / Sembawang
        ("828999", True, 19, "North-East"),  # sector 82 -> Punggol
        ("998877", True, None, None),  # sector 99 unassigned
        ("12345", False, None, None),  # not 6 digits
    ]
    ok = True
    for raw, valid, district, region in cases:
        got = p.postal_lookup(raw)
        if (got["valid"], got["district"], got["region"]) != (valid, district, region):
            print(f"FAIL postal: {raw!r} -> {got}")
            ok = False
    print(f"postal_lookup: {len(cases)} cases checked")
    return ok


def _check_triage() -> bool:
    c = _load_tool("case_triage")
    # (text, category, queue, priority).
    cases = [
        ("My HDB rental flat lease query", "housing", "HDB Branch", "normal"),
        ("How do I pay income tax?", "tax", "IRAS e-Services", "normal"),
        ("renew my passport at ICA", "immigration", "ICA Counter", "normal"),
        ("CDC voucher help", "cdc", "CDC Vouchers", "normal"),
        ("road tax and COE question", "transport", "LTA Feedback", "normal"),
        ("just saying hi", "general", "General Enquiries", "normal"),
        # Urgency keyword bumps priority regardless of category.
        ("income tax deadline is today, urgent", "tax", "IRAS e-Services", "high"),
    ]
    ok = True
    for text, category, queue, priority in cases:
        got = c.case_triage(text)
        if (got["category"], got["queue"], got["priority"]) != (category, queue, priority):
            print(f"FAIL triage: {text!r} -> {got}")
            ok = False
    print(f"case_triage: {len(cases)} cases checked")
    return ok


def main() -> int:
    ok = True

    # 1. Tool logic.
    ok &= _check_phone()
    ok &= _check_nric()
    ok &= _check_postal()
    ok &= _check_triage()

    # 2. Files present.
    required = [
        "config.yaml",
        "skills/citizen-intake/SKILL.md",
        "skills/sg-phone-lookup/SKILL.md",
        "skills/nric-check/SKILL.md",
        "tools/python/phone_normalize.py",
        "tools/python/nric_validate.py",
        "tools/python/postal_lookup.py",
        "tools/python/case_triage.py",
        "agents/reviewer/config.yaml",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            print(f"FAIL missing: {rel}")
            ok = False
    print(f"files: {len(required)} checked")

    # 3. YAML parses (best-effort; skipped if pyyaml absent).
    try:
        import yaml

        for rel in ("config.yaml", "agents/reviewer/config.yaml"):
            yaml.safe_load((ROOT / rel).read_text())
        print("yaml: parsed OK")
    except ImportError:
        print("yaml: pyyaml not installed, skipped (not fatal)")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL yaml parse: {exc}")
        ok = False

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
