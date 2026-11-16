# Changelog

All notable changes to the Seam Specification. Format loosely follows Keep a Changelog;
versions follow the rule in SPEC §11.4 — an affordance changing kind is a major bump.

## [0.1-draft] — 2026-11-15

First draft, published for implementation and criticism. Three revisions on the same day: the
first from writing the specification, the second from implementing it for three surfaces, the
third from implementing it for a terminal.

### Revision 3 — after the terminal binding

The fourth binding is the one that found the gaps, because 80 columns leave no room to hide an
invented convention. It produced SPEC §4.7 in full:

- **Added `group`** (§4.7a). The web surface grouped controls by liveness, the terminal wanted
  grouping by affordance, ImGui by neither. All three were invention. Grouping is editorial
  structure and only the author has it; ungrouped points render last.
- **Added `precision`** (§4.7b) and a formatting rule that is numeric rather than type-based.
  `%.4g`, `toPrecision(5)` and a hand-rolled f-string are three renderings of one sample, and two
  of them disagreed about whether `1234567.0` is an integer. JSON erases that distinction before a
  binding sees it, so the rule cannot use it.
- **Added the commit boundary** (§4.7c). An intervention is one *submitted* value, not one input
  event. This immediately caught a bug in the reference implementation: the ImGui slider returns
  `changed` on every frame of a drag, so one gesture was writing dozens of crossings.
- **Made the position mapping normative** (§4.7d). A log dial that is linear in value on one
  surface and linear in the exponent on another is two different knobs.
- **Added `confirm`** (§4.7e) for destructive triggers. The agent projection had carried a
  `confirm` argument since the first draft; the human projection had nothing. That asymmetry had
  no justification.

A second finding, about testing: the first formatter stripped trailing zeros from a scientific
mantissa so that a declared precision of 3 rendered as `4e-10`. It did this **in both
implementations**, so a cross-binding consistency check passed while both were wrong. Consistency
is not correctness; `tests/test_format_parity.py` now asserts expected strings as well.

### Revision 2 — after building the bindings

- **Added `Preview`** (SPEC §4.6, the fifteenth word). A grid observation at a live pitch must
  declare `max_width`, and what crosses the seam is a frame rather than the array. The forcing
  reason was empirical, not aesthetic: a raw 160×160 Meep `Ez` sample carries a grid-scale
  (Nyquist) mode that flips sign between adjacent Yee cells. Rendered at native resolution it
  reads as an entire lattice of fine structure that does not exist; 2×2 box averaging cancels it
  exactly. Downsampling is a filter, so the *producer* has to reduce, to a width the manifest
  declared — otherwise every viewer invents its own picture of the same run.
- **Added `bindings.md`** and the rule that follows from it: a binding may change how things look
  and never what they accept. Three bindings ship (web, ImGui, Electron) and one of the tests
  performs the same sealed write through a native client and through HTTP and requires both to be
  `rejected`.
- **Added two channels to the reference HTTP surface** — server-sent events for state, and a
  binary frame endpoint (`png` or raw `rgba`). Neither is normative; both are what "live" turned
  out to require in practice.

### Added

- **Manifest** as single source of truth, with two normative projections (human bindings,
  agent tool signatures) and a mechanical divergence check between them. SPEC §3, §7.
- **Four affordances**, closed set: `trigger`, `dial`, `ratchet`, `gauge`. Derivation from
  three declared facts (writeability, domain shape, liveness) rather than from type or name.
  `primitives/affordance.md`, `derivation/DECISION-TABLE.md`.
- **Evidence ladder** E0–E4 with a settling rule and per-field sufficiency. The rule that
  `liveness` is never settled below E0-with-reason or E4 is the load-bearing part.
  `derivation/LADDER.md`.
- **Intervention Grade** (`advisory`, `imperative`, `gated`) and **Liveness** (`sealed`,
  `midrun`, `perstep`) as separate fields, because "what a write means" and "when it is
  accepted" are independent questions. `primitives/intervention-point.md`.
- **Pitch** as a declared, normative field on observations. Sampling-rate disagreement was
  the most common silent bug in existing monitoring surfaces, and declaring the rate turns it
  into a contract.
- **Crossing Record** covering observations as well as interventions, with `caused_by` for
  causality rather than chronology. `primitives/crossing-record.md`.
