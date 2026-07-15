# SG Citizen Helpdesk — demo recipe

A step-by-step runbook for demoing the bundle (meta-harness, governance,
cross-vendor review). See `README.md` for what the bundle is; this is how to
present it.

## 0. One-time prep (before the room)

```
cd <dir containing sg-citizen-helpdesk/>

# Offline sanity check — all four tools, no provider needed:
python3 sg-citizen-helpdesk/validate.py        # expect RESULT: PASS

# A Claude provider for the brain + local tools:
omnigent setup        # or: export ANTHROPIC_API_KEY=...
# Optional (for the cross-vendor review beat): also an OpenAI provider for codex.
```

**Demo hygiene — read this, it saves real time:**

- **Fully stop the server after any bundle edit.** Omnigent caches the
  extracted bundle. `--no-session` starts a fresh *conversation* but can still
  read a *cached spec*. After editing `config.yaml`, run `omnigent stop` so the
  new bundle is re-extracted.
- **Start a NEW conversation to pick up changes.** A *resumed* conversation
  replays the spec it was created with. If the launch banner says "Resumed
  conversation…", use `--no-session` for a guaranteed-clean one.

## 1. Launch

```
omnigent stop
omnigent run sg-citizen-helpdesk          # add --no-session to force a fresh conversation
```

---

## Beat 1 — Meta-harness (safe opener)

Prompt (the slide-pinned anchor):

```
Normalize and validate this SG number: (+65) 8123-4567
```

Expected: `+6581234567 · valid · mobile`.

Say: "The brain runs on the Claude SDK; `phone_normalize` is a local Python
function we own. One line of config picks the vendor — swap it, nothing else."

## Beat 2 — Realistic helpdesk (the rich one)

```
I need to renew my passport. My NRIC is S1234567D and I live at postal 520123.
```

Expected: routes to **immigration / ICA Counter**; NRIC returned **masked**
(`*****567D`); postal → district 18, Tampines / Pasir Ris, East. (The NRIC call
triggers the approval card from Beat 3 — approve it to continue.)

Say: "One message, several owned tools — validate NRIC, resolve the postal
district, triage to the right agency queue — and the identity number is masked,
never echoed."

## Beat 3 — Governance (the reliable policy demo)

```
Validate my NRIC S1234567D
```

Expected: an **ASK / approval card** before `nric_validate` runs
(`gate_identity_lookup`: "Identity (NRIC/FIN) lookups require human approval").
Approve → masked result. Deny → the agent says it was blocked by policy.

Say: "This rule is authored once and applies to every session. It gates a tool
the bundle owns, so it fires on any machine — no external dependency."

> Why gate the NRIC lookup and not email? `gmail_message_send` is **not** in
> this bundle — the claude-sdk harness inherits it from the operator's
> `~/.claude.json` MCP servers, so it's present on some machines and absent on a
> clean one. That made email a flaky anchor. `gate_identity_lookup` gates a
> bundle-owned tool, so it's deterministic. (`gate_outbound_email` remains in
> the config as a documented connector example.)

## Beat 4 — Cross-vendor review (only if OpenAI/codex is configured)

```
Validate S1234567D and have the reviewer double-check the result.
```

Expected: a `codex` (different-vendor) sub-agent checks the answer → "checks
out."

Say: "The answer is cross-checked by a different vendor. Swap the reviewer's
harness to change who reviews — that's the meta-harness thesis: compose across
the model frontier."

## Beat 5 — Triage nuance (pocket / Q&A)

```
I have a question about my road tax and COE.
```

Expected: **transport / LTA Feedback** (not IRAS), even though "tax" is in the
text.

Say: "Routing is transparent, inspectable rules we own and tune — not a model
guessing."

## Beat 6 — Collaboration (share a case for a second opinion)

Driven entirely from the **UI**, not a prompt — no bundle change. The story: you
own a case, hit something worth a second opinion, and **you choose to share that
one session** with a named colleague. They open it on another device and weigh
in. Access is granted by you, per session — not standing visibility into a
queue.

Frame it carefully (this is a government audience):

- **This is a peer hand-off, not monitoring.** You are sharing a session you
  own with one person you name. No one — supervisor or otherwise — can see a
  citizen's session unless its owner shares it. Say that out loud; it turns the
  obvious "who's watching all these sessions?" question into a selling point.
- **The agent does not share anything.** Sharing is a human action in the
  platform's permission model. This bundle deliberately leaves
  `agent_session_sharing` OFF — a helpdesk agent has no business granting access
  programmatically. (If asked about org-wide oversight: that is a separate
  ADMIN role, not part of this demo. Mention it exists; don't demo it, and don't
  imply routine surveillance.)

Setup (verify BEFORE the room — see checklist below):
- The server is in **multi-user mode** with auth (single-user local mode has no
  one to share with).
- You have a second device / second account for the hand-off (e.g. a phone).

Run it:
1. Handle a case first so there's something to look at, e.g.
   `Renew passport, NRIC S1234567D, postal 520123` — approve the identity ASK,
   get the masked result routed to ICA Counter.
