# Instance Mapping — EPOCH3

| | |
| :--- | :--- |
| Code | EPOCH3 (`/opt/epoch/epoch3d/bin/epoch3d`), deck-driven |
| Domain | laser–plasma interaction (PIC) |
| Exposure | text deck, `begin:<block>` … `end:<block>`, `key = value` |
| Conformance | **L1** — no mid-run channel exists; everything is `sealed` |
| Manifest | `seam-examples/manifests/epoch.toml` |

## The exposure

A deck is the cleanest parameter surface of the four, and the most misleading.

```ini
begin:control
  nx = 200
  t_end = 50 * femto
  x_min = -4 * micron
  x_max = -x_min
end:control

begin:boundaries
  bc_x_min = simple_laser
  bc_x_max = open
end:boundaries
```

Three structural facts fall out at E1, all of them load-bearing:

1. **Names are block-scoped.** `t_end` appears in both `begin:control` and `begin:laser` with
   different meanings (run end vs laser switch-off). A flat parameter namespace is a bug: two
   parameters, one name. The manifest must qualify — `control.t_end`, `laser.t_end` — or the
   surface will move the wrong one.
2. **Values are expressions, not literals.** `x_max = -x_min` refers to an earlier parameter;
   `t_profile = gauss(time,4*femto,4*femto)` calls a deck function. The value grammar is not
   `<number>`; it is an arithmetic expression over parameters and unit constants.
3. **Units are inline.** `50 * femto`, `-4 * micron`. The unit is part of the value and the
   deck's constant table is the only authority on what `femto` means.

## The surface

### Interventions (all `sealed`)

| Point | Affordance | Domain | Evidence |
| :--- | :--- | :--- | :--- |
| `control.nx` | dial | int `[16, 4096]`, log | E1 deck grammar; bounds E0 |
| `control.t_end` | dial | float `[1, 500]` fs | E1; unit from `femto` symbol |
| `control.x_min` | dial | float `[-100, -0.1]` µm | E1; `x_max` is derived, not independent |
| `boundaries.bc_x_min` | ratchet | enum | E1/E2: `open`, `simple_laser`, `reflect`, `periodic` |
| `boundaries.bc_x_max` | ratchet | enum | same |
| `laser.intensity_w_cm2` | dial | float `[1e10, 1e20]`, log | E1; log domain is E0 |
| `laser.lambda` | dial | float `[0.1, 10]` µm | E1 |
| `laser.t_end` | dial | float `[0, 500]` fs | E1; block-scoped, distinct from `control.t_end` |
| `laser.t_profile` | unresolved | — | E1 says "expression"; no finite domain. Correct answer is `unresolved` |
| `output.dt_snapshot` | dial | float `[0.1, 100]` fs | E1 |
| `output.ey` | ratchet | enum `{never, always, ...}` | E1 |
| `stop` | trigger | void | E4: SIGTERM; final state written |

`laser.t_profile` being unresolved is the honest outcome and the interesting one. It is a
function of `time` — a waveform. There is no closed form of dials for it, and pretending
otherwise by exposing three Gaussian parameters that the deck does not have would be
invention. It renders as a labelled read-only expression with its locator, so the operator can
see what waveform is in play.

### Observations

| Point | Shape | Pitch | Source |
| :--- | :--- | :--- | :--- |
| `step` | scalar | per-step | `stdout:^\s*(\d+)\s` |
| `time` | scalar | per-step | `stdout` |
| `total_energy` | series | per-step | `stdout:Total energy` |
| `ey` | grid | per-step | `file:S208_ey%04d.sdf` |
| `laser_absorbed` | series | per-step | `file:S208_*_laser_absorbed` |

EPOCH prints a step table to stdout and writes SDF dumps per `dt_snapshot`. The two have
different pitches — stdout every step, SDF per snapshot interval — and the manifest says so.
A renderer that assumes one pitch for both will show a grid that appears frozen for fifty
steps at a time.

## Why L1 and not L2

The deck is read once, at start-up, and parsed into a static configuration. There is no
control channel, no signal handler for parameter change, and no callback. So:

- every deck parameter is `liveness: sealed`;
- the only `midrun` intervention is `stop`, implemented as SIGTERM, and it terminates rather
  than modifies.

This is not a limitation to be worked around. It is the *finding*. An interface that offers a
live `nx` slider over EPOCH is offering a control that will do nothing, and the operator will
believe it. Declaring `sealed` is what makes the rest of the surface credible.

The one legitimate extension — sweep mode — is not a liveness feature. It is a *batch*
feature: submit N jobs with N values, and the seam shows an array of runs rather than a live
dial. That is a different manifest (a sweep wrapper), and the spec deliberately does not model
it in v0.1 (SPEC §11.2).

## Derivation trace

```
control.nx            dial      E1  deck-grammar  input.deck:2
control.t_end         dial      E1  deck-grammar  input.deck:5   unit=femto
boundaries.bc_x_min   ratchet   E1  symbolic      input.deck:11  (simple_laser|open|...)
laser.t_end           dial      E1  deck-grammar  input.deck:22  block-scoped!
laser.t_profile       unresolved E1 expression    input.deck:21
stop                  trigger   E4  signal-probe  run:epoch-stop-01
```

## Traps

**Block scoping.** The single highest-value E1 fact about EPOCH decks, and the one a
`grep '=' input.deck` harvest gets wrong. Two `t_end`s, two meanings.

**Expression values.** `x_max = -x_min` means `x_max` is not an independent parameter. A
surface that offers both as dials allows the operator to set an inconsistent box, and EPOCH
will either error or silently use one. Declare `x_max` as derived and read-only.

**Never `eval` a deck value.** `gauss(time,4*femto,4*femto)` is a function call in a namespace
you do not control. Parse the shape, or declare unresolved.

**Unit laundering.** `4 * micron` is 4 µm. If a renderer strips `* micron` and displays `4`
with a µm label, it is right by coincidence and becomes wrong by 10³ the first time the deck
uses `nano`. Parse the symbol through the deck's constant table.

**`bc_x_min` and the laser.** `simple_laser` as a boundary condition is only meaningful with a
matching `begin:laser` block. A ratchet over boundary conditions that hides this coupling lets
the operator pick `simple_laser` with `boundary = x_max`, which produces a run that starts and
does nothing. The manifest can express the coupling in `doc`; v0.1 has no first-class way to
declare it, which is a real gap.

## Profile justification

L1: rules 1, 2, 4, 5 satisfied; rule 3 satisfied trivially because every claimed liveness is
`sealed` and the one `midrun` trigger has an E4 witness. A conformant L1 with an entirely
sealed parameter space is a *better* document than an L2 with three decorative sliders.