- **Three modes** driven by one manifest: Bench (authoring), Scenario (executable tutorial),
  Specimen (offline replay). `modes/`.
- **Four instance mappings** across two physics domains and four exposure mechanisms:
  Meep (Python object), EPOCH3 (text deck), Gadget-2 (tag-value paramfile),
  AstroNbodySim.jl (Julia immutable struct). `mappings/`.
- **Agent Protocol**: a seven-move procedure with decision gates, written to be followed
  rather than admired. `agent/AGENT-PROTOCOL.md`.
- Machine-checkable grammar: `schema/seam-manifest.schema.json`.

### Observations from writing the four mappings

Recorded here because they are the evidence for the design, not decoration:

- **Liveness is not derivable from exposure type.** Meep permits a mid-run assignment that
  makes the run wrong; Julia forbids it at the language level. Same nominal exposure
  ("constructor kwargs"), opposite liveness for the same parameter.
- **The exposure's reader matters more than the exposure.** Gadget-2's paramfile looks like
  `key = value` and is parsed by `sscanf("%s%s%s")`, so `=` becomes the value. A harvest that
  reads the file and not the reader produces a manifest the code cannot consume.
- **Three of four codes are entirely `sealed`.** This is the finding, not the failure. A
  specification whose main output is "this cannot be steered, and here is the proof" is more
  useful than one that produces a live slider over a dead parameter.
- **One apparent fifth affordance** appeared and decomposed: AstroNbodySim's `TimeStep = 0`
  means "adaptive", which is a mode rather than a small number. Modelled as a ratchet over
  `{adaptive, fixed}` plus a dial for the fixed value. The closed set survived its first
  near-miss.

### Findings from the four instantiations (v0.1-draft, after implementation)

Recorded because each one changed a sentence in the normative text, not just a line of code:

- **`pitch` has no vocabulary for event-driven producers.** EPOCH appends its step table once
  per snapshot write: not per-step, not per-second. Currently declared `per-step` with a
  `notes` entry. A `per-event:<name>` pitch belongs in v0.2 (SPEC §11).
- **Writability and liveness are not the same thing, and Python will not tell you.** Meep
  permits `sim.resolution = 60` mid-run; the assignment succeeds and the run is then wrong. Julia
  forbids it at the language level. Same nominal exposure, opposite liveness for the same
  parameter — which is why `liveness` needs E4 or an explicit E0, never E2 or E3.
- **The exposure's reader outranks the exposure.** Gadget-2's paramfile looks like
  `key = value`; `sscanf("%s%s%s")` makes `=` the value. A harvester that reads the file and not
  the reader produces a manifest the code cannot consume.
- **Out-of-domain rejection is a feature the surface must show.** A test wrote `until = 9000`
  against a declared domain of `[5, 500]`; the seam rejected it *before* the job and recorded
  the rejection. Without that, an operator would believe the run had been extended.
- **A `dissent` record earned its place.** Gadget-2's `EnergyPot` column is silently zero when
  the build lacks `-DOUTPUTPOTENTIAL`. The value is not wrong, it is absent — detectable only by
  watching the column across rows, which is exactly what a crossing trace makes possible and a
  final-number comparison does not.
- **The two projections did diverge once, in this implementation.** Not in bounds or point
  sets, but in the `disabled` flag: specimen mode initially left triggers enabled because
  liveness said `perstep`. The mechanical diff did not catch it; the mode contract did (§8.2).
  Worth noting as a limit of rule 5's error detection.

### Findings from the bindings (revision 2)

- **The unreduced picture is not the field.** See `Preview` above. Worth restating because it is
  the only place in this project where a rendering choice changed a normative rule.
- **A viewer must not dead-end on the first declared grid point.** Both native clients initially
  requested frames from whichever grid OP came first in the manifest — which for Meep is
  `ez_slice`, an `on-demand` artifact nobody had produced. The fix belongs in the client (scan,
  then fall back), but the lesson is for the manifest author: **order your observations so the
  live ones come first**, because order is presentation order and every consumer honours it.
- **SSE, not polling.** The transport to a job is an SSH round trip of order a second, so it is
  already the bottleneck. A client polling at 1.5 s adds 1.5 s of dead time on top of it; a client
  polling at 100 ms asks the same question fifteen times. Push costs nothing when there is no news.
