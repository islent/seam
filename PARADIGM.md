# Paradigm

> Fifteen words, each of which makes a sentence possible that could not be said before.

A design vocabulary earns its keep in one way only: **someone can state a claim with it, and
someone else can disagree precisely.** "Harness" works because "the harness holds the model" is
a claim you can argue with. "Framework" does not, because "the model calls the framework" is
either a tautology or a category error.

This page is the argument for each word. If a word can be removed without losing a sentence,
it should be removed.

---

## The load-bearing sentences

Read these as the test suite for the vocabulary. Each one is precise, checkable, and impossible
to state in the conventional parameter/status/log language.

1. "This parameter is a `dial` with `liveness: sealed`, so the control is decorative after
   submission — and the seam says so."
2. "The pitch of this observation is `per-step`, so polling it at 10 Hz reads the same value
   ten times; that is a gap, not a plateau."
3. "That write was `advisory` and the job ignored it; there is a `dissent` record with the seq
   of the observation that preceded it."
4. "The two projections disagree on the bounds of `resolution`; the implementation is
   non-conformant and the check is mechanical."
5. "This point is `unresolved` at E3, which means the name suggested an affordance and nothing
   corroborated it."
6. "The specimen's trace shows the operator stopped the run eleven seconds after `energy_kin`
   crossed 2100 — that link is `caused_by`, not a timestamp coincidence."

None of those sentences can be assembled from `parameter`, `status`, `log`, and `result`. That
is the whole case.

---

## The fifteen

### 1. Seam
The declared contact line between a running job and any external actor.

**Sentence it enables:** "The seam is at the deck, not at the process" — i.e. this job's
interface begins where its inputs are fixed.

**What breaks without it:** you say "the interface", and nobody knows whether you mean the
Python API, the CLI, the dashboard, or the MCP server. All four are *consumers of* the seam.

### 2. Manifest
The single declarative document that both consumers project from.

**Sentence:** "That value is not in the manifest, so no projection may show it."

**What breaks without it:** the form and the tool schema drift, silently, and the drift is
discovered by a user rather than by CI.

### 3. Seal
The boundary at which parameters stop being writable.

**Sentence:** "Everything before the seal is a dial; after it, only what the code can actually
accept."

**What breaks without it:** "before the run" becomes an informal phrase, and the interface
starts offering controls that are valid only in a state the job has already left.

### 4. Observation Point (OP)
A declared readable quantity: name, shape, pitch, source.

**Sentence:** "Add an OP for the transmitted flux at `on-demand`; per-step would be 4×10⁸
samples."

**What breaks without it:** "output" — which conflates a printed line, a file, and an in-memory
array, and therefore cannot carry a sampling contract.

### 5. Pitch
How often an OP is guaranteed current.

**Sentence:** "The dashboard and the job disagree about the peak because nobody declared the
pitch."

**What breaks without it:** the single most common silent bug in scientific monitoring becomes
undiagnosable, because both sides believe they are reading the truth.

### 6. Intervention Point (IP)
A declared writable quantity, carrying Grade and Liveness.

**Sentence:** "That is an IP with `liveness: sealed`, so it renders read-only after submission."

**What breaks without it:** "input" — which cannot distinguish a knob from a constant, and so
invites a knob where a constant belongs.

### 7. Grade
What a write *means*: `advisory`, `imperative`, `gated`.

**Sentence:** "This write is advisory; if the job ignores it, the trace must say so."

**What breaks without it:** every write is assumed to take effect, so a silently ignored write
is indistinguishable from a successful one. This is the defect that makes an interface
untrustworthy rather than merely awkward.

### 8. Liveness
*When* a write is accepted: `sealed`, `midrun`, `perstep`.

**Sentence:** "Meep permits this assignment and the run is then wrong; liveness is not the same
as writability."

**What breaks without it:** a slider that moves and does nothing. Worse than no slider, because
it teaches the operator that the surface is decorative.

### 9. Crossing Record (CR)
One append-only record of one thing crossing the seam, with `caused_by`.

**Sentence:** "The intervention at seq 411 was caused by the sample at seq 409."

**What breaks without it:** the trace degenerates into a log: chronological, not causal, and
unable to answer "what did they see before they acted".

### 10. Affordance
The interaction kind a value admits. Exactly four: `trigger`, `dial`, `ratchet`, `gauge`.

**Sentence:** "A boolean is a ratchet with two positions, not a two-stop slider."

