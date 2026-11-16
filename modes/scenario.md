# Scenario — the executable tutorial

> A tutorial that cannot be executed rots. A scenario is a tutorial with a test suite inside it.

## The problem a scenario solves

Every scientific code has a tutorial that reads:

> Set `nx = 200`, `t_end = 50 fs`, then press Run. After about a minute you should see the
> laser reflect off the target.

Three failure modes, all silent:

1. The reader's version differs, and `t_end` no longer means what the text says.
2. The reader sets `nx = 200` in the wrong block and gets a different run.
3. The reader does see something, and cannot tell whether it is the right thing.

A scenario converts each of these into a checkable statement. Not "you should see a
reflection" but `flux_transmitted` drops below 0.1 of its initial value by step 400. Now the
tutorial is a program, and the reader knows whether they succeeded.

## Shape

```toml
[scenario]
name = "laser-reflection"
manifest = "../manifests/epoch.toml"
requires = ">=0.1"

[[step]]
id = "seal-it"
kind = "intervene"
point = "nx"
value = 200
expect = "accepted"

[[step]]
id = "run"
kind = "intervene"
point = "start"
expect = "accepted"

[[step]]
id = "moving"
kind = "expect"
point = "step"
op = ">="
value = 40
timeout = "120s"

[[step]]
id = "reflected"
kind = "assert"
point = "flux_transmitted"
op = "lt"
value = 0.1
within = "step >= 400"
```

## Step kinds

| Kind | Semantics | Failure |
| :--- | :--- | :--- |
| `intervene` | Write an IP; assert the resulting `outcome`. | Write rejected, deferred when `accepted` expected, or no crossing record at all |
| `expect` | Block until an OP satisfies a predicate, or `timeout`. | Timeout |
| `assert` | Check a predicate against an OP *now* (or `within` a window). | Predicate false when evaluated |
| `snapshot` | Freeze the current surface state into the specimen. | OP absent |
| `note` | Print prose at this point. The only non-checkable step. | — |

Predicates are a small closed set: `lt`, `le`, `eq`, `ne`, `ge`, `gt`, `within_rel`,
`within_abs`, `exists`, `changes_by`. A scenario that needs an arbitrary expression has
stopped being a scenario and become a test suite — that is fine, but it should then be a
test suite, not a tutorial pretending to be prose.

## Dual execution

A scenario MUST run against a live job **and** against a specimen, unchanged.

```
seam scenario run scenarios/laser-reflection.toml --host user@hpc
seam scenario run scenarios/laser-reflection.toml --specimen specimens/epoch-laser-01
```

In live mode, `expect` polls the running job. In specimen mode, `expect` replays the recorded
trace at its recorded pace, or as fast as possible with `--fast`. In `--fast` mode the
`timeout` fields are ignored, because there is no wall clock to respect.

**Why both.** A tutorial that only works live cannot be run by a reviewer, by CI, or by a
reader without the cluster. A tutorial that only works offline cannot catch a code change.
Neither alone is a tutorial; together they are.

## Interaction logic in the surface

The tutorial mode is not a document with a Run button bolted on. It is a stepper over the
same surface the free mode uses.

```
┌──────────────────────────────────────────────────────────────────┐
│  Tutorial: laser-reflection             step 3 / 6   [◀] [▶] [↻] │
├──────────────────────────────────────┬───────────────────────────┤
│  Controls (from the manifest)        │  Narration                │
│                                      │                           │
│  nx        ●───────────  200  ⌾sealed│  "Now the pulse propagates│
│  t_end     ●──────────  50 fs ⌾sealed│   to the right. Watch the │
│  boundary  [simple_laser ▾]  ⌾sealed │   incident flux rise, then│
│  ── post-seal ──                     │   the reflected one."     │
│  stop      [ Stop ]       ⌾midrun    │                           │
│                                      ├───────────────────────────┤
│  Gauges                              │  ✓ gate 2 passed          │
│  ┌────────────────────────────────┐  │  ● gate 3 waiting…        │
│  │  flux_incident — rising        │  │    step >= 40  (now 12)   │
│  │  flux_transmitted — flat       │  │                           │
│  └────────────────────────────────┘  │  [ Next step ▸ ]          │
└──────────────────────────────────────┴───────────────────────────┘
```

Rules the surface must obey:

1. **Only the current step's controls are enabled.** Everything else is visible and read-only.
   Hiding future controls makes the tutorial a slideshow; disabling them makes it a lesson
   about the parameter space.
2. **A step's gate is displayed before it is satisfied**, with the live predicate value. A
   tutorial that says "wait for step 40" without showing the current step number is asking
   the reader to trust rather than observe.
3. **Failure is instructive, not fatal.** A failed `assert` freezes the surface at the failing
   sample and offers three exits: retry from the previous step, jump to the end, or drop into
   free mode with the current manifest. The third is the important one — it turns a failed
   tutorial into an exploration.
4. **The `note` steps are the only prose**, and they are rendered adjacent to the controls,
   never in a separate pane that can be scrolled away from the thing it describes.

## Authoring rules

- **One concept per scenario.** A six-step scenario that teaches the deck, the units, and the
  physics teaches none of them.
- **The first step is always a seal.** The reader must see the parameter set close, or they
  will not understand why later steps have no sliders.
- **Every scenario ends with a specimen.** `snapshot` as the last step, so the tutorial's
  output is a file the reader can hand to somebody else.
- **Numbers in prose must come from the trace.** "You should see about 0.7" is a number that
  will be wrong next version. "You should see `flux_transmitted` below 0.1" is a predicate
  that stays true or fails loudly.

## What a scenario cannot do

It cannot teach judgement. A scenario can assert that the transmitted flux dropped; it cannot
assert that the reader understands why. That is the residual job of prose, and pretending
otherwise is how tutorials become checklists that people pass without learning.
