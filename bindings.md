# Bindings

> Six consumers, one manifest. They may differ in how things look, and must not differ in what
> they admit — or in what they print.

A binding is the replaceable half of the specification. The manifest fixes what may be read and
written, at what resolution, with what display precision; a binding decides pixels, keypresses and
fonts. Six have been written against this protocol. Two ship with the reference implementation; the
other four are kept as experiments, because they produced the rules below and a specification with
exactly one binding cannot be distinguished from a specification of that binding.

## The six

| Binding | Where | Transport | Frames | What it uniquely buys | What it cannot do |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Web** | `ui/index.html` | SSE + fetch | PNG `<img>` | Nothing but a URL. No install, works over an SSH tunnel, works on a phone. | No disk access; a specimen must come through the seam process. |
| **ImGui** | `experiments/implot_app.py` | HTTP poll | raw RGB → texture | 60 fps plots with no DOM in the path; direct GPU upload. | Weak widget ecosystem; fonts and IME are your problem. |
| **Electron** | `experiments/electron/` | SSE + fetch | PNG | Resident window, filesystem, configurable API base. | ~200 MB of Chromium to do what a tab does. Its value is convenience, not capability. |
| **Terminal** | `tui/seam_tui.py` | HTTP poll | RGB → ASCII ramp | Works over any SSH session, no display, no install. Finds the spec's gaps. | 80 columns, no colour gradient, no mouse. |
| **Tk** | `experiments/tk_app.py` | HTTP poll | PNG → `PhotoImage` | Retained-mode: the only binding that can detect a manifest whose point identity churns. | Needs an interpreter built with Tcl/Tk. |
| **Makie** | `experiments/makie/` (+ `bridge.py`) | TOML snapshot on disk | RGB → `image!` | Reactive observable graph, in Julia. Proves transport is out of scope. | No HTTP/JSON stack in Julia; needs a bridge process. |

All six read `GET /api/manifest` and `GET /api/state`, write through `POST /api/intervene`, and
fetch grids from `GET /api/frame`. Nothing else. That set is small on purpose: it is the smallest
surface on which a binding can be complete, and any binding that needs more is a binding that has
started inventing semantics.

## Why the terminal one mattered most

It is the binding with the least room, so every place where the manifest was vague showed up as an
invented convention rather than as space to hide it. Writing it produced SPEC §4.7 in full:

- **Grouping.** Web grouped by liveness, the terminal wanted by affordance, the manifest said
  nothing. Now `group` is declared and every binding follows manifest order.
- **Formatting.** `%.4g` vs `toPrecision(5)` vs a hand-rolled f-string is three renderings of one
  sample. Now `precision` is declared and `seam.client.format_value` is the shared answer, with the
  JavaScript copy compared digit for digit by `tests/test_format_parity.py`.
- **Commit boundary.** A held arrow key must not emit forty interventions, and a dragged slider
  must not emit one per pixel. Adjustments stay in a draft; one submission is one crossing.
- **Arming.** `stop` sits one keypress from `dump_slice`. A trigger may declare `confirm`, and a
  binding must make the operator mean it.
- **Position mapping.** A log dial means one thing if the slider is linear in the exponent and
  another if it is linear in the value. Now the mapping is normative.

Five programming models, one manifest: DOM, immediate mode (ImGui), immediate mode with a
draft (terminal), retained mode (Tk), reactive graph (Makie). Each found a different gap, and two
of the four experiments exist only as *evidence* that the declaration is the invariant:

- **Retained mode** (Tk) is the only model that can tell whether a point keeps its identity across
  polls. An immediate-mode surface rebuilds everything and cannot notice. A retained-mode binding
  must rebuild its tree only when the declared point set changes, and patch values otherwise — or
  the operator loses focus, cursor and scroll on every refresh.
- **Reactive** (Makie) is the only model where writing a value and a user editing it are the same
  operation. That produced SPEC §4.7(f): a value flowing job→surface is an observation, and one
  flowing surface→job is an intervention; a binding that cannot tell them apart loops, and the
  loop is invisible until somebody reads a trace full of interventions nobody made.

## The two rules

**(a) A binding MUST NOT change admission.** If a `sealed` point rejects a write, it rejects it for
every consumer: human in a browser, human in a native window, human at a terminal, agent through a
tool schema. The form that accepts a value the tool layer rejects is how one team ends up with two
truths.

**(b) A binding MUST NOT change presentation either.** Grouping order, significant digits, and the
position-to-value mapping are declared, not chosen. Two surfaces of one run that disagree on the
fourth digit are showing two different numbers.

Both are checked, not asserted. `tests/test_bindings.py` starts a live run, drives it through the
clients, and:

- performs the same sealed write through a native client and through HTTP, requiring both to be
  `rejected`;
- compares the Python and JavaScript formatters on a matrix of awkward values;
- renders the terminal surface and asserts it fits its column budget and that every control has a
  declared group.

```
python tests/test_bindings.py        # two surfaces, one manifest, one verdict
python tests/test_format_parity.py   # the formatting rule, implemented three times
```

A consistency check is not a correctness check: the first version of the formatter stripped
trailing zeros from scientific mantissas in *both* implementations, so they agreed perfectly while
both rendering a declared precision of 3 as `4e-10`. The parity test therefore also asserts
expected strings, not only equality.

## What a fifth binding needs

1. Fetch `/api/manifest` at start. Read `human` for controls, `agent` for tool signatures, and
   `diff` — if it is non-empty, refuse to render and say so.
2. Subscribe to `/api/events` if the platform has an event stream; otherwise poll `/api/state`.
   Do not invent a third cadence: the crossing loop's cadence is already in `cadence.poll`.
3. Render affordances, not widgets-you-like. A `ratchet` is not a spin box, and a `gauge` is not a
   form field.
4. Show `liveness` and `grade` on every intervention. A control whose liveness is invisible is a
   control that will be attempted at the wrong time.
5. For grids, request a preview at or below `preview.max_width`, and never resample it yourself
   (SPEC §4.6 — the producer's reduction is a filter, yours is aliasing).
6. Send interventions as `{point, value}` and display `outcome` verbatim: `rejected` with its note
   is information, not an error to swallow.
7. Format numbers with the §4.7b rule, or import an implementation of it. Do not "improve" it: the
   only thing worse than an ugly number is two different ugly numbers.