**What breaks without it:** widget choice becomes a matter of taste, and a matter of taste
cannot be audited. Note the word is *affordance*, not *widget*: the widget is a binding, and
bindings differ per renderer while affordances do not.

### 11. Derivation
Deciding an affordance from evidence, and recording which evidence won.

**Sentence:** "That affordance was derived at E3, which is to say it was guessed from the name."

**What breaks without it:** "auto-generated" — which hides the difference between a claim
backed by a signature and a claim backed by a hunch.

### 12. Binding
A renderer's realization of an affordance.

**Sentence:** "One manifest, four bindings: browser, terminal, Gradio, tool schema."

**What breaks without it:** the specification accidentally specifies a GUI framework, and dies
with it.

### 13. Projection
A consumer of the manifest. Two are normative: human and agent.

**Sentence:** "Enumerate both projections and diff them; divergence is a defect."

**What breaks without it:** you cannot say *why* the hand-written form and the hand-written
tool schema must agree — they are not two implementations, they are two views of one document.

### 14. Specimen
A frozen run: manifest + trace + artifacts, replayable with no job and no network.

**Sentence:** "Diff the two specimens; the affordance changed from dial to sealed, which is a
major version change."

**What breaks without it:** every example requires somebody else's cluster, and therefore every
example is documentation rather than evidence.

### 15. Preview
A declared reduction of a grid observation: how much of the array is allowed to cross the seam.

**Sentence:** "This grid declares `max_width = 120`, so what a surface shows is a frame the run
agreed to, not a picture the viewer improvised."

**What breaks without it:** every consumer reduces the array its own way, so two people looking
at the same run see two different pictures — and, measured on Meep during the drafting of v0.1,
the unreduced picture is not even the field: a raw Yee sample carries a grid-scale mode that
reads as fine structure. Downsampling is a filter, and a filter that nobody declared is a
fiction. (SPEC §4.6.)

---

## Three mode words

| Word | Mode | The sentence |
| :--- | :--- | :--- |
| **Scenario** | guided | "This tutorial is a scenario: it runs live *and* against a specimen, unchanged." |
| **Specimen** | frozen | "Open the specimen; every control is disabled because a recorded run accepts no writes." |
| **Bench** | authoring | "The bench re-derives on edit, so you see the other projection move as you type." |

---

## Anti-vocabulary

Words this specification deliberately does **not** use, and why. The rejections are as much of
the design as the acceptances.

| Rejected | Why |
| :--- | :--- |
| **Widget** | Names a rendering artifact. Using it makes the spec GUI-framework-specific by accident. |
| **Parameter** | Collapses OP and IP. Half of every "parameter" panel in scientific software is read-only data mislabelled as input. |
| **Status** | Collapses lifecycle state, progress, and health. `running` says nothing about whether the job is stuck. |
| **Job / Task / Run** | Three words for one thing in most codebases. This spec uses **run** for the execution and **seam** for its interface, and does not introduce a third noun. |
| **Dashboard** | Names a layout. Layout is out of scope (§2a), and naming it invites scope creep. |
| **Auto** (as a prefix) | Seam is not about automation. Its differentiator is *visible and interruptible*; "auto" asserts the opposite. |
| **Anything** (as a suffix) | Promises breadth. The falsifier is a fifth code that needs a fifth affordance, and four codes have not produced one — a name should not claim more than the tests do. |
| **Contract** | Already taken by Design by Contract, and it connotes legal text rather than a physical joint. `Grade` and `Liveness` carry the contractual content without the collision. |
| **Hook / Callback / Plugin** | Mechanism words. They say how the code is wired, not what crosses the seam. |

---

## What did not become a word

SPEC §4.7 added five rules — `group`, `precision`, the commit boundary, the position mapping, and
`confirm` — and **no new noun**. That is the test working as intended: these are constraints on how
an existing word (`Binding`) behaves, not new things in the world. A vocabulary that grows every
time a rule is added is a vocabulary that has stopped being a vocabulary.

## Why fifteen and not four

Four affordances are enough for a *surface*. Fourteen words are needed for a *specification*,
because a specification has to be able to describe its own limits: that a value is sealed
needs `Seal` and `Liveness`; that a derivation was weak needs `Derivation` and the E-classes;
that a run is evidence needs `Specimen`.

The test for whether a word belongs is not "is it useful" but **"does removing it leave a claim
unstateable"**. Nine of the fifteen fail that test on their own and are kept because they anchor
a section that would otherwise have no name. If a future revision can fold one into
another without losing a sentence, it should — the vocabulary is meant to be small enough to
hold in mind while arguing.
