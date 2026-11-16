# Seam Specification

**Version:** 0.1-draft
**Status:** Draft for implementation and criticism
**Editors:** Meng Runyu
**License:** CC-BY-4.0

> **This is a draft, and it is meant to be argued with.**
>
> The primitives here are a bet, not a result. One of them (`Preview`, §4.6) was added
> mid-draft because a measurement contradicted the first version, and others may need the
> same treatment — added, narrowed, or removed. If you think an abstraction does not hold — or that
> five affordances are needed where this document says four — that is the most useful report
> you can send, and §11 lists the places we already know are weak.
>
> This draft is published to be **cited and criticised**, not to be adopted. It is not stable,
> and version numbers will change without ceremony until v1.0.

---

## 0. Reading this document

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be interpreted as
described in RFC 2119.

A **Seam-conformant** implementation is one that satisfies the seven normative rules in
[§9](#9-conformance). Everything else in this document describes *how* to satisfy them
and *why* they are shaped this way. Section numbers marked **(N)** are normative.

---

## 1. Problem

An agent driving a scientific simulation today has two options, both bad.

It can call a tool and wait. `submit(params) → job_id`, `poll(job_id) → status`. The
agent learns nothing about what the job is doing, the human learns nothing either, and
neither can touch the job between submission and completion. MCP formalises exactly this
shape: a request enters a tunnel, a response exits. Everything inside the tunnel is
private to the simulation.

Or it can generate code. The agent writes a script, the script runs, the script prints.
Now the human can see everything — but only as text, only after the fact, and with no
structure an interface can bind to. Every parameter is a string in a file; every output
is a line in a log.

Both options discard the same thing: **the structure of what can be seen and what can be
changed**. That structure exists — it is latent in the code's API or its CLI — but
nothing forces it to be declared, so nothing can rely on it.

Seam's premise is that this structure can be declared once, cheaply, and that doing so
makes both the human surface and the agent surface fall out mechanically.

## 2. Non-goals

These are not omissions. They are the design.

**(a) Not a GUI framework.** Seam does not specify layout, styling, widget libraries,
colour, or interaction modality. It specifies four affordances; how a renderer draws
them is out of scope.

**(b) Not a transport.** The manifest and the crossing trace may travel over stdio,
HTTP, WebSocket, a shared filesystem, a message queue, or a printed page. A
conformant implementation need not define a wire format at all.

**(c) Not a scheduler.** Slurm, Kubernetes, `nohup`, `tmux`, a Jupyter kernel, a
long-running Python process — all are acceptable substrates. Seam says nothing about
how a job comes to exist.

**(d) Not a rendering obligation.** "Observable" is an interface obligation. An OP MUST
be readable at its declared pitch; nothing requires that anything read it, or that what
reads it draws every sample. A renderer that shows one number and fetches detail on
demand is conformant.

**(e) Not a promise of mid-run control.** A code that cannot accept a write between
submission and completion MUST declare `liveness: sealed` on every intervention. The
specification's contribution is to make that limitation *declared* instead of
*discovered three hours into a run*.

**(f) Not a replacement for MCP.** A Seam manifest can be projected into an MCP server;
the projection is one consumer among several. Seam describes the surface, MCP is one way
to reach it.

## 3. The Manifest  **(N)**

### 3.1 Single source of truth

A Seam surface MUST be generated from a **manifest**: a declarative document listing every
observable quantity and every writable quantity that the surface may expose.

A manifest MUST be the only source of truth. A projection MUST NOT introduce a value,
bound, unit, affordance, or default that is absent from the manifest. If a renderer wants
to show something the manifest does not contain, the manifest is wrong and MUST be
amended — not bypassed.

*Rationale.* The failure mode this prevents is the ordinary one: a hand-written form and
a hand-written tool schema that agree on the day they are written and disagree three
sprints later. When both are projections of one document, drift is not possible; there is
only one thing to drift from.

### 3.2 Required structure

A manifest declares:

| Field | Meaning |
| :--- | :--- |
| `seam.version` | Specification version the manifest targets. |
| `identity` | Human name, physics domain, code name and version, entry point. |
| `evidence` | The sources derivation actually consulted, as locators. |
| `[[param]]` | Writable quantities. §4.1 |
| `[[observe]]` | Readable quantities. §4.2 |
| `[[artifact]]` | Optional: file-backed products with a declared shape. §4.4 |

Unknown top-level keys are an error, not a warning: a manifest that silently carries a
key nobody reads is a manifest whose author believed something false.

### 3.3 Formats

TOML is RECOMMENDED for authoring, because comments are load-bearing in a document that
records *why* a value is `sealed`. JSON is RECOMMENDED for interchange. The two forms
MUST be losslessly convertible, and the conversion MUST NOT reorder `[[param]]` or
`[[observe]]` entries — order is presentation order.

The normative grammar is [`schema/seam-manifest.schema.json`](schema/seam-manifest.schema.json).

## 4. Points

Two directions cross a seam. A value that can only be read is an Observation Point; a
value that can be written is an Intervention Point. There is no third direction, and
nothing is both.

### 4.1 Intervention Points (`[[param]]`)

Every IP MUST declare:

- `name` — stable identifier, unique within the manifest.
- `affordance` — one of `dial`, `ratchet`, `trigger`. (See §5.1; `gauge` is not a legal
  affordance for an IP.)
- `liveness` — `sealed`, `midrun`, or `perstep`. §4.3
- `grade` — `advisory`, `imperative`, or `gated`. §4.4
- `provenance` — which evidence settled the affordance, and where that evidence is. §5.2

For `dial`, the IP MUST also declare a numeric domain: `lo`, `hi`, optional `step`,
optional `log`. For `ratchet`, it MUST declare the finite domain: either an enumeration
of labels, or an integer interval with a step.

**Invariants.** An implementation MUST reject a manifest that violates any of these:

1. `affordance = "trigger"` with `liveness = "sealed"`. A trigger has no pre-seal
   meaning; if a value can only be set before submission, it is a dial or a ratchet.
2. A `dial` without finite `lo` and `hi`. An unbounded dial cannot be bound to a slider;
   declare `grain: "numeric"` instead and bind a numeric field.
3. `grade = "gated"` with `liveness = "sealed"`. Nothing is running to gate.
4. Two IPs with the same `name`.
5. A `default` outside its own declared domain. A manifest whose default violates its own
   statement about what is admissible is a defect in the manifest, and no surface should have to
   render an impossible number. The same applies at the seal: a value offered for a sealed
   parameter MUST satisfy its domain, because sealing is not a way around validation.

### 4.2 Observation Points (`[[observe]]`)

Every OP MUST declare:

- `name` — stable identifier.
- `shape` — `scalar`, `series`, `grid`, `table`, or `log`.
- `pitch` — sampling interval, as `per-step`, `per-second:<n>`, or `on-demand`.
- `source` — where the value comes from: `stdout:<pattern>`, `file:<path>`,
  `api:<callable>`, `metric:<key>`.
- `provenance`.

`shape` is the rank of the quantity, not the way it is drawn. A `series` may be drawn as
a line, a sparkline, or a column of numbers; a `grid` may be a heatmap or a thumbnail.
Separating rank from rendering is what lets one manifest serve a terminal and a browser.

`pitch` is declared, never chosen by the consumer. A renderer that polls faster than the
declared pitch is reading a value the job has not promised to have updated; a renderer
that polls slower MUST mark the gap rather than interpolate.

*Rationale for pitch being normative.* Almost every "the dashboard is lying" bug in
scientific monitoring is a sampling-rate disagreement that nobody declared. Making pitch a
declared field converts a silent bug into a visible contract.

### 4.3 Liveness

| Value | Meaning | What the surface may do |
| :--- | :--- | :--- |
| `sealed` | Accepted only before submission. | Show the control before the seal; after the seal, render it read-only with its sealed value. |
| `midrun` | Accepted at any time while the job runs. | Keep the control live; mark accepted writes with a CR. |
| `perstep` | Accepted only at declared step boundaries. | Keep the control enabled but show a pending state until the next boundary; a write that misses a boundary is `deferred`, not lost. |

**An adapter MUST NOT claim a liveness it cannot demonstrate.** If mid-run writes are
queued and only applied at termination, `liveness` is `sealed`. If a write is accepted but
the code ignores it, `grade` is `advisory` and the adapter SHOULD emit a dissent record
when the value fails to take effect.

This is the most commonly violated rule in practice, and the most damaging: a slider that
moves and does not act is worse than no slider.

### 4.4 Grade

| Value | Meaning |
| :--- | :--- |
| `advisory` | A suggestion. The job may ignore it, and MUST say so if it does. |
| `imperative` | Takes effect at the next crossing. Not negotiable, not silently dropped. |
| `gated` | The job suspends at the next crossing until the write is acknowledged or withdrawn. |

`gated` is the only grade that changes the job's control flow, and it is therefore the
only grade a renderer MUST represent as blocking. A `gated` write with no timeout is a
liveness hazard; adapters SHOULD declare `timeout` on gated IPs.

### 4.5 Artifacts

`[[artifact]]` declares a file-backed product: `name`, `path` (may contain a step
placeholder), `shape` (`grid`, `table`, `series`, `blob`), `pitch`, `provenance`.

An artifact is an OP whose source is a file. It is declared separately only because
artifact presence is a lifecycle fact — "does the file exist yet" is itself an
observation, and a renderer must be able to distinguish *absent* from *empty*.

### 4.6 Preview  **(N)**

A grid observation declared at a live pitch MUST declare a preview:

```toml
[[observe]]
name = "ez_frame"
shape = "grid"
pitch = "per-step"
source = "file:frame.npy"
preview = { max_width = 120, diverging = false }
```

`max_width` is the maximum width, in pixels, of what may cross the seam. `diverging` selects a
symmetric colour map for quantities that cross zero; it is optional and only a hint.

**What crosses the seam for a grid OP is a frame, not the array.** The full array remains
available at `pitch: on-demand`, through the same OP or through a declared artifact.

Three reasons, and the third is the one that forced this section into the spec:

**(a) Bandwidth.** A 512×512 float64 slice is 2 MB. At one frame a second that is a 2 MB/s
seam, which is not a seam, it is a bill.

**(b) Agreement.** If the array crosses, every consumer reduces it its own way, and two people
looking at the same run see two different pictures. Declaring the reduction makes the picture a
property of the *run*, not of the viewer.

**(c) The raw sample is not the physical field.** Measured on Meep 1.33 during the drafting of
this version: a 160×160 `Ez` array from a driven point source carries a grid-scale mode that
flips sign between adjacent Yee cells. Rendered at native resolution it reads as fine structure
— an entire lattice of features that does not exist. 2×2 box-averaging cancels it exactly.

So downsampling is **a filter, not cosmetics**, and it has to happen where the declaration is,
not wherever a renderer happens to feel like it. A consumer MUST NOT request a preview wider
than `max_width`, and MUST NOT apply its own resampling to a declared preview. A producer MUST
honour `max_width`, and MAY apply a stronger reduction if its transport requires it — but it
MUST declare that in the manifest rather than doing it silently.

*Consequence for adapters.* An adapter that cannot produce a preview for a grid OP MUST declare
that OP `on-demand` and say why in `doc`. EPOCH's SDF dumps and Gadget-2's HDF5 snapshots are
declared exactly this way in the reference implementations: reading them needs a format reader,
and a specification should not require one to be called conformant.

### 4.7 Presentation  **(N)**

Four rules that look cosmetic and are not. Each one came from writing a second and third binding
and discovering that the manifest did not say, so each binding invented an answer and two
windows showed one run differently. "Two pictures of one run" is the failure this specification
exists to prevent, and it happens at the level of a decimal point just as readily as at the
level of a state machine.

#### (a) Grouping

Every point MAY declare `group`. A binding MUST render points grouped by their declared `group`,
in **first-appearance order** within the manifest, with ungrouped points last. A binding MUST NOT
group by affordance, liveness, or any other property it computes itself.

*Why.* The three reference bindings independently grouped by liveness, by affordance, and
alphabetically. All three were defensible; all three were invention. Grouping is editorial
structure — "grid", "run control", "numerics" — and only the author has it.

#### (b) Numeric formatting

Every point MAY declare `precision`, an integer in 0..12 (0 meaning "exact integer"), default 4.
A binding MUST render a numeric value by this rule, and the rule is **numeric, not type-based**:

1. If `precision` is 0, print the rounded integer.
2. If the value is zero, print `0`.
3. If the value is integral and its digit count is `≤ precision`, print it as an integer.
4. Else let `m = floor(log10 |v|)`. If `m ≥ precision` or `m < -2`, print scientific notation with
   exactly `precision` significant digits, **keeping trailing zeros in the mantissa**.
5. Else print fixed notation with `max(0, precision − 1 − m)` decimals, stripping redundant
   trailing zeros.

Rule 3 is numeric rather than `isinstance(v, int)` on purpose: JSON erases the difference between
`200` and `200.0` before a binding sees it, and two implementations that used the type test
rendered one sample as `1234567` and `1.235e6`. Rule 4 keeps the mantissa's trailing zeros
because `4.00e−10` and `4e−10` are different claims about how much is known.

Rounding on an exact tie is UNSPECIFIED. For continuous data a tie is measure-zero; for a discrete
value it does not arise because such values are integral.

#### (c) The commit boundary

An intervention is one *submitted* value, not one input event. A binding with a continuous input
device MUST coalesce adjustments and submit once — on slider release, on Enter, on a debounced
keystroke — and MUST NOT emit one crossing per pixel, per scroll tick, or per held key.

*Why.* A dragged slider and a held arrow key are the same user intent. Without this rule one
produces one crossing record and the other produces forty, and the trace stops being a record of
what the operator did.

#### (d) Position mapping for continuous controls

A continuous control's position `t ∈ [0, 1]` maps to a value by:

- linear (default): `v = lo + (hi − lo)·t`
- geometric, when `domain.log` is set: `v = lo·(hi/lo)^t`, requiring `lo > 0`

A binding MUST use the declared mapping. A binding that treats a log dial as linear
gives the same knob a different physical meaning on each surface.

#### (e) Destructive triggers

A `trigger` MAY declare `confirm = true`. A binding MUST require an explicit second confirmation
before firing it, and MUST show that it is armed. `confirm` is illegal on any other affordance.

*Why.* `stop` sits one keypress from `dump_slice` in every keyboard-driven surface, and one click
from it in every pointer-driven one. The agent projection already carried a `confirm` argument for
triggers; the human projection had no equivalent, which is an asymmetry with no justification.

## 5. Affordance and Derivation

#### (f) Programmatic updates are not gestures

A binding MUST NOT emit an intervention for a value it applied itself.

A surface continuously writes the job's state into its own controls: a slider must sit where the
run says it sits. In a reactive system (an observable graph, a data-bound form) that write
propagates exactly like a user's drag, so a naive implementation sends an intervention, receives
the new state, writes it back, and sends again — a loop that fills the trace with movements nobody
made. The same hazard exists in any toolkit with change notifications, and it is invisible until
somebody reads the trace and finds forty interventions they did not perform.

The rule is not "guard your event handler". It is that **the direction of a value change is part of
its meaning**: a value flowing from the job to the surface is an observation, and a value flowing
from the surface to the job is an intervention. A binding that cannot tell them apart is not a
binding of this specification.

*Observed.* Found while writing the Makie binding, where `slider.value[] = x` triggers the same
listener as a drag. The fix is a sync guard around every programmatic write, and it must be around
the *write*, not inside the handler, or a handler invoked during a sync still fires.


### 5.1 The closed set

Exactly four affordances exist:

| Affordance | Interaction | Human binding (typical) | Agent binding (typical) |
| :--- | :--- | :--- | :--- |
| `trigger` | Discrete, atomic, side-effecting, no value. | button | zero-argument tool |
| `dial` | Continuous value in a bounded interval. | slider, spin box | number with `minimum`/`maximum` |
| `ratchet` | Discrete value from a finite domain. | segmented control, select, checkbox | enum |
| `gauge` | Read-only. | plot, readout, table | read-only resource |

The set is closed by rule, not by preference. A value that appears to need a fifth kind is
two of these stacked (a "range slider" is two dials; a "file picker" is a ratchet over a
finite set of admissible paths, or a dial over an integer index); a value that fits none is
`unresolved` (§5.4).

*Why close the set.* An open set of widget kinds is what makes GUI generation
undecidable in practice: every framework has forty widgets and every parameter seems to
want a different one. Four kinds with a mechanical mapping from three declared facts makes
the choice a derivation rather than a judgement call — and derivations can be audited.

### 5.2 Provenance and the evidence ladder

Every affordance MUST carry provenance:

```toml
provenance = { grade = "E1", evidence = "signature", witness = "meep.Simulation.__init__(resolution)" }
```

`grade` is the evidence class that settled the affordance, from the ladder in
[`derivation/LADDER.md`](derivation/LADDER.md):

| Class | Evidence | Reliability |
| :--- | :--- | :--- |
| **E0** | Declared by the author in the manifest, with a comment saying why. | Authoritative |
| **E1** | Structural: function signature, argparse spec, deck grammar, struct fields, JSON schema of an input file. | High |
| **E2** | Documentary: docstrings, `--help` text, comments in a deck, README tables. | Medium |
| **E3** | Nominal: naming and unit conventions (`_steps`, `dt`, `n_`, `*_every`, SI suffixes). | Low |
| **E4** | Behavioural: what a probe run actually did. | Conclusive when available, expensive |

`witness` is a locator a third party can check: `file:line`, `python:dotted.name`,
`shell:command`, or `run:<run-id>` for E4.

**Rule.** An affordance settles at the highest class available, and MUST NOT be silently
upgraded. If E1 says `continuous` and E3 suggests otherwise, E1 wins and the conflict
SHOULD be recorded as a `dissent` crossing record. Recording dissent is how a manifest
accumulates the knowledge that "this parameter looks like a step count but is actually a
float".

### 5.3 Derivation procedure

Deriving an affordance is a decision over three facts, not a choice among widgets:

1. **Writeability** — is the value an OP or an IP? (E1: is it in the constructor /
   argparse / deck / struct at all, and is it read back?)
2. **Domain shape** — continuous, finite-discrete, boolean, or absent (a pure action)?
3. **Liveness** — can it change after the seal, and does the code honour that?

The affordance is then read off the table in
[`derivation/DECISION-TABLE.md`](derivation/DECISION-TABLE.md). For an OP, shape and
pitch are derived the same way and `gauge` follows unconditionally.

An implementation MUST be able to emit the derivation trace: for each declared point, the
evidence consulted, the class of the winning evidence, and the resulting affordance. A
derivation that cannot be inspected cannot be corrected.

### 5.4 Unresolved

A value whose affordance cannot be settled at E1 or better, and which has no E2/E3
corroboration, MUST be declared:

```toml
affordance = "unresolved"
provenance = { grade = "E3", evidence = "name", witness = "paramfile:Omega0" }
```

`unresolved` points are visible in the surface, are never bound to an interactive widget,
and are never hidden. Guessing is a conformance violation. An `unresolved` point is a
question for the code's author, and hiding it destroys the only signal that the question
exists.

## 6. Crossing Records  **(N)**

### 6.1 Obligation

Every crossing of the seam MUST leave a record. A crossing is:

- a **seal** — parameters became immutable;
- an **observation** — an OP was sampled;
- an **intervention** — an IP was written, accepted, deferred, or rejected;
- a **transition** — the job changed lifecycle state;
- an **artifact** — a declared artifact appeared or changed.

Observation crossings are included deliberately. A trace that records only interventions
answers "what did the human do" but not "what did the human see when they did it", and
the second question is the one that matters when reconstructing a run.

### 6.2 Record fields

A crossing record MUST contain:

| Field | Meaning |
| :--- | :--- |
| `seq` | Monotonic sequence number within the trace. |
| `at` | Wall-clock timestamp (RFC 3339, with offset). |
| `job_time` | The job's own notion of time at the crossing, if it has one. |
| `kind` | `seal` \| `observe` \| `intervene` \| `transition` \| `artifact` \| `dissent`. |
| `point` | The OP or IP name, or the lifecycle state name. |
| `actor` | Who caused it: `human:<id>`, `agent:<id>`, `job`, `seam`. |
| `value` | The value, or a content-addressed reference to it if it is large. |
| `outcome` | `accepted` \| `deferred` \| `rejected` \| `sampled` \| `observed`. |
| `caused_by` | `seq` of the record that caused this one, or `null`. |

`caused_by` is what makes the trace causal rather than chronological. An intervention that
was applied because a human saw a particular sample is reconstructible only if the
observation and the intervention are linked.

### 6.3 Immutability

A trace MUST be append-only. Corrections are new records (a `dissent` following a
contradicted claim), never edits.

## 7. Projections  **(N)**

A projection is a function from manifest to a consumable surface. Two projections are
normative.

### 7.1 Human projection

Maps each affordance to a binding:

- `trigger` → a control that fires once per activation.
- `dial` → a control whose admitted values are the declared interval, discretised by
  `step` if present. The binding MUST NOT offer a value outside `[lo, hi]`.
- `ratchet` → a control whose options are exactly the declared domain. No free text.
- `gauge` → a read-only element. Its visual form MAY be chosen freely from `shape`.

A binding MUST be able to display, for each control, the IP's `liveness` and `grade`. An
operator who cannot see that a control is `sealed` will try to move it.

### 7.2 Agent projection

Maps each affordance to a tool signature:

- `trigger` → a tool taking no arguments beyond the IP `name`.
- `dial` → a tool taking a number, validated against `[lo, hi]` and `step`.
- `ratchet` → a tool taking an enum.
- `gauge` → a read-only resource at the declared pitch, not a tool with side effects.

The agent projection MUST reject out-of-domain writes at the schema level rather than
accepting them and failing at the job. An agent that has to discover a bound by violating
it learns nothing generalisable.

### 7.3 Divergence is a defect

If the two projections expose different sets of points, or the same point with different
domains, the implementation is non-conformant. This is checkable mechanically and SHOULD
be checked in CI: enumerate both projections, compare.

## 8. Modes

The manifest drives three surface modes. They are described in [`modes/`](modes/); the
normative requirement is only that all three read the *same* manifest and produce
*compatible* bindings.

### 8.1 Scenario (guided)

A tutorial MUST be executable. A scenario is an ordered list of steps against a manifest:

```toml
[[step]]
kind = "expect"            # the run must reach this state
point = "step"
op = ">="
value = 10

[[step]]
kind = "intervene"         # perform a write
point = "dump_slice"
value = true
expect = "accepted"

[[step]]
kind = "assert"            # check an observation
point = "energy_total"
op = "within_rel"
value = 0.02
```

A scenario MUST run against a live job and against a specimen without modification. A
tutorial that only works live is a tutorial nobody can run twice.

### 8.2 Specimen (frozen)

A specimen is a run captured as `manifest + crossing trace + artifacts`, replayable with
no job and no network. Opening a specimen MUST reproduce the same bindings as the live
run, with every control disabled and every gauge driven by the recorded samples.

This is the mode that makes examples durable. An example that requires somebody else's
cluster is documentation; a specimen is evidence.

### 8.3 Bench (authoring)

The authoring surface, where a manifest is written. It MUST show, per point, the derived
affordance *and its provenance class*, and MUST re-derive on edit. It MUST refuse to save
a manifest that violates a §4.1 invariant, and SHOULD show what the agent projection would
expose for the current draft.

The bench is the surface where the ladder's output is visible. Its purpose is to make the
author notice that a parameter they assumed was a dial is `sealed` — before a user does.

## 9. Conformance

An implementation is Seam-conformant at v0.1 if and only if:

1. **Single source.** Every exposed point originates in a manifest; no projection adds
   to it (§3.1).
2. **Provenance.** Every point declares provenance with a checkable witness (§5.2).
3. **Honest liveness.** Every IP declares liveness and grade, and each claimed liveness
   is backed by a demonstration (§4.3).
4. **Total tracing.** Every crossing in §6.1 leaves a record with the fields of §6.2, and
   the trace is append-only (§6.3).
5. **No guessing.** Values that cannot be settled are `unresolved` and surfaced (§5.4).
6. **Reduced previews.** Every grid observation at a live pitch declares `preview`, and no
   preview wider than `max_width` crosses the seam (§4.6).
7. **One rendering.** Grouping, numeric formatting, slug mapping and the commit boundary follow
   §4.7, so that two bindings of one manifest show the same numbers in the same order (§4.7).

Conformance levels:

| Level | Requirement |
| :--- | :--- |
| **L0 — declared** | Rules 1, 2, 5, 6. A static manifest; no runtime. |
| **L1 — traced** | L0 + rule 4 + rule 7. |
| **L2 — driving** | L1 + rule 3. Mid-run interventions demonstrably take effect. |

Most adapters land at L1 on first contact. That is the expected landing point, and stating
it is more useful than pretending otherwise.

## 10. Design lineage

Seam is not a new theory. It sits at the intersection of four existing lines, and its
contribution is the joining.

**Design by Contract** (Meyer, 1986) made preconditions, postconditions and invariants
first-class at function boundaries. Seam applies the same discipline at the boundary of a
*long-running* computation rather than a call: an IP's `grade` is a postcondition on when a
write takes effect, and `liveness` is a precondition on when it may be offered at all. DbC
has no vocabulary for "this write is advisory" because a function call has no notion of
deferral; a nine-hour job does.

**Interface automata** (de Alfaro & Henzinger, 2001) describe components by the state
transitions that are legal and the inputs accepted in each state. An OP set and an IP set
are exactly an output alphabet and an input alphabet, and `liveness` is the state-dependent
input restriction. Seam does not borrow the verification machinery — it borrows the
observation that *which inputs are accepted depends on state*, and makes that dependency a
declared field instead of a runtime surprise.

**Provenance** (W3C PROV, 2013) tracks the lineage of *data products*. Seam's crossing
trace tracks the lineage of *state transitions*: not "where did this file come from" but
"who wrote this value, having seen what". The two are complementary; a complete record of
a run needs both, and scientific workflow systems have historically provided only the
first.

**HITL granularity.** Existing human-in-the-loop systems intervene at the turn level (the
agent finished a step, a human approves) or the task level (a human sets the goal). Seam
pushes the declared granularity down to the state-transition level, and — this is the part
that is new — requires the granularity to be declared *in the interface*, not chosen ad hoc
by a UI. "What is the smallest intervenable unit of this computation" becomes a question
with a written answer.

## 11. Open questions

Recorded rather than resolved, because a draft that hides its uncertainty is not a draft.

1. **Sampling cost.** An OP at `pitch: per-step` on a 10⁶-step run produces 10⁶ records.
   Compression is an implementation matter, but the spec should say whether a conformant
   producer may downsample its own trace. Current position: yes, if the downsampling is
   declared as an artifact rather than silently applied.
2. **Multi-job seams.** Nothing here describes a seam spanning several coupled jobs
   (climate couplers, co-simulations). The primitives look like they extend — a crossing
   whose actor is another job — but that is untested.
3. **Gated interventions and failure.** What happens to a `gated` write when the reader
   dies? Current position: unspecified, which is a real gap for production use.
4. **Affordance stability.** If a code changes and an affordance flips from `dial` to
   `ratchet`, is that a minor or major manifest version change? Current position: major,
   because a stored scenario may no longer be executable.
5. **The fifth affordance.** The closed set of four is a bet. The falsifier is a code whose
   parameter surface genuinely needs a fifth interaction primitive. Four codes have not
   produced one.
6. **Trace merging across ranks.** EPOCH was driven under `mpirun -np 4`, and four processes
   wrote four streams of progress. The reference implementation reads one append-only table
   written by rank 0, which works but is a choice: a crossing raised by rank 2 has no causal
   edge to an observation produced by rank 0. Whether a conformant trace needs a per-rank
   vector clock, or whether "the job speaks with one voice through a single writer" is a
   legitimate simplification, is unanswered.
7. **Nested jobs.** If a seam spans a job that itself submits jobs (a workflow step, a
   coupled run), does `liveness` inherit? Does a `gated` write inside a child job mean the
   parent is gated too? The primitives look composable — a crossing whose actor is another
   job — but nothing here says how, and the reference implementation never nested one.

## 12. Change log

| Version | Date | Change |
| :--- | :--- | :--- |
| 0.1-draft | 2026-11-15 | First draft. Four affordances, three grades, three liveness values, three modes, one preview rule, one presentation rule. Four reference instantiations, four bindings. |
