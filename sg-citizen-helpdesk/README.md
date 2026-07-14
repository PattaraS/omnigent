# SG Citizen Helpdesk — GovTech demo bundle

A self-contained Omnigent agent image for the Singapore GovTech demo. It plays
a realistic front-line citizen helpdesk — validate the details a citizen gives
you, route their request to the right agency, keep identity numbers masked — and
makes the "compose an agent" story concrete on one screen:

- **Harness** — the brain runs on `claude-sdk`; swap the harness to change
  vendor, nothing else.
- **Skills** — Markdown playbooks your team authors (no code):
  `citizen-intake` (handle a request end to end), `sg-phone-lookup`,
  `nric-check`.
- **Tools** — local Python functions under `tools/python/`, auto-discovered
  (each `@tool` function becomes a tool named after the function):
  - `phone_normalize` — canonicalize + validate a Singapore phone number.
  - `nric_validate` — validate an NRIC/FIN checksum; returns a **masked** id.
  - `postal_lookup` — validate a 6-digit postal code; locate its district.
  - `case_triage` — route a request to an agency queue with a priority.
- **Policies** — centrally-authored governance (`guardrails.policies`),
  enforced on every session:
  - `blast_radius` — the shipped catastrophic-command guard.
  - `gate_outbound_email` — outbound email becomes a human approval (ASK).
  - `mask_pii_in_prompts` — a national-id-style / card / SSN pattern in the
    request itself triggers an ASK (defense in depth; the phone category is
    intentionally off — accepting phone numbers is this helpdesk's job).
- **Sub-agent** — an independent `reviewer` on a *different* vendor (codex) for
  cross-vendor verification.

## What this bundle demonstrates

"Define once, applies everywhere": each policy is authored in one place and
enforced on every tool call and request the agent makes. Skills and tools are
not magic — each traces back to a file your team wrote (a `SKILL.md` or a
`.py`). And the answer can be cross-checked by a *different vendor*: swap the
`reviewer`'s harness to change who checks the work.

The scenario is deliberately concrete: a citizen writes in, the agent validates
their phone / NRIC / postal code with owned tools, triages the request to the
right queue, and replies with the identity number masked — the everyday shape
of a government service desk.

## Prerequisites

- Omnigent installed (`omni --version`).
- Python 3.12+.
- One Claude provider for the brain + local tools:
  `omnigent setup` (or `export ANTHROPIC_API_KEY=...`).
- (Optional) An OpenAI provider so the codex `reviewer` sub-agent can boot:
  `export OPENAI_API_KEY=...`.

## Run it

```
# from the directory that CONTAINS sg-citizen-helpdesk/
omnigent run sg-citizen-helpdesk \
  --prompt "Normalize and validate this SG number: (+65) 8123-4567"
```

Expected: `(+65) 8123-4567` -> `+6581234567`, valid, mobile. Try the other
lines in `sample_inputs.txt` — phone numbers, NRIC/FIN, postal codes, and whole
citizen requests that exercise triage and the `citizen-intake` skill.

## Verify before the demo

```
# 1. Unit-test all four tools offline (no provider needed):
python3 validate.py

# 2. Confirm the bundle parses / loads in YOUR deployment before you rely on it
#    live. If your CLI exposes a validate/lint subcommand, use it; otherwise a
#    dry `omnigent run ... --prompt "reply OK"` confirms it boots.
```

## Honesty notes (read before it goes on a government screen)

- **Everything is offline and deterministic.** All four tools are pure
  standard-library Python with no network — safe on a venue network with no
  egress. Verdicts are reproducible: the same input always gives the same
  answer, and you can read exactly why in the tool source.
- **The NRIC/FIN check is the published checksum, and nothing more.** "Valid"
  means *well-formed* (the digits and check letter are internally consistent).
  It does NOT confirm the person exists, that the id is theirs, or that any
  record is attached. The tool returns a masked id (last 4) and the skill/prompt
  forbid echoing the full number.
- **The postal table is the real SingPost/URA district mapping** (D01-D28),
  shipped inline. A production deployment would swap it for the authoritative
  OneMap/SLA lookup behind an MCP server; the tool contract stays the same.
- **`case_triage` is a transparent keyword classifier, not a model call** — on
  a government screen the routing must be inspectable and reproducible. Tune the
  keyword tables for your agencies; the contract stays the same.
- **The slides sketch an `nric_directory` MCP** (`npx @gov/nric-mcp`) as the
  "bring your own capability" illustration. This bundle realizes that capability
  as an *offline local tool* instead, so it can't fail to boot on a venue
  network. Plugging in a real MCP server is a config edit, not a code change.
- This bundle uses the **shipped-example schema** (`executor:` + `prompt:` +
  `guardrails.policies` + `tools.python` auto-discovery + `tools.agents`),
  matching `examples/scribe` and `examples/polly`. The higher-level
  `AGENTSPEC.md` documents a *different* `llm:` form and an HTTP-only
  `tools/mcp/` shape; do not mix the two.
- Model ids are intentionally NOT pinned so the bundle runs on whatever provider
  you configured. Pin `executor.model` only if you want a specific catalog
  model.
