---
name: citizen-intake
description: Handle a citizen helpdesk request end to end — validate any details provided (phone, NRIC/FIN, postal code), triage the request to the right agency queue, and summarize next steps. Use whenever a citizen describes a problem or asks for help.
---

# citizen-intake — handle a citizen request end to end

Turn a citizen's message into a clear, actionable helpdesk outcome: validate
whatever details they gave, route the request, and tell them what happens next.
Use the tools as the source of truth; never hand-derive a verdict yourself.

## Procedure
1. Extract any structured details from the message and validate each with its
   tool, calling each tool once:
   - a phone number -> `phone_normalize`
   - an NRIC / FIN -> `nric_validate`
   - a 6-digit postal code -> `postal_lookup`
   Skip a tool if that detail is absent — do not invent an input to feed it.
2. Triage the request itself with `case_triage` on the citizen's own words to
   get the agency `queue` and `priority`.
3. Reply in a few short lines:
   - the queue the case is routed to and its priority,
   - one line per validated detail (canonical form + verdict), and
   - the single next step the citizen should take.
4. Handle invalid details plainly: state what was wrong (from the tool's
   `reason`) and ask for a correction rather than guessing.

## Handling identity numbers (NRIC / FIN)
- Report only the MASKED id that `nric_validate` returns (e.g. `*****567D`).
  Never repeat the full NRIC/FIN back to the citizen or write it into your
  summary — the masked form is the source of truth for the reply.
- A valid checksum means the number is well-formed only. Never state or imply
  that it confirms the person's identity or that the record exists.

## Notes
- Keep answers factual and brief; a citizen wants the outcome, not the method.
- If correctness matters (an eligibility or identity call), route the final
  answer plus the raw inputs through the `reviewer` sub-agent for an
  independent, different-vendor cross-check before finalizing.
