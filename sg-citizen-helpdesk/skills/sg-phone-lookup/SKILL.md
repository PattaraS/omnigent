---
name: sg-phone-lookup
description: Normalize and validate a Singapore phone number to canonical E.164 form and classify its type. Use whenever the user provides a phone number in any format.
---

# sg-phone-lookup — normalize & validate Singapore numbers

Turn any Singapore phone number the user gives you into a single canonical form
with a clear validity verdict, using the `phone_normalize` tool as the source
of truth. Never hand-normalize the number yourself.

## Procedure
1. Call `phone_normalize` once with the user's raw string exactly as given.
2. Report, in one or two short lines:
   - the canonical E.164 form (`+65XXXXXXXX`),
   - whether it is valid,
   - its type (mobile / landline / voip / unknown), and
   - if invalid, the one-line reason.
3. Do not invent a number, area code, or type the tool did not return.

## Singapore numbering rules (context, the tool enforces these)
- Country code is `+65`; the national number is 8 digits.
- First digit determines type: `8` or `9` = mobile, `6` = landline,
  `3` = VoIP. Anything else is unknown/invalid.
- Strip spaces, hyphens, parentheses, and a leading `+65`/`65`/`0` before
  validating length.
- A number that is not exactly 8 national digits is invalid — report it as
  such rather than guessing.
