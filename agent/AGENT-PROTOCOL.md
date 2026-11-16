# Agent Protocol

> The operating procedure an agent follows to turn a simulation code into a Seam surface.

This document is written for an agent, not about agents. It is a procedure with decision
gates and stop conditions. Follow it in order. Do not skip gates because the answer seems
obvious — the two most common failures in this work are both confidently guessed wrong
values (`liveness` and `domain bounds`), and both guesses survive every check except the
ones below.

---

## Move 0 — Classify the exposure

Before reading anything, answer one question: **how does this code accept parameters?**

| Exposure | Tell | Consequence for the rest of the procedure |
| :--- | :--- | :--- |
| **In-process Python** | `import meep`; you construct an object and call `run()` | `midrun`/`perstep` are *possible*. Read §1.2 of PROBES. |
| **Deck-driven CLI** | a `input.deck`, `begin:`/`end:` blocks | Everything is `sealed`. No probe needed. |
| **Tag-value paramfile CLI** | `Tag Value` lines, a C reader | Everything is `sealed`. Read the reader's format string, not the file. |
| **Struct-driven, hosted** | Julia `@kwdef`, a REPL you can hold open | `perstep` if a callback exists; else `sealed`. |
| **Library with no run loop** | you must write the loop yourself | You own the seam. `midrun` is yours to provide. |

**Gate 0.** Write the classification down before proceeding. If the classification is
ambiguous, stop and report ambiguity — do not pick the more capable option. Classifying a
deck-driven CLI as "probably controllable" is how decorative sliders are born.

---

## Move 1 — Enumerate the surface (E1)

Produce a list of every value the code accepts and every value it produces.

For an in-process Python code: signature + source harvest (PROBES §1.1, §1.2).
For an argparse CLI: parser dump (PROBES §2.1).
For a deck: grammar harvest (PROBES §3.1).
For a paramfile: reader's `strcmp` chain (PROBES §4.1).
For Julia: `@kwdef` block (PROBES §5.1).

**Output format — a table, not prose:**

```
name            dtype    default   source-locator              notes
resolution      int      —         meep.Simulation.__init__    reaches GridVolumes
boundary        str      —         meep.Simulation.__init__    docstring lists 5 values
nx              int      200       deck:begin:control:2        —
TimeMax         float    1.0       paramfile:12                unit = 0.978 Gyr
```

**Gate 1.** Every row needs a locator. A row without a locator is E3 evidence (you
remembered the name) and must be marked as such, or deleted. Deleting is usually right.

---

## Move 2 — Split into OP and IP

Apply DECISION-TABLE step 1. For each value, ask: **does anything read it back?**

- Written by the caller, read by the code → **IP**.
- Computed by the code, read by nobody (except printing/writing) → **OP**.
- Both → it is an OP whose value happens to be settable; declare it as an IP *and* an OP
  only if both directions are genuinely useful. Usually the OP is the interesting one.

**Gate 2.** Every value must be classified, with no "maybe". Values you cannot classify are
dropped from the manifest and listed in a `notes` block. A manifest that omits three
parameters honestly is better than one that mis-declares them.

---

## Move 3 — Derive domains (E1 → E2)

For each IP, determine its admissible set.

Order of evidence: `choices=` / `Literal` / `@enum` (E1) → docstring enumeration (E2) →
range check in source (E1) → author's bound (E0).

**Gate 3 — the bounds gate.** If no admissible set is found at E1 or E2:

- If the type is `bool` → two-position `ratchet`. Done.
- If the type is `int`/`float` with no bounds anywhere → **do not invent bounds silently**.
  Either declare `unresolved`, or declare bounds at E0 with a one-line reason and a stated
  source. Both are conformant; a bare `[0, 100]` with no provenance is not.
- If the type is `str` with no enumeration → `unresolved`. Strings are not dials.

Record which path you took. The reviewer needs to know whether they are looking at a
derived bound or an editorial one.

---

## Move 4 — Settle liveness (architecture, then E4)

This is the gate that decides whether the surface is honest.

**Step 4a — architectural answer.** From Move 0:

| Exposure | Liveness without any probe |
| :--- | :--- |
| Deck-driven CLI | `sealed` |
| Tag-value paramfile CLI | `sealed` |
| MPI CLI | `sealed` |
| In-process Python, parameter reaches a constructor | `sealed` |
| In-process Python, parameter read inside the step loop | `midrun` — *if* a channel exists |
| Julia, parameter in the `@kwdef` struct | `sealed` |
| Julia, callback channel exists | `perstep` |

