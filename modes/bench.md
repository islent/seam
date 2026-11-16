# Bench — the authoring surface

> Where you find out that the parameter you assumed was a slider is `sealed` — before a user does.

## The problem

Manifest authoring looks like form filling and is not. The author is making claims about a
code's behaviour, most of which they have not checked:

- that a value can change after submission;
- that a value's admissible set is what they wrote;
- that a quantity is sampled as often as they said.

Every one of these claims is checkable, and none is checked by a text editor. The bench exists
to put the check next to the claim.

## Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Bench — manifests/epoch.toml            [ Derive ⟳ ] [ Validate ] [ Save ]│
├──────────────────────────┬──────────────────────────────────────────────┤
│  Points                  │  resolution                    (intervention) │
│                          │                                              │
│  ▸ resolution    dial  E1│  affordance   ● dial                         │
│    boundary      ratch E1│               ○ ratchet  ○ trigger           │
│    nx            dial  E1│  liveness     ○ sealed  ● midrun  ○ perstep  │
│    t_end         dial  E0│  grade        ● imperative                   │
│    stop          trig  E4│  domain       lo 16   hi 4096   step 16      │
│    step          gauge E1│  unit         —                              │
│    flux_incid.   gauge E1│  ────────────────────────────────────────    │
│    flux_trans.   gauge E1│  provenance   E1  deck-grammar               │
│    n_steps       unreso E3│               witness input.deck:2          │
│                          │  ⚠ liveness=midrun claimed without E4 witness│
│                          │                                              │
│                          │  agent projection:                           │
│                          │    set_resolution(x: int, 16 <= x <= 4096)   │
│                          │    ── writes accepted before seal only?      │
└──────────────────────────┴──────────────────────────────────────────────┘
```

## Interaction logic

**Derive on edit.** Changing `affordance` re-runs the invariant checks and the projection
generation immediately. Changing `domain` re-runs the agent-signature generation so the author
sees the tool signature change as they type it. This is the bench's whole reason to exist: the
author sees the *other projection* while editing this one.

**Provenance is always visible.** Every point shows its evidence class. A point at E3 is
rendered with the same visual weight as a `TODO`; a point at E0 without a `witness` is a
warning. The author cannot quietly promote a guess to a declaration because the class is on
screen.

**The liveness contradiction is the headline warning.** When `liveness` is `midrun` or
`perstep` and the adapter has no E4 witness for that point, the bench shows it in red and the
Save button stays enabled — but the saved manifest records `assumed = true` in the provenance.
Blocking the save would be wrong (the author may be about to run the probe); pretending the
claim is verified would be worse.

**Unresolved points are listed, not hidden.** They appear in the point list with their
evidence class and an empty affordance. Clicking one opens the probe panel: the locators that
were consulted, and what each returned.

**Validate is a separate, explicit action.** It runs the full §4.1 invariant set plus the
projection diff, and it is the thing CI calls. Derive is cheap and continuous; validate is
deliberate and logged.

## The probe panel

The second half of the bench, and the half that does the real work:

```
Probe — resolution
──────────────────────────────────────────────────────────────
[✓] E1 signature       meep.Simulation.__init__      → int, no bound
[✓] E1 source          grid built in __init__        → read once (sealed)
[·] E1 argparse        n/a
[✓] E2 docstring       "resolution of the grid"      → no range
[✓] E3 name            "resolution"                  → suggests dial
[ ] E4 probe run       not run                       → liveness unverified
──────────────────────────────────────────────────────────────
Conclusion: dial / sealed / imperative      Settled at: E1 + E0(bounds)
```

The panel is a checklist of the ladder. An author who cannot fill it in has not derived
anything, and the panel makes that fact hard to avoid.

## What the bench refuses to do

**It will not infer for you.** No "auto-derive from signature" button that silently fills the
manifest. The derivation is a procedure with provenance; automating it away produces a manifest
whose claims have no author, and whose `provenance` fields are fiction.

**It will not hide an invariant violation behind a warning.** A manifest that violates
invariant 1 (`trigger` + `sealed`) cannot be saved at all. That is a shape error, not a
judgement call. Level-of-confidence issues (assumed liveness) warn; shape errors block.

**It will not render the run.** The bench has no gauges. Authoring and operating are different
activities, and a surface that does both encourages editing a manifest while a job is running
against it — which is how a trace ends up paired with a manifest that does not describe it
(`manifest.sha256` exists for exactly this reason, and the bench should be the place that never
needs it).

## Saving

Save writes the manifest and, if the run directory has a live job attached, refuses and says
why. A manifest is a description of a run's surface; changing it under a running job produces a
trace whose records reference points that no longer exist.

The rule: **edit, validate, then seal.** Not edit while sealed.