- **Post-processing is a run.** Modelled as a second seam with its own manifest, seal, trace and
  specimen, it needed no new primitive — only a different adapter. Its first useful output was a
  disagreement with the prose: `within_tolerance = 0.0` at 34 % energy drift, which independently
  confirms that Gadget-2's test initial condition is not a true Plummer equilibrium DF.

### Findings from the terminal binding (revision 3)

- **The narrowest binding is the best specification test.** Not because terminals are important,
  but because a surface with no room cannot absorb ambiguity: every vague field became a visible
  invention within an hour.
- **Manifest order is presentation order, and sorting breaks it.** The first version of the
  grouping helper sorted group names alphabetically. This contradicted SPEC §3.3 and was caught by
  looking at a screenshot, not by a test. Groups now appear in first-appearance order.
- **A short label is missing.** The terminal truncates `force_complex_fields` to
  `force_complex_f…` at 20 columns. Currently mitigated by showing the full name plus `doc` on the
  selected row, and deliberately *not* solved by adding a `short` field: the manifest already has
  a name and a doc, and a third string for every point is a cost that the two bindings which can
  fit the name do not need. Open question for v0.2 — the falsifier is a real parameter whose name
  cannot be abbreviated meaningfully.
- **The agent projection and the human projection drifted.** `confirm` existed on one and not the
  other for a full revision. The projection diff (SPEC §7.3) compares point sets and domains, not
  fields, so it did not catch it. Comparing *key sets* per point would have.

### Revision 4 — after the Tk and Makie bindings

Two more bindings, two more programming models: Tk is a retained-mode widget tree, Makie is a
reactive observable graph, and Makie's binding lives in Julia.

- **Added §4.7(f): programmatic updates are not gestures.** In a reactive system, writing the
  job's state into a control propagates exactly like a user's edit. The naive Makie binding sent
  an intervention, received the new state, wrote it back, and sent again. The rule is not "guard
  your handler" but "direction is part of a value's meaning": job→surface is an observation,
  surface→job is an intervention.
- **Added invariant 5 (§4.1): a value offered at seal must satisfy its declared domain.** Found by
  reading `1.20e3 a/c` off a dial declared `[5, 500]`: `--set until=1200` had bypassed validation
  because only *interventions* were checked. Sealing was an unvalidated side door into the surface.
- **`default` is now validated against its own domain** when a manifest is loaded. The same bug at
  authoring time should not need a run to find.

Findings that belong to `bindings.md` rather than to the specification:

- **Retained-mode identity.** A Tk surface must keep the same widget instance per point across
  polls, or every refresh resets focus, cursor and scroll. An immediate-mode surface passes
  regardless, so only a retained-mode binding can detect a manifest whose point identity churns.
- **The third implementation of a formatting rule finds its own bugs.** Julia's `log10` returns a
  `Float64`, which `@sprintf` rejects as a precision argument. Two implementations agreeing was
  already shown not to be evidence of correctness; three implementations disagreeing is what found
  this one inside a minute.


### Before the first public commit

Not a specification change — a preparation note, kept because the same mistakes recur.

- **Every machine path was scrubbed.** The reference runs happened on one shared HPC node, and
  its private address, account name and home-directory layout had leaked into the mappings,
  the manifests, the adapters and four specimens. The prefix is now `/opt/...`, and every
  adapter path is overridable through a `SEAM_*` variable. A reference implementation that only
  runs on its author's machine is a screenshot, not a reference implementation.
- **`--transport` no longer defaults to `ssh`, and `--host` no longer has a default.** A fresh
  clone running `seam run` without flags used to dial the author's cluster. It now runs locally.
- **The specimen hashes were recomputed after the path rewrite.** `manifest.sha256` and the
  `manifest_sha256` field in each trace header are derived from the manifest text, so editing a
  path invalidates them — and the loader refuses to pair a trace with the wrong manifest, which
  is exactly what it should do.

### Known gaps

- No first-class way to declare **parameter interaction** (`ComovingIntegrationOn` changes the
  meaning of `TimeMax`; `bc_x_min = simple_laser` requires a matching laser block). Currently
  expressed in `doc`, which is lossy.
- `gated` interventions have no defined behaviour when the reader dies (SPEC §11.3).
- Coupled multi-job seams are unaddressed (SPEC §11.2).
- The full CC-BY-4.0 legal text is not yet vendored.