**Step 4b — channel check.** `midrun` requires a *channel*: control file, socket, shared
memory, callback. If no channel exists, the value is `sealed` regardless of where it is read.
Reading a value each step from a struct nobody can write to is not liveness.

**Step 4c — E4 demonstration, only if 4a/4b say `midrun` or `perstep`.** One short run:
write a value mid-run, observe the effect, record the run id as the witness.

**Gate 4.** You may not write `liveness = "midrun"` without either (a) an E4 witness, or
(b) an E1 witness that a channel exists *and* that the loop reads it. Otherwise write
`sealed`. This gate is not negotiable and the specification calls violating it a
conformance failure.

> **Why this gate is the whole protocol.** Every other field, guessed wrong, produces a
> slightly ugly interface. Liveness guessed wrong produces an interface that accepts input
> and does nothing with it. That is not a UI bug; it destroys the premise that the seam is
> trustworthy.

---

## Move 5 — Derive observations

For each OP: `shape` from dtype and producer, `pitch` from where it is produced.

| Where produced | Pitch |
| :--- | :--- |
| inside a step loop, every iteration | `per-step` |
| inside a block that runs every N steps | `per-step` (and say N in `doc`) |
| after the loop | `on-demand` |
| written to a file per output interval | `per-step`, source = `file:` |
| computed on request from a stored array | `on-demand` |

**Gate 5.** An OP with no `pitch` is not declared. If you cannot tell how often it updates,
it is `on-demand` — the conservative choice, because `on-demand` promises nothing and
`per-step` promises everything.

Beware the aggregate temptation: a code that prints only `max(E)` gives you one OP. Resist
declaring it as a proxy for the field `E`. The field is `on-demand` and worth more.

---

## Move 6 — Bind (human projection)

Map each affordance to a widget per SPEC §7.1. Then check three things:

1. Does the control display `liveness`? If not, add it. An operator who cannot see `sealed`
   will try to move it.
2. Does the control display `unit`? If not, add it. (See the Gadget-2 `TimeMax` trap: 2.2 %
   of silent error, purely a unit-display failure.)
3. Does the control's admitted range equal the declared domain exactly — not wider, not
   narrower?

**Gate 6.** Enumerate both projections and diff them (SPEC §7.3). Same point set, same
domains. Any difference is a defect, and it is the only defect in this whole procedure that
is mechanically checkable — so check it.

---

## Move 7 — Trace

Wire the crossing records. Minimum viable trace per run:

- one `seal`
- one `transition` per lifecycle change
- one `observe` per OP per pitch tick — unless the OP is `on-demand`
- one `intervene` per write, with `outcome` from the adapter
- `caused_by` on every intervention: the seq of the observation that preceded it

**Gate 7.** Replay the trace end to end and answer, from the trace alone: *what did the
operator see immediately before they intervened?* If the trace cannot answer that, the
`caused_by` links are missing and move 7 is incomplete.

---

## What to hand back

```
1. exposure classification (Move 0) with the tell that decided it
2. surface table (Move 1) with locators
3. OP/IP split (Move 2), including the values you dropped and why
4. derivation table (Moves 3–5) with evidence class per field
5. unresolved list — every value you refused to guess
6. projection diff (Gate 6) — empty, or explained
7. one specimen: manifest + trace + artifacts, replayable offline
```

Item 5 is not an admission of failure. It is the most useful thing in the report: it is the
list of questions the code's author should answer, and it is the reason the manifest can be
trusted about everything else.

---

## Anti-patterns, in the order agents commit them

**Type-driven widget choice.** `float → slider`, `bool → checkbox`, `str → text field`. Wrong
on the two cases that matter: float-valued enums (slider over three admissible values, every
intermediate value throws) and sealed numeric parameters (live slider, dead effect).

**Liveness by optimism.** "It would be nice if the user could change this mid-run." It
would. It isn't. `sealed`.

**Bounds by round numbers.** `[0, 100]` because it is a percentage-looking thing. If the
code divides by the value, the true bound is `(0, 100]`, and `0` crashes the run. Bounds
come from a range check or from an author with a reason — never from plausibility.

**Silent omission.** Dropping the three parameters you could not derive, and shipping a
manifest that looks complete. The `unresolved` list is a deliverable.

**Aggregate substitution.** Declaring `max|E|` because the field is expensive to sample.
The aggregate answers a question nobody asked.

**The false `midrun`.** The one that hurts. See Gate 4.

**Unit laundering.** Reading `4 * micron` from a deck, storing `4`, and displaying `4` with
`unit: "um"` — which is correct only by luck, and becomes a factor of 10⁶ the first time the
deck uses `nm`. Parse the unit or declare it unknown; never assume the deck's base unit is
the one you want to display.
