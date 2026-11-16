# Specimen — the frozen run

> An example that needs somebody else's cluster is documentation. A specimen is evidence.

## What it is

A specimen is a run captured as four files:

```
specimens/epoch-laser-01/
├── manifest.toml      the exact manifest used
├── manifest.sha256    hash, so a trace cannot be paired with the wrong manifest
├── trace.jsonl        the crossing records, append-only
└── artifacts/         every declared artifact, by content hash
```

That is the whole format. It is deliberately boring: a specimen should be readable with
`cat`, diffable in git, and openable by a tool that knows nothing about the producer.

## Why it is a first-class mode and not an export option

Three things become possible only when a run is a file:

**Review.** A referee asked to believe a figure can open the specimen, replay it, and see the
trace that produced it. This is what "reproducible" means in a form that fits in a
supplementary archive.

**Regression.** `seam specimen replay` against a new code version diffs the traces. An
affordance that flipped from `dial` to `sealed`, an OP whose pitch changed, an intervention
that was accepted before and is now rejected — all visible as a trace diff, none visible in a
test suite that only checks final numbers.

**Teaching.** The tutorial mode needs something to run against when the reader has no cluster
and no licence. A specimen is that something, and it is also why tutorials are durable.

## Replay semantics

```
seam specimen open specimens/epoch-laser-01
```

Replaying MUST:

1. Rebuild every binding from `manifest.toml` — the same widgets, the same domains, the same
   liveness badges.
2. Disable every control. A specimen accepts no writes.
3. Drive every gauge from the recorded `observe` records, advancing at the recorded pace or
   at `--fast`.
4. Keep `caused_by` links intact, so "jump to the intervention" lands on the sample that
   preceded it.

Replaying MUST NOT:

- Reconnect to a job, a network, or a scheduler.
- Recompute anything. A specimen that recomputes is a specimen that can disagree with itself.
- Accept an intervention "for demonstration". If the reader wants to explore, they run a
  live job or they fork the specimen into a scenario.

## The rendered pace

A specimen records wall-clock timestamps and its own job time. Replay has to pick one.

| Pace | Source | Use |
| :--- | :--- | :--- |
| `job` (default) | `job_time` | The sample sequence, without the wall-clock stalls. This is what a reader wants: the physics, not the queue. |
| `wall` | `at` | Reconstructs the experience, including the four minutes the code spent in initialisation. Useful for exactly one purpose: showing an agent's operator what a long job feels like. |
| `fast` | none | As fast as the renderer can consume. CI, diffing, and reading. |

Default is `job`, and this is a considered choice: replaying at wall speed makes a 40-minute
run unwatchable, and a specimen nobody watches is a file nobody opens.

## Trace diff

The operation that makes specimens worth keeping:

```
seam specimen diff specimens/epoch-laser-01 specimens/epoch-laser-02
```

Reports, in order of severity:

1. **Manifest differences.** A point added, removed, re-domained, or its affordance or
   liveness changed. A liveness change is a breaking change (SPEC §11.4).
2. **Shape differences.** An OP's `shape` or `pitch` changed. This breaks every stored
   scenario that referenced it.
3. **Outcome differences.** The same intervention accepted in one run and rejected in the
   other. Almost always a real behavioural change in the code.
4. **Numeric drift.** Same OP, same sequence position, different value. Reported with
   relative tolerance, and this is the only category where "expected" exists — everything
   above is a contract change, not a number change.

Categories 1–3 are contract diffs; category 4 is a physics diff. Conflating them is why
"regression test" for simulation codes usually means "compare one number at the end", which
catches almost nothing.

## Size discipline

A `per-step` OP on a long run produces a large trace. The rules:

- **Downsample the trace, declare the downsampling.** A `dissent`-class record at the head
  saying `{"note": "observe records decimated 1:100, kind=series"}`. Never silent.
- **Never downsample the sparse kinds.** `seal`, `intervene`, `transition`, `dissent` are few
  and each one is load-bearing.
- **Artifacts by content hash**, so two specimens that share a 200 MB snapshot store it once.

A specimen that is 40 MB is a specimen people keep. One that is 4 GB is a specimen people
delete, and then the tutorial stops working.

## Interaction logic

The specimen mode is the tutorial mode minus the writes, and the surface should make that
difference visible rather than merely factual:

- Every control renders in its disabled form with its recorded value.
- A banner states the run identity and the fact that nothing can be written.
- Interventions present in the trace are shown as **markers on the time axis**, not as
  buttons. The reader sees that a human stopped this run at step 1840, and can jump there.
- The `caused_by` link is a clickable edge: from an intervention marker to the sample that
  preceded it.

That last interaction is the one that makes the whole spec legible in ten seconds. A reader
who clicks an intervention and lands on the sample that caused it has understood the
difference between a tunnel and a seam without reading a word of this repository.
