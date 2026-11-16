# Observation Point

> A declared place on the seam where state may be read, at a declared rate.

An OP is the unit of *seeing*. It answers three questions before anyone asks them: what is
this, what shape is it, and how often is it true?

## Fields

| Field | Required | Meaning |
| :--- | :--- | :--- |
| `name` | yes | Stable identifier. Unique in the manifest. Used verbatim in the agent projection, so it must survive being a tool name: `[a-z0-9_]+`. |
| `shape` | yes | Rank of the quantity: `scalar`, `series`, `grid`, `table`, `log`. |
| `pitch` | yes | `per-step`, `per-second:<n>`, `on-demand`. |
| `source` | yes | `stdout:<regex>`, `file:<path>`, `api:<callable>`, `metric:<key>`. |
| `unit` | recommended | Physical or dimensionless unit, as a string. Never parsed for arithmetic; parsed only for display and for unit-mismatch warnings. |
| `doc` | optional | One sentence for a human. |
| `provenance` | yes | Which evidence established shape and pitch, and where. |

## Shape is rank, not drawing

The single most common modelling error is to name an OP after the way it should be drawn.
`flux_plot`, `density_map`, `energy_curve` — these bake a rendering decision into a data
declaration, and then a terminal renderer cannot consume them.

Rank instead:

| Shape | Rank | Typical renderings |
| :--- | :--- | :--- |
| `scalar` | 0 | readout, sparkline endpoint, badge |
| `series` | 1 | line, bars, table column |
| `grid` | 2 | heatmap, contour, thumbnail, slice viewer |
| `table` | 2 (heterogeneous) | grid widget, CSV viewer |
| `log` | 1 (text) | tail, filtered stream |

A `series` of length one is a `series`, not a `scalar`: the distinction is what the
producer promises to keep producing, not what it has produced so far. A run that has
emitted one sample and will emit a thousand is a `series` with one sample, and a renderer
that shows it as a number will have to change its mind.

## Pitch is a promise

`pitch` states the interval at which the producer guarantees the value is current. It is a
contract in both directions:

- A consumer that polls **faster** than `pitch` is reading a value the job never promised
  to update. It will see repeats, and if it treats repeats as data it will draw a
  staircase and call it a plateau.
- A consumer that polls **slower** than `pitch` has a gap. It MUST mark the gap. It MUST
  NOT interpolate: interpolation across an unobserved interval is fabrication, and in a
  monitoring surface it is fabrication that looks like smoothness.

`on-demand` exists for expensive quantities — a full 3D field, a particle dump. An
`on-demand` OP is not sampled by the crossing loop; it is fetched when asked, and each
fetch is its own crossing record. Declaring an expensive quantity `per-step` is the most
reliable way to make a run unusable.

## Source

`source` says where the value comes from, in a form a third party can check:

```toml
source = "stdout:^\\s*Step\\s+(\\d+)"      # EPOCH progress line
source = "file:output/snap_%03d.hdf5"      # Gadget-2 snapshot series
source = "api:sim.get_array(component=meep.Ez)"  # Meep field slice
source = "metric:energy_total"             # adapter-defined derived metric
```

`file:` sources are also declared as `[[artifact]]` when the file's *existence* is a
lifecycle fact. The rule of thumb: if a renderer needs to distinguish "not yet produced"
from "produced and empty", declare an artifact.

## Example

```toml
[[observe]]
name = "energy_kin"
shape = "series"
pitch = "per-step"
unit = "code"
source = "stdout:^Energy:\\s+kin=(\\S+)"
doc = "Total kinetic energy, one sample per output step."
provenance = { grade = "E2", evidence = "docstring", witness = "gadget2:README.md#energy.txt" }
```

## Anti-patterns

**The aggregate as OP.** Declaring `max_field` as an OP because it is cheap to compute, and
never declaring the field it came from. The aggregate answers a question nobody asked and
forecloses the one they did. Declare the field as `on-demand` and the aggregate as
`per-step` if both are wanted.

**The implicit pitch.** Leaving pitch out and letting the consumer decide. This is how two
dashboards of the same run end up disagreeing about where a peak is.

**The mutable name.** Renaming an OP between runs. Crossing traces reference OPs by name;
a rename silently invalidates every stored scenario and specimen.
