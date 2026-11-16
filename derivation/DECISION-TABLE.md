# Decision Table

> writeability × domain shape × liveness → affordance

The whole derivation, in one table. An agent implementing Seam should be able to run this
in its head, and an implementation should be able to run it as a function.

## Step 1 — writeability

Ask one question, answered by E1: **is this value read back by anything?**

| Answer | Kind |
| :--- | :--- |
| The code computes it; nothing reads it back. | Observation Point → `gauge`. Done. |
| The code accepts it as input; the code may read it back. | Intervention Point → steps 2–3. |
| The code accepts it *and* exposes it *and* nothing reads it back (an echo). | OP. An output that is also an input is still an output for the purpose of the surface. |
| Cannot tell. | `unresolved`. |

## Step 2 — domain shape

| Shape | E1 signal | Notes |
| :--- | :--- | :--- |
| Void (no value) | method with side effects, verb subcommand, directive without argument | → `trigger` |
| Boolean | `bool` annotation, `type=bool`, `0/1` tag in a paramfile | → `ratchet` with 2 positions |
| Finite enumeration | `choices=`, `Literal[...]`, `str` with a documented set, a switch statement | → `ratchet` |
| Ordered discrete with few settings | small int with a documented range, `step` ≫ `hi-lo` | → `ratchet` |
| Continuous with declared bounds | `lo`/`hi` from a range check, or E0 | → `dial` |
| Continuous, unbounded | `float` with no range check anywhere | `unresolved`, or bound it at E0 with a stated reason |
| Structured (dict, list, file path) | `dict`, `list`, path | Decompose or `unresolved`. Never a text box. |

## Step 3 — liveness

| Situation | Liveness |
| :--- | :--- |
| Read once at construction / at deck parse / at job start. | `sealed` |
| Read at a declared step boundary from a channel you control. | `perstep` |
| Read whenever, from a channel you control. | `midrun` |
| Unknown, and the architecture says read-once. | `sealed` (E4-grade knowledge from E1 architecture) |
| Unknown, and the value is genuinely live. | `sealed` until demonstrated. **Claiming `midrun` without demonstration is a conformance violation.** |

## The table

| # | Writable? | Domain | Liveness | Affordance | Human binding | Agent binding |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | read-only | any | — | `gauge` | plot / readout / table by `shape` | read-only resource |
| 2 | yes | void | midrun, perstep | `trigger` | button | `tool()` |
| 3 | yes | boolean | any | `ratchet` | checkbox / segmented | `tool(x: bool)` |
| 4 | yes | enum | any | `ratchet` | select / segmented | `tool(x: Enum)` |
| 5 | yes | small ordered int | any | `ratchet` | stepper / segmented | `tool(x: int)` |
| 6 | yes | continuous, bounded | sealed | `dial` (disabled after seal) | slider, read-only post-seal | `tool(x: float)` pre-seal only |
| 7 | yes | continuous, bounded | perstep | `dial` (pending state) | slider with pending badge | `tool(x: float)`, returns `deferred` |
| 8 | yes | continuous, bounded | midrun | `dial` | slider | `tool(x: float)` |
| 9 | yes | continuous, unbounded | any | `unresolved` | labelled value, no control | not exposed |
| 10 | ? | ? | ? | `unresolved` | labelled value + provenance | not exposed |

Rows 6, 7, 8 are the same affordance with three different liveness values, and that is the
point: **the widget does not change, the admission does.** A sealed dial and a mid-run dial
look identical and behave completely differently, which is why `liveness` must be visible
on the control and not merely known to the adapter.

## Invariants an implementation must enforce

```
1. affordance = trigger         ⇒ liveness ∈ {midrun, perstep}
2. affordance = dial            ⇒ domain.kind = continuous ∧ lo, hi finite
3. affordance = ratchet         ⇒ domain.kind = enum ∨ (integer ∧ lo < hi ∧ step ≥ 1)
4. affordance = gauge           ⇒ point is in [[observe]]
5. affordance = unresolved      ⇒ no interactive binding, no agent tool
6. grade = gated                ⇒ liveness ∈ {midrun, perstep}
7. ∃ unique names; ∃ provenance with witness for every point
```

Violations are manifest errors, not runtime warnings. A manifest that fails invariant 1
produces a button that works only before submission, which is a dial on a boolean
pretending to be an action — and the operator will press it after submission and nothing
will happen.

## Three worked derivations

### Meep `resolution`

```
E1  meep.Simulation.__init__(..., resolution: int, ...)          → int, no declared bound
E1  source: grid = mp.GridVolumes(...) built from resolution     → read once, at construction
E2  docstring: "resolution of the computational grid"            → no range given
E3  name: "resolution"                                           → looks like a dial
E0  author: range [8, 200] from the docs' tuning guidance        → bound it
─────────────────────────────────────────────────────────────────────
affordance = dial   liveness = sealed   grade = imperative   provenance = E1(signature) + E0(bounds)
```

Note what happened: E1 supplied type and the read-once structure; E0 supplied bounds
because no evidence anywhere declares them. The bounds are an editorial act, and declaring
them at E0 with a reason is honest. Leaving them absent and marking `unresolved` would be
more honest still — and produces a surface nobody can use. This tension is real and the
spec permits either, provided it is declared.

### EPOCH `nx`

```
E1  deck grammar: begin:control / nx = 200                      → integer, no bound in grammar
E1  architecture: deck parsed once at start-up                  → sealed
E2  deck comment: "Size of domain"                              → describes meaning, not range
E3  name: nx                                                    → E3, worthless here
E0  author: [16, 4096], log-spaced                                → bound it
─────────────────────────────────────────────────────────────────────
affordance = dial   liveness = sealed   provenance = E1(deck-grammar)
```

### Gadget-2 `TimeMax`

```
E1  paramfile grammar: "Tag<whitespace>Value", parsed by sscanf("%s%s%s")   → float
E1  architecture: paramfile read once at start-up                          → sealed
E2  README: "TimeMax = 1.0 → 0.978 Gyr"  (unit trap: unit time ≠ 1 Gyr)     → unit matters
E3  name: TimeMax                                                          → dial
E0  author: [0, 20] Gyr, displayed in Gyr, converted at seal                → bound + unit
─────────────────────────────────────────────────────────────────────
affordance = dial   liveness = sealed   unit = "Gyr"   provenance = E1(paramfile-grammar)
```

The `TimeMax` case is why `unit` is a first-class field and why bindings must show it. The
number the operator types is in Gyr; the number the code stores is in code time and is 2.2 %
different. A surface that shows `TimeMax` as a bare float will produce runs that are
silently 2.2 % short, and no amount of interface polish fixes a unit error.

## What the table is not

It is not a heuristic. Every row is decidable from the three facts, and every fact is
supposed to be established at a declared evidence class. If an agent finds itself reasoning
"this feels like a slider", it has left the table and is guessing — and the correct output
in that situation is `unresolved` with the evidence it did consult, not a confident wrong
answer.
