# The Evidence Ladder

> How an agent decides what a value *is*, and how it records that it decided.

Derivation is not inference from vibes. It is a search over a fixed ladder of evidence
classes, ordered by reliability, terminated at the first class that yields a sufficient
answer — and the answer must be annotated with the class that produced it.

## The five classes

### E0 — Declared

The author wrote the affordance in the manifest, with a comment saying why.

```toml
# Meep reads resolution once at Simulation() construction. It is not a live parameter:
# the Yee grid is built from it. Sealed is the only honest liveness.
name = "resolution"
affordance = "dial"
liveness = "sealed"
provenance = { grade = "E0", evidence = "author", witness = "manifests/meep.toml:41" }
```

E0 is authoritative and unimpeachable — but it is also unaudited. An E0 claim that
contradicts E1 is a bug in the manifest, and a reviewer is entitled to ask for the
demonstration. E0 is for knowledge the code does not expose, not for bypassing evidence
that exists.

### E1 — Structural

The machine-readable surface of the code. This is the class that should settle most
derivations, because it is both reliable and cheap to read mechanically.

| Exposure | E1 surface |
| :--- | :--- |
| Python object | `inspect.signature()`, type annotations, `ast` of the constructor, dataclass/attrs fields |
| CLI (argparse) | `parser._actions` via a `--dump-schema` hook, or `ast` of `add_argument` calls |
| CLI (hand-rolled) | the usage string, plus the parsing code's own grammar table |
| Deck format | the deck grammar: `begin:<block>` … `end:<block>`, key `=` value |
| Tag-value paramfile | the reader's `sscanf` format string; the tag list in the source |
| Julia | `Base.@kwdef` struct fields, `@with_kw`, or the function's `kwargs` |
| HDF5/NetCDF output | dataset names, shapes, dtypes |

E1 gives you: the value's **name**, **type**, **default**, and often its **admissibility**
(an `enum`, a `choices=` list, a range check in the source). It rarely gives you
**liveness** — that is E4's job or E0's.

### E2 — Documentary

Docstrings, `--help` text, README tables, comments inside a deck file.

E2 is where "must be one of: open, periodic" lives, and where "read once at start-up" is
sometimes written. It is medium reliability because documentation drifts from code, and
because it is prose: extracting `lo`/`hi` from "should be between 8 and 200" is a
heuristic, not a parse.

**Use E2 for corroboration and for domain enumeration; never for liveness alone.** A
docstring that says "can be changed during a run" is a claim about a version of the code
that may no longer exist.

### E3 — Nominal

Naming and unit conventions. The weakest class, and the one agents reach for first when
they should reach for E1.

Signals: `_steps`, `n_`, `num_`, `_every`, `*_interval`, `dt`, `t_end`, `omega_*`, `*_min`
/`*_max`, SI suffixes in the name, `_on` / `_enable` for booleans.

E3 corroborates. It never settles an affordance on its own. A value settled at E3 alone is
`unresolved` (SPEC §5.4) — because E3 is exactly the class that produces confident wrong
answers. `resolution` sounds like a dial; in a spectral code it may be a sealed
construction parameter. The name told you nothing true.

### E4 — Behavioural

What a probe run actually did.

- Did the value appear in stdout at all? Then it is at least observable.
- Did it appear once, or per step? That is `pitch`.
- Did writing it mid-run change the next sample? That is `liveness: midrun`, demonstrated.
- Did writing it produce no change and no error? That is `grade: advisory` — or a lie in the
  code, which is a `dissent` record.

E4 is conclusive and expensive. It is the only class that can establish liveness, and the
only class that can falsify an E0 claim.

## The settling rule

```
for cls in [E0, E1, E2, E3, E4]:
    if cls yields a sufficient answer for the field: settle; record cls; stop
if nothing sufficient: mark "unresolved" at the highest class consulted; stop
```

"Sufficient" is per field:

| Field | Sufficient at |
| :--- | :--- |
| `affordance` | E1 (or E0). E2/E3 alone → `unresolved`. |
| `domain` (lo/hi/values) | E1, or E2 with an explicit enumeration, or E0. |
| `liveness` | E4, or E0 with a cited reason. **Never E2 or E3.** |
| `grade` | E0 or E4. Default `imperative` at E1, flagged as assumed. |
| `shape` | E1 (dtype/shape of the output), or E4. |
| `pitch` | E4, or E1 if the code declares an output interval. |

The asymmetry around `liveness` is deliberate. Liveness is the field that produces
decorative sliders, it is the field documentation is most often wrong about, and it is the
field no amount of reading can settle. Liveness is E4 or nothing.

## Conflict handling

When two classes disagree, the higher class wins and the disagreement is recorded:

```json
{"kind": "dissent", "point": "n_steps", "value": {"E1": "int, unbounded", "E3": "looks like a dial"},
 "outcome": "rejected", "note": "E1 wins; unbounded int is `unresolved` until bounds are found"}
```

Recording dissent is not bookkeeping. It is how a manifest accumulates the specific
knowledge that this parameter looks like one thing and is another — the knowledge that
makes the second author's derivation cheaper than the first's.

## The trace

A conformant implementation can emit its derivation as a table:

```
point          affordance   evidence  cls  witness
resolution     dial         signature E1   meep.Simulation.__init__(resolution: int)
boundary       ratchet      enum      E1   meep.Simulation.__init__(boundary: str, choices)
stop           trigger      signal    E4   run:meep-stop-01
flux           gauge        stdout    E1   meep: sim.display_fluxes(...)
n_steps        unresolved   name      E3   deck:begin:control n_steps
```

This table is the artifact a reviewer checks. An implementation that cannot produce it has
not derived anything — it has guessed, and dressed the guess in a `provenance` field.

## Cost discipline

E4 costs a job. Do not spend it on every field:

1. Derive everything at E0–E3 first. Cheap, and it usually covers the whole surface.
2. Spend one short probe run on liveness only, for the handful of IPs where E1–E3 disagreed
   or where mid-run control is plausible (in-process Python, Julia callbacks).
3. For deck-driven CLI codes, do not probe liveness at all: the answer is `sealed`, and the
   probe would only confirm what the architecture already dictates.

The last point is where most derivation effort is wasted. A code that reads its parameter
file once at start-up cannot accept a mid-run parameter change, no matter what the
docstring says. Recognising the architecture answers the liveness question for free — and
that recognition is E4-grade knowledge obtained without running anything, which is the best
kind.
