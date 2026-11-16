# Intervention Point

> A declared place on the seam where state may be written, with a declared meaning.

An IP is the unit of *touching*. The hard part is not "which parameter" — it is **what a
write means**. A slider that moves and does nothing is worse than no slider, because it
teaches the operator that the surface is decorative.

So an IP carries two extra fields that most parameter systems omit: **Liveness** (can this
be written now?) and **Grade** (what happens if it is?).

## Fields

| Field | Required | Meaning |
| :--- | :--- | :--- |
| `name` | yes | Stable identifier, valid as a tool name. |
| `affordance` | yes | `dial`, `ratchet`, or `trigger`. Never `gauge`. |
| `liveness` | yes | `sealed`, `midrun`, `perstep`. |
| `grade` | yes | `advisory`, `imperative`, `gated`. |
| `domain` | for dial/ratchet | `{ kind = "continuous", lo, hi, step?, dtype? }` or `{ kind = "enum", values = [...] }` |
| `default` | recommended | The value used when the IP is never written. |
| `provenance` | yes | Which evidence settled the affordance and liveness. |
| `timeout` | for gated | Seconds after which an unacknowledged gated write is withdrawn. |

## Liveness: the honest question

Liveness is not a property of the UI. It is a property of the code, and the only honest way
to establish it is to demonstrate it.

| Liveness | Claim | How to demonstrate it |
| :--- | :--- | :--- |
| `sealed` | Only before submission. | Trivial: show that no channel exists to change it after launch. |
| `midrun` | Any time while running. | Write a value mid-run, observe the job's behaviour change, find both in the trace. |
| `perstep` | At declared step boundaries. | Write between boundaries, observe the value take effect exactly at a boundary, and observe a `deferred` record in between. |

**The failure this prevents.** The default behaviour of every ad-hoc simulation GUI is to
present all parameters as editable at all times. In most codes, most of them are read once
at start-up and never again. The user moves a slider, the run continues unchanged, and
nothing in the interface admits that the slider is decorative. Declaring `sealed` is not a
limitation — it is the only way the interface can be trusted.

Corollary rule: **if a write is accepted but the code ignores it, the grade is
`advisory`**, and the adapter SHOULD emit a `dissent` record when the value fails to take
effect. Silent absorption of writes is the defect.

## Grade: the meaning of a write

| Grade | Contract | Trace outcome |
| :--- | :--- | :--- |
| `advisory` | The job may ignore this. If it does, it must say so. | `accepted` then possibly `dissent` |
| `imperative` | Takes effect at the next crossing. Not negotiable. | `accepted` or `rejected`, never silently dropped |
| `gated` | The job suspends at the next crossing until acknowledged or withdrawn. | `deferred` → `accepted` \| `rejected` \| `deferred` until `timeout` |

`gated` is the only grade that changes control flow, and the only one a renderer must
represent as blocking. It is also the only one that can deadlock: a gated write with no
timeout on a job whose operator has walked away hangs the run. Adapters SHOULD declare
`timeout` on every gated IP. The specification does not yet say what happens when the
reader dies (see SPEC §11.3), which is a real gap.

## Domain

A `dial` needs finite bounds. Not because sliders need them — because an unbounded
continuous input cannot be validated, and an input that cannot be validated cannot be
rejected at the schema level, which means the agent projection has to learn bounds by
violating them.

```toml
domain = { kind = "continuous", lo = 8, hi = 200, step = 2, dtype = "int" }
domain = { kind = "continuous", lo = 1e-6, hi = 1e-1, log = true, dtype = "float" }
domain = { kind = "enum", values = ["open", "simple_laser", "periodic"] }
```

If a value is genuinely unbounded, it is not a dial: either bound it (a legitimate
editorial act — every real workflow has a sane range) or mark it `unresolved`.

## Trigger

A `trigger` is an IP with no value: an action. `stop`, `checkpoint`, `dump_slice`,
`pause`. Its domain is `{ kind = "void" }`.

Rules:

1. A trigger MUST NOT carry `liveness = sealed` (SPEC §4.1 invariant 1). A button that only
   works before submission is a dial on a boolean, and should be declared as one so that
   its state is visible.
2. A trigger SHOULD declare the state transition it causes, if any:
   `transition = "running -> checkpointing"`. This lets the agent projection expose the
   trigger with the precondition written into its description instead of leaving the agent
   to discover it by firing.
3. Triggers are `imperative` by default. An `advisory` trigger — "it would be nice if you
   checkpointed" — is almost always a modelling error.

## The mid-run question, answered honestly per code

| Code family | Typical achievable liveness | Why |
| :--- | :--- | :--- |
| In-process Python (Meep, FEniCS) | `midrun` or `perstep` | You own the main loop; a control file read each step is a legitimate channel. |
| Deck-driven CLI (EPOCH, Gadget-2) | `sealed` + `trigger` for signals | The deck is read once. SIGTERM is a real, demonstrable `imperative` trigger. |
| MPI CLI | `sealed` | Same, plus a signal that reliably cleans up is not free. |
| Julia struct-driven (AstroNbodySim) | `perstep` | The integration loop is yours; a callback at a step boundary is the natural channel. |

Note what this table says: **most HPC codes cannot accept a mid-run parameter change, and
that is fine.** The spec's value is that the impossibility is declared at authoring time,
not discovered by an operator who has been moving a dead slider for two hours.

## Example

```toml
[[param]]
name = "resolution"
affordance = "dial"
liveness = "sealed"
grade = "imperative"
unit = "px/um"
domain = { kind = "continuous", lo = 8, hi = 200, step = 2, dtype = "int" }
default = 30
doc = "Grid resolution. Fixed at construction; changing it requires a new run."
provenance = { grade = "E1", evidence = "signature", witness = "meep.Simulation.__init__(resolution)" }

[[param]]
name = "stop"
affordance = "trigger"
liveness = "midrun"
grade = "imperative"
domain = { kind = "void" }
transition = "running -> terminated"
doc = "Terminate the job. Backed by SIGTERM; the code writes a final checkpoint."
provenance = { grade = "E4", evidence = "signal-probe", witness = "run:epoch-stop-01" }
```
