# Instance Mapping — AstroNbodySim.jl

| | |
| :--- | :--- |
| Code | AstroNbodySim.jl on Julia 1.13.3 (`/opt/astro/AstroNbodySim.jl`) |
| Domain | stellar dynamics / galactic N-body (direct sum, tree, PM) |
| Exposure | Julia keyword-argument constructor over an immutable `Simulation` struct |
| Conformance | **L2** — `poststep` and `analysers` are callback channels by construction |
| Manifest | `seam-examples/manifests/astronbodysim.toml` |

## Why this mapping matters most

Of the four codes, this is the only one where the seam is **free**: the constructor already
takes a vector of callbacks, and the run loop already invokes them at every step.

```julia
Simulation(d;
    ...
    analysers = Dict{String, Function}(),   # run at analysis intervals
    poststep  = Function[],                 # run after every step
    Realtime  = false,                      # already has a live renderer
    ...
)
```

Two consequences, both important to the spec:

1. `perstep` liveness is available at **E1**, not E4. The signature declares the channel; its
   existence is structural evidence, not a behavioural claim. This is the cheapest legitimate
   `perstep` in any of the four mappings, and it is what a code author who *wanted* to be
   intervenable would build.
2. The code already ships a real-time visualiser (`Realtime`, `RenderTime`, `xlims`, `ylims`,
   `markersize`). Seam's job here is therefore not to add a UI — it is to **declare the
   surface the existing UI has**, so an agent can drive what a human already can. That is the
   cleanest possible statement of what the specification is for.

## The surface

### Interventions

| Point | Affordance | Liveness | Grade | Domain | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TimeEnd` | dial | sealed | imperative | `[0.001, 20]` Gyr | E1: `Simulation(; TimeEnd)` — immutable struct field |
| `TimeStep` | dial | sealed | imperative | `[0, 0.01]` Gyr, log | E1; `0.0` selects adaptive |
| `TimeBetweenSnapshots` | dial | sealed | imperative | `[1e-5, 1]` Gyr | E1 |
| `TreeOpenAngle` | dial | sealed | imperative | `[0.01, 1.0]` | E1 |
| `ErrTolAcc` | dial | sealed | imperative | `[0.001, 0.1]` log | E1 |
| `epsilon` | dial | sealed | imperative | `[0, 0.01]` kpc | E1 |
| `Nx` / `Ny` / `Nz` | dial | sealed | imperative | int `[8, 512]` | E1: PM mesh |
| `BoundaryCondition` | ratchet | sealed | imperative | `{Vacuum, Periodic, ...}` | E1 dispatch on type |
| `device` | ratchet | sealed | imperative | `{CPU, GPU}` | E1 dispatch on type |
| `Realtime` | ratchet | sealed | imperative | `{false, true}` | E1 |
| `RenderTime` | dial | sealed | imperative | `[0.05, 5]` s | E1; renderer interval |
| `output_on` | trigger | perstep | imperative | void | E1: push a closure onto `poststep` — no, see below |
| `snapshot` | trigger | perstep | imperative | void | E1: same channel |
| `stop` | trigger | midrun | imperative | void | E4: SIGTERM |

The `output_on` / `snapshot` pair deserves care. They are not constructor keywords; they are
*closures the seam runtime pushes into `poststep` before the run starts*. So their liveness is
`perstep` not because the constructor accepts them, but because the callback vector is a
channel and the closures are the writes. This is the one place in the four mappings where
"the write is a function" rather than "the write is a value", and it is the most interesting
derivation in the set:

> A `poststep` closure that reads a control file is an `imperative` `perstep` intervention
> whose payload is "do this thing at the next boundary". The affordance is still `trigger`,
> because from the operator's side it is a button with no value.

### Observations

| Point | Shape | Pitch | Source |
| :--- | :--- | :--- | :--- |
| `step` | scalar | per-step | `api:sim.timeinfo.step` |
| `time` | scalar | per-step | `api:sim.timeinfo.time` |
| `total_energy` | series | per-step | `api:analyze(sim)` |
| `positions` | table | per-step | `api:gather(sim, ...)` |
| `render_frame` | grid | per-second:0.2 | `api:sim.visinfo` |

The last row is the honest one: `Realtime` renders at `RenderTime` (default 0.2 s), not every
step. So the visualisation's pitch is wall-clock, while the physics' pitch is per-step. Two
different pitches over the same quantity. A manifest that collapses them will show a
visualisation that appears to skip steps, and an operator will conclude the physics skipped
them too.

## Immutability and the seal

`struct Simulation{D}` is immutable. Its fields cannot be assigned after construction. That is
E1 evidence of the strongest kind for `liveness: sealed` — not "the code does not read it
again", but "the language will not let you write it".

This is worth contrasting with Meep, where Python *permits* the assignment and the run is then
wrong. Julia's immutability is a better-designed surface, and the manifest for it is
correspondingly simpler: every `@kwdef`-style field is `sealed`, full stop, and only the
callback channels are live.

## Derivation trace

```
TimeEnd            dial      E1  kwargs       Simulation(; TimeEnd::Unitful.Time)
TimeStep           dial      E1  kwargs       Simulation(; TimeStep)
BoundaryCondition  ratchet   E1  dispatch     BoundaryCondition::Vacuum|Periodic
poststep           trigger   E1  channel      Simulation(; poststep::Vector{Function})
snapshot           trigger   E1  channel      Simulation(; analysers::Dict{String,Function})
render_frame       gauge     E1  visinfo      Realtime=true, RenderTime=0.2
stop               trigger   E4  signal       run:ans-stop-01
```

## Traps

**Unitful everywhere.** Every time-like keyword is a `Unitful` quantity: `0.1u"Gyr"`,
not `0.1`. A manifest that carries plain floats and a `unit` label is losing the type
information that the language is giving away for free. The adapter must convert, and the
manifest's `unit` must match the quantity actually passed.

**`TimeStep = 0.0` means adaptive.** A dial with a `0` stop is not a dial over a continuous
range: `0` is a distinct mode, not an infinitesimal step. It belongs as a `ratchet` over
`{adaptive, fixed}` plus a `dial` for the fixed value — or, if kept as one dial, the `0`
endpoint must be labelled "adaptive" in the binding. This is an apparent fifth affordance that
decomposes into two of the four, and it is the closest any of these four codes has come to
falsifying the closed set.

**`epsilon` is a softening length in kpc, not a tolerance.** It sits next to `ErrTolAcc`, which
*is* a tolerance, in the same keyword block. E3 (naming) would happily classify both as
"tolerance-like floats"; they differ by four orders of magnitude and by physical meaning.

**`pids` is a process list.** `pids = [1,2,3,4]` is a distribution choice, not a parameter.
Multi-element integer list → unresolved, not a dial.

**`device = GPU()` will fail on this machine.** Tesla P100 with CUDA is present, but the
package's GPU path requires `CUDA.jl` to be functional in the depot, which is a separate
condition from the GPU existing. The manifest declares the ratchet; the adapter must check and
reject at seal time rather than let the run fail ten minutes in.

## Profile justification

L2. Two `perstep` triggers (`snapshot`, `output_on`) and one `midrun` trigger (`stop`), all
with channels visible in the constructor signature at E1, plus E4 demonstration for `stop`.
Everything else is `sealed` by language-level immutability.

This is the mapping where Seam asks for the least and gets the most, which is the correct
outcome: the code was already built with a seam in it, and the specification only had to name
what was there.
