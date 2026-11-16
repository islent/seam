# Instance Mapping — Gadget-2

| | |
| :--- | :--- |
| Code | Gadget-2.0.7 (`/opt/gadget2/bin/Gadget2_*`), tag-value paramfile |
| Domain | cosmological / galactic N-body, TreePM |
| Exposure | parameter file, `Tag<whitespace>Value`, read by `sscanf("%s%s%s")` |
| Conformance | **L1** |
| Manifest | `seam-examples/manifests/gadget2.toml` |

## The exposure, and the trap that defines it

Gadget-2's parameter file looks like a key-value file and is not one:

```c
/* param.c */
if(sscanf(buf, "%s%s%s", buf1, buf2, buf3) < 2) continue;
```

A line is `Tag<whitespace>Value`. Writing `Tag = Value` — the Gadget-3/4 style, and what most
online examples show — makes `=` the *value*. `OutputDir = out` stores the literal string `=`,
every subsequent `strcpy` inherits it, and the run fails with
`cp: cannot create regular file '=/parameters-usedvalues'`.

This is the highest-value E1 fact in the whole file, and it is **not visible in the
paramfile**. It is only visible in the reader. An agent that harvests the paramfile as
`key=value` gets a grammatically valid manifest over a format the code cannot read.

It is also the best available illustration of the ladder's central claim: the exposure's
*appearance* is worth nothing, the exposure's *reader* is worth everything.

## The surface

### Interventions (all `sealed`)

| Point | Affordance | Domain | Unit | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `TimeMax` | dial | float `[0, 20]` | Gyr × 0.9778 | E1 paramfile-grammar; see unit trap |
| `TimeBetSnapshot` | dial | float `[0.01, 2]` | Gyr × 0.9778 | E1 |
| `Nmesh` | ratchet | enum `{32, 64, 128, 256, 512}` | — | E1: powers of two required by FFT |
| `SofteningHalo` | dial | float `[0.1, 20]` | kpc | E1; log domain is E0 |
| `BoxSize` | dial | float `[10, 1000]` | kpc | E1; must contain the IC |
| `Omega0` | dial | float `[0.05, 1]` | — | E1 |
| `OmegaLambda` | dial | float `[0, 1]` | — | E1; must satisfy `Omega0+OmegaLambda≈1` |
| `HubbleParam` | dial | float `[0.4, 1.0]` | — | E1 |
| `ComovingIntegrationOn` | ratchet | `{0, 1}` | — | E1; **changes the meaning of `TimeMax`** |
| `NumFilesPerSnapshot` | dial | int `[1, 512]` | — | E1 |
| `ICFormat` / `SnapFormat` | ratchet | `{1, 2, 3}` | — | E1: 1=Fortran binary, 2=HDF5, 3=HDF5+padding |
| `OutputListFilename` | unresolved | — | — | path; no finite domain |
| `stop` | trigger | void | — | E4: SIGTERM, with a final `energy.txt` flush |

`OutputListFilename` is a path and is therefore unresolved. A text box over a filesystem path
is not an affordance: it cannot be validated, and an agent projection over it has no schema an
agent can rely on.

### Observations

| Point | Shape | Pitch | Source |
| :--- | :--- | :--- | :--- |
| `time` | scalar | per-step | `stdout` |
| `step` | scalar | per-step | `stdout` |
| `energy_kin` | series | per-step | `file:output/energy.txt` |
| `energy_pot` | series | per-step | `file:output/energy.txt` (needs `-DOUTPUTPOTENTIAL`) |
| `a` | series | per-step | `file:output/energy.txt` |
| `snapshot` | grid | per-step | `file:output/snap_%03d.hdf5` |

## The unit trap, in full

The parameter block declares its unit system:

```
UnitLength_in_cm        3.085678e21
UnitMass_in_g           1.989e43
UnitVelocity_in_cm_per_s 1e5
```

The code's time unit is therefore

```
UnitLength / UnitVelocity = 3.0857e16 s = 0.9778 Gyr    (not 1 Gyr)
```

So `TimeMax = 1.0` evolves 0.978 Gyr, and to evolve 6 Gyr you need `TimeMax = 6.135`. This is
a 2.2 % error: small enough to survive review, large enough to invalidate a comparison between
two codes.

Seam's response is `display_scale`:

```toml
[[param]]
name     = "TimeMax"
unit     = "Gyr"
display_scale = 0.9778      # Gyr per code time unit
```

The operator types Gyr, the adapter writes code time. The manifest says the factor is a
declared quantity rather than an implicit assumption, which means a reviewer can check it.

Note the second-order trap: `ComovingIntegrationOn` changes what `TimeMax` *means* (expansion
factor vs physical time). Two parameters that interact this way cannot both be dials with
independent meaning, and if the operator changes `ComovingIntegrationOn` after setting
`TimeMax`, the intent is ambiguous. The manifest expresses this in `doc`; v0.1 has no
first-class way to declare interaction, which is a genuine gap and a candidate for v0.2.

## Why L1

The paramfile is read once, in `read_parameter_file()`, before any integration. There is no
channel, no callback, no re-read. Every parameter is `sealed`, and the only `midrun`
intervention is SIGTERM.

An additional honesty note: SIGTERM on Gadget-2 with `ResubmitOn = 0` triggers a restart-file
rename that fails with `mv: cannot stat 'output/restart.N'` — harmless, but it means the trace
of a `stop` intervention will contain a stderr line that looks like an error. The adapter
should record it as a `dissent` with a note, so that a reviewer does not spend an hour on it.

## Derivation trace

```
TimeMax               dial     E1  paramfile-grammar  param.txt:14
                      E2  README: "TimeMax = 1.0 → 0.978 Gyr"  → display_scale
Nmesh                 ratchet  E1  powers-of-two FFT constraint (README)
ComovingIntegrationOn ratchet  E1  paramfile  (0|1)
OutputListFilename    unresolved E1 path — no finite domain
stop                  trigger  E4  run:g2-stop-01
```

## Traps

**`=` in the paramfile.** Destroys the run, silently, with an error message three steps later
in a different directory.

**Unit time is not a round number.** See above. The code's own docs and most papers assume
1 Gyr; the build in use does not.

**`Nmesh` is not a free integer.** The PM solver needs a power of two and the FFTW2 build is
single precision. A dial from 1 to 1000 lets the operator pick 200, which is a power of two
times 25 and will either round or crash depending on build flags.

**`energy.txt`'s `EnergyPot` column is zero without `-DOUTPUTPOTENTIAL`.** A compile-time
flag, invisible at runtime, produces a plausible-looking file with a silent zero column. An OP
declared over that column will report zero energy forever and look like physics. The adapter
should check whether the column is identically zero across the first ten rows and emit a
`dissent` if so — this is exactly the kind of check that a crossing trace makes possible and a
final-number comparison does not.

**`mv: cannot stat 'output/restart.N'`** at every normal exit. Harmless; recorded as a
`dissent` so it does not read as a failure.

## Profile justification

L1. All liveness `sealed`, one demonstrated trigger. Four compile-time traps documented, three
of which are declared in the manifest as `notes` entries so that a reader of the manifest alone
learns them without reading this file.
