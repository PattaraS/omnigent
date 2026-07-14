---
name: nric-check
description: Validate a Singapore NRIC or FIN against the official checksum and report a masked, classified result. Use whenever a citizen provides an NRIC/FIN.
---

# nric-check — validate & mask a Singapore NRIC/FIN

Confirm whether an NRIC/FIN is well-formed, using the `nric_validate` tool as
the source of truth, and report it without ever exposing the full id.

## Procedure
1. Call `nric_validate` once with the id exactly as the citizen typed it.
2. Report, in one or two short lines:
   - the MASKED id the tool returned (e.g. `*****567D`) — never the full id,
   - whether it is valid (passes the checksum),
   - the holder class (citizen/PR vs foreigner), and
   - if invalid, the one-line reason.
3. Do not guess a check letter, reconstruct the full number, or classify a
   number the tool marked invalid.

## What "valid" means (say this if asked)
- A valid checksum proves the number is *well-formed* only — the digits and
  check letter are internally consistent.
- It does NOT confirm the person exists, that the id is theirs, or that any
  record is attached. Never imply identity verification from this check.

## Singapore NRIC/FIN rules (context; the tool enforces these)
- Shape: one prefix letter, 7 digits, one check letter.
- Prefix: `S`/`T` = citizen or PR (T = issued 2000 onward); `F`/`G` = foreigner
  (G = issued 2000 onward).
- The final letter is a checksum over the 7 digits; a mismatch means a typo.
- Always surface the masked id, never the raw one.
