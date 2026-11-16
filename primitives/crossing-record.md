# Crossing Record

> One append-only record of one thing crossing the seam.

A log answers "what happened". A crossing record answers "what happened, *in response to
what*". The difference is `caused_by`.

## Why observations are recorded

It is tempting to trace only interventions — those are the user's actions, the interesting
events. That trace answers *what did the human do* and leaves unanswerable the question
that actually comes up: **what did the human see when they did it?**

A run that was stopped after an energy spike is only explainable if both the sample that
showed the spike and the intervention that followed it are in the same trace, linked.
Recording only interventions produces a log that looks like arbitrary vandalism.

So the crossing record covers five kinds, and observations are the majority of them by
count.

## Kinds

| Kind | Crossing |
| :--- | :--- |
| `seal` | Parameters became immutable. Exactly one per run. |
| `observe` | An OP was sampled, or an artifact was fetched on demand. |
| `intervene` | An IP was written, and what became of it. |
| `transition` | The job changed lifecycle state. |
| `artifact` | A declared artifact appeared, changed, or vanished. |
| `dissent` | The trace contradicts a prior claim: a write was ignored, a derivation was wrong, an expectation was not met. |

`dissent` is the odd one out and the most valuable. It is how a trace records that
something is not as declared, without rewriting history.

## Fields

```json
{
  "seq": 412,
  "at": "2026-11-15T22:14:03.881+08:00",
  "job_time": {"step": 1840, "t": 0.42},
  "kind": "intervene",
  "point": "dump_slice",
  "actor": "human:operator",
  "value": true,
  "outcome": "accepted",
  "caused_by": 409
}
```

| Field | Notes |
| :--- | :--- |
| `seq` | Monotonic within a trace. Gaps are a defect, not a feature. |
| `at` | RFC 3339 with offset. Local time without an offset is a defect: it makes two traces from two machines incomparable. |
| `job_time` | The job's own time, as an object. `null` if the job has no time axis (rare) or before the first transition. |
| `kind` | From the table above. |
| `point` | OP/IP name, lifecycle state, or artifact name. |
| `actor` | `human:<id>`, `agent:<id>`, `job`, `seam`. |
| `value` | Inline if small (scalar, short string). For a `grid` or a file, a content-addressed reference: `{"ref": "sha256:...", "bytes": 1048576, "shape": [128,128]}`. |
| `outcome` | `sampled`, `observed`, `accepted`, `deferred`, `rejected`, `entered`, `exited`. |
| `caused_by` | `seq` of the causing record, or `null` for records with no in-trace cause. |
| `note` | Free text. |

## Causal links that matter

Three link patterns carry almost all the diagnostic value:

**Observation → intervention.** The human stopped the run because of what they saw. Without
`caused_by` on the intervention pointing at the observation, this is invisible, and a
reviewer reconstructing the run will conclude the stop was arbitrary.

**Intervention → transition → observation.** A write was accepted, the state changed, and
the effect is visible three samples later. This chain is the only evidence that an
intervention *worked* rather than merely being *received* — and it is exactly what an
adapter needs to demonstrate before it may claim `liveness: midrun` (SPEC §4.3).

**Dissent → intervention.** A write was ignored, so a second write was issued with a
different value. Recording the dissent keeps the second write from looking like
indecision.

## Size

A `per-step` OP on a 10⁶-step run produces 10⁶ observe records. Storing each as a JSON
object is wasteful but not wrong; the specification does not mandate a format. What it does
require is that any downsampling is **declared as an artifact** rather than silently
applied, so that a reader can tell the difference between "the value was constant" and
"we only kept every thousandth sample".

Practical shape for large traces, which implementations are free to ignore:

- Header block with the manifest hash, so a trace cannot be silently paired with the wrong
  manifest.
- Columnar body (one array per field) for the bulk `observe` records.
- Row-based tail for the sparse kinds (`seal`, `intervene`, `transition`, `dissent`), which
  are few and read individually.

## Immutability

A trace is append-only. Corrections are new records. A `dissent` that contradicts seq 412
is appended at seq 900 and points at 412; seq 412 is never edited.

This is not fussiness. A trace is the thing a reviewer uses to decide whether to believe a
result; if it can be edited, it proves nothing, and the entire premise — that the seam is
inspectable — collapses.

## Example chain

```
seq 1    seal        params            seam      -         accepted     null
seq 2    transition  initializing      job       -         entered      null
seq 3    transition  running           job       -         entered      2
seq 4    observe     step              seam      {step:0}  sampled      3
seq 5    observe     energy_kin        seam      1590.1    sampled      4
...
seq 409  observe     energy_kin        seam      2103.7    sampled      407
seq 411  intervene   dump_slice        human:operator  true  accepted     409   <- saw 409, asked
seq 412  artifact    slice_01840.h5    job       {ref:...} observed     411
seq 413  observe     energy_kin        seam      2104.0    sampled      412
```

Read seq 411 with 409: the human dumped a slice *because* the energy reading was rising.
Read seq 413 after 412: the dump did not disturb the run. Both facts are recoverable from
the trace alone, and neither is recoverable from a log that records only interventions.