2. In the web UI, **share this session** with the colleague by email (or copy
   the session link). Grant COMMENT or EDIT access.
3. The colleague opens it on their **phone / second machine**, sees the same
   live transcript (masked NRIC, the approval that was granted), and either
   **replies with a turn** or **comments** on the result.
4. Back on the main screen, their message/comment appears live.

Say: "I own this case. I want a second opinion on the eligibility call, so I
share THIS session with a named colleague — I grant the access; they had none
until I did. They open it on their phone and weigh in, and the governance
(masked ID, the approval I granted) travels with the session. Multi-user,
multi-device, real-time — and access is explicit and per-session, not a
dashboard watching everyone."

### Collaboration pre-checks

- Confirm the server is multi-user: you can reach a share/invite affordance in
  the session UI, and `/v1/me` returns a real user (not the local single-user
  sentinel).
- Have the second account already logged in on the second device before the
  demo — don't burn stage time on a login.
- Decide the access level up front: COMMENT (they annotate) vs EDIT (they can
  send turns). EDIT is the stronger "reply from their phone" beat.
- Know your one-liner for the oversight question: sharing is owner-granted and
  per-session; org-wide visibility is a separate admin role, out of scope here.

---

## Fallback prompts

- PII defense-in-depth (ASK on card/SSN patterns, NOT phones/NRIC):
  `My credit card 4111 1111 1111 1111 was charged twice, help`
- Honest failure: `Validate my NRIC S1234567A` (bad checksum) or `71234567`
  (bad phone prefix).

## If a policy "does nothing"

Almost always the cache/resume trap: `omnigent stop`, relaunch, start a **new**
conversation. For the email policy specifically, see the connector caveat in
Beat 3.

## Honesty notes

- The NRIC / postal values are synthetic test vectors chosen to pass the
  checksum. The tool only asserts "well-formed", never "this person exists".
- All four tools are offline and deterministic (pure stdlib, no network).

---

## Setting a cost budget

Omnigent ships a built-in `cost_budget` policy that gates a session on its
cumulative LLM spend. Add it under `guardrails.policies` in `config.yaml`:

```yaml
    session_cost_budget:
      type: function
      function:
        path: omnigent.policies.builtins.cost.cost_budget
        arguments:
          max_cost_usd: 5.0            # hard cap (see note on DENY below)
          ask_thresholds_usd: [1.0, 2.5]   # soft checkpoints -> ASK once each
          expensive_models: [claude-opus-4-8]   # optional; which models the cap treats as "expensive"
```

How it behaves (gates on both the per-turn request and each tool call):

- **`ask_thresholds_usd`** (soft): each time cumulative session cost crosses a
  checkpoint, the turn / tool call is parked for approval (**ASK**), once per
  checkpoint.
- **`max_cost_usd`** (hard): once cost crosses the cap, further spend on an
  `expensive_models` model is **DENY**'d — it acts as a "downgrade to a cheaper
  model to continue" gate rather than a hard session kill.
- At least one of `max_cost_usd` / `ask_thresholds_usd` is required.

For a **live demo**, set the numbers tiny so it fires within a turn or two:

```yaml
          max_cost_usd: 0.50
          ask_thresholds_usd: [0.10, 0.25]
```

Then run a couple of the richer prompts (Beat 2 is the most expensive) and the
ASK card appears after the first threshold is crossed.

**Important caveat:** the gate reads `total_cost_usd`, which is only populated
when the provider/model has **catalog pricing**. On a subscription or an
unpriced gateway model, cost isn't measured — the policy then fails closed with
an ASK ("switch to a priced model or approve"). Verify your demo provider is a
priced/token-metered one, or the budget will show that fallback ASK instead of a
real threshold crossing.

Two related variants exist if you need them:

- **`omnigent.policies.builtins.cost.user_daily_cost_budget`** — same gating,
  but the budget is the session OWNER's spend per UTC day (`max_cost_usd` is
  required and must be > 0). Good for "each user gets $N/day".
- **`omnigent.policies.builtins.cost.subagent_cost_budget`** — scopes a budget
  to a spawned sub-agent; the parent sets it via `sys_session_send`'s
  `cost_budget` argument (not authored directly in this bundle's YAML).

### Do I need to reload the agent after enabling it?

**Yes — and a plain `omnigent run` will NOT pick up the change.** Two reasons:

1. If a server is already running, `omnigent run` reuses it and returns without
   re-registering the edited bundle (it prints "A local server is already
   running … — reusing it"). The bundle is registered only when the server
   *boots*, so a reused server keeps serving the spec it started with.
2. A *resumed* conversation replays the spec it was created with, so even after
   a restart an old conversation won't see the change.

So any `config.yaml` edit (the cost budget included) needs:

```
omnigent stop                                    # force a fresh server -> re-registers the bundle
omnigent run sg-citizen-helpdesk --no-session    # fresh server + fresh conversation
```

There is no CLI hot-reload of a bundle into a live server. If you target a
specific server with `--server <url>`, that server process must be restarted
too. Skipping the `omnigent stop` is the usual reason a newly-enabled policy
"does nothing".
