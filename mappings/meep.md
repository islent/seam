# Instance Mapping — Meep 1.33

| | |
| :--- | :--- |
| Code | Meep 1.33.0-beta (`/opt/conda/envs/mp/bin/python`) |
| Domain | computational electromagnetics (FDTD) |
| Exposure | in-process Python object |
| Conformance | **L2** — one class of `midrun` intervention is demonstrable |
| Manifest | `seam-examples/manifests/meep.toml` |

## Why this mapping matters

Meep is the case where a naive surface looks most plausible and is most wrong. The API is a
Python constructor with two dozen keyword arguments, which invites the reflex "each argument
is a slider". In fact the entire grid is built at construction and almost nothing can be
changed afterwards — but the *run loop* is Python you control, which means some things can.

Meep is therefore the best demonstration that `liveness` is not derivable from the exposure
type. It has to be derived per parameter.

## The surface

### Interventions

| Point | Affordance | Liveness | Grade | Evidence | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `resolution` | dial | sealed | imperative | E1 `meep.Simulation.__init__` | Yee grid built from it; `[8, 200]` is E0 |
| `until` | dial | midrun | imperative | E4 | `sim.run(until)` may be called again to continue — this is a real mid-run write |
| `Courant` | dial | sealed | imperative | E1 `Simulation(Courant=...)` | stability factor; changing it mid-run invalidates the integrator |
| `eps_averaging` | ratchet | sealed | imperative | E1 signature | two-position |
| `force_complex_fields` | ratchet | sealed | imperative | E1 signature | two-position |
| `boundary` | ratchet | sealed | imperative | E1 docstring enum | `open`, `periodic`, `PML`, `metal`, ... |
| `pml_thickness` | dial | sealed | imperative | E1 `PML(thickness=)` | construction of `BoundaryLayer` |
| `dimensions` | ratchet | sealed | imperative | E1 signature | `1/2/3` — and it changes the whole geometry type |
| `dump_slice` | trigger | perstep | imperative | E4 | writes the full `Ez` array from the step callback |
| `stream_frames` | trigger | perstep | imperative | E4 | turns on per-step reduced frames — the only live preview among the four codes (§4.6) |
| `stop` | trigger | midrun | imperative | E1 `mp.stop_when_*` / exception | sets a flag read by the step loop |
| `n_steps` | unresolved | — | — | E3 name | Meep has no step count; `until` and `dt` are the real parameters |

`n_steps` is deliberately unresolved and stays in the manifest as a labelled value. Meep's
"steps" are structured-grid steps, and `until` is the parameter that controls how many happen.
Declaring `n_steps` a dial because the name sounds like one is the canonical E3 error.

### Observations

| Point | Shape | Pitch | Source | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `sim_time` | scalar | per-step | `api:sim.meep_time()` | E1 |
| `flux_incident` | series | per-step | `api:mp.get_fluxes(refl)` | E1 |
| `flux_transmitted` | series | per-step | `api:mp.get_fluxes(tran)` | E1 |
| `energy` | series | per-step | `api:mp.dft_ldos` / field energy | E2 |
| `Ez_slice` | grid | on-demand | `file:slice.npy` | E1 | `preview: max_width=120, diverging` |
| `Ez_frame` | grid | per-step | `file:frame.npy` | E4 | `preview: max_width=120`; box-averaged 2×2 in the callback |
| `eps` | grid | on-demand | `file:eps-000000.00.h5` | E1 |

`Ez_slice` is `on-demand` and that is the important declaration. A 200×200 slice at `per-step`
on a 10⁴-step run is 4×10⁸ samples; a renderer that promises to keep them is lying. `on-demand`
plus a `dump_slice` trigger is the honest pair.

## The midrun case, worked

Meep is the one code here where a `midrun` parameter change is real, and it is worth showing
because it is the exception that validates the rule.

```python
# the channel is the callback: Meep calls it every `at_every` of sim time
def seam_tick(sim):
    cmd = read_control_file()          # written by the seam runtime, atomically
    if cmd.get("until") is not None:
        # legitimate: extending a run is a documented Meep pattern
        sim.until = cmd["until"]
    if cmd.get("dump_slice"):
        sim.output_field_to_hdf5("slice", mp.Ez)
    if cmd.get("stop"):
        raise SeamStop()

sim.run(mp.at_every(0.5, seam_tick), until=start_until)
```

Note what is *not* in that list: `resolution`, `Courant`, `boundary`, `dimensions`. They are
`sealed`, not because Meep forbids the assignment (Python will let you) but because assigning
them produces a run whose grid and integrator disagree. **The ability to write is not
liveness.** This distinction is the reason §4.3 exists.

## Derivation trace

```
resolution     dial        E1  meep.Simulation.__init__(resolution: int)
                            E0  bounds [8,200] from the tuning guidance
boundary       ratchet     E1  meep.Simulation.__init__(boundary: str) + docstring enum
dump_slice     trigger     E1  sim.output_field_to_hdf5 present  → E4 demonstrated
until          dial        E1  meep.Simulation.run(until: float)
                            E4  run:meep-extend-01 (extended 40→60, run continued)
n_steps        unresolved  E3  name only; no such parameter in the API
```

## Traps

**`resolution` is not on the constructor.** It is on `mp.GridVolumes` / the `Simulation`
signature depending on version, and a signature harvest of `Simulation` may miss it. Read the
source when the signature is thin (PROBES §1.1).

**Complex fields.** `force_complex_fields = True` changes every field array's dtype. An OP
declared `series` on a real field becomes `series` of complex numbers, and a renderer that
plots the real part will look correct and be wrong. Declare the dtype in `doc`.

**`until` is not a step count.** `until` is in Meep time units (`a/c`). A surface that labels
it "steps" is wrong by a factor of the resolution and the Courant number simultaneously.

**The raw sample is not the field.** `get_array(mp.Ez)` on a driven point source returns a
160×160 array whose adjacent cells alternate sign: the grid-scale (Nyquist) mode of the Yee
lattice, which has zero group velocity and no physical meaning. Rendered at native resolution it
reads as an entire lattice of fine structure. 2×2 box averaging cancels it exactly — which is why
SPEC §4.6 makes the *producer* reduce, to a width the manifest declared. Stride-sampling instead
of averaging preserves the mode and is the bug this paragraph exists to prevent.

**Two independent monitors.** `add_flux` regions must be added before the run starts; adding
one mid-run is not meaningful. So `flux_*` are `per-step` observations but their *regions* are
`sealed` — an observation can be sealed in its configuration while being live in its samples.
The manifest expresses this by declaring the region as a sealed parameter and the flux as an
observation.

## Profile justification

L2 is claimed on the strength of two demonstrated `midrun` writes (`until`, `dump_slice`) with
E4 witnesses. Every other IP is `sealed`. A manifest where eleven of twelve parameters are
sealed and one is genuinely live is a *more* useful document than one where everything appears
live and nothing is.
