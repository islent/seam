# Probe Recipes

> Concrete procedures for extracting E1–E4 evidence from each kind of exposure.

Each recipe says: what to run, what comes back, which field it settles, and where it lies.

---

## 1. Python API (Meep, FEniCS, in-process codes)

### 1.1 Signature harvest — E1

```python
import inspect, ast, textwrap

def harvest(obj):
    sig = inspect.signature(obj)
    for name, p in sig.parameters.items():
        yield {
            "name": name,
            "type": None if p.annotation is inspect._empty else str(p.annotation),
            "default": None if p.default is inspect._empty else p.default,
            "kind": str(p.kind),
        }
```

Settles: `name`, `type`, `default`. Corroborates `domain shape`.

**Where it lies.** `meep.Simulation` does not take `resolution` as a keyword — it takes
`cell_size`, and `resolution` appears in `mp.GridVolumes`. A signature harvest of the
constructor returns nothing for `resolution`, and an agent that concludes "resolution is not
a parameter" is wrong. Signature harvesting finds the *obvious* parameters; it does not find
the ones the code passes around internally.

### 1.2 Source harvest — E1, higher yield

When the signature is thin, read the source. `ast` gives the assignment sites:

```python
import ast, pathlib
src = pathlib.Path("meep/__init__.py").read_text()
tree = ast.parse(src)
# find every assignment of the form self.X = <expr> inside __init__, and every
# keyword in a call to the grid constructor
```

Settles: which parameters reach the grid/stepper (i.e. are read-once → `sealed`), and which
are re-read in the step loop (→ possible `midrun`). This is the E1 route to `liveness` for
in-process codes, and it is cheaper and more reliable than a probe run.

### 1.3 Output-surface harvest — E1

Step functions and their print/return statements:

```python
# grep-equivalent: every call to a function whose name starts with "display" / "output" /
# "get_" inside the step loop; every print() with a numeric format
```

Settles: `shape` and `pitch` for OPs. A quantity printed inside the step loop is
`per-step`; one printed after the loop is `scalar`.

### 1.4 Live-control probe — E4

Only for in-process codes, and only to establish `midrun`.

```python
# 1. create a control file the step callback polls
# 2. run to step 50, write a new value, record the step at which the next sample changes
# 3. if the change is visible at the very next sample  → liveness = midrun
#    if visible only at a declared boundary            → liveness = perstep
#    if never visible                                  → liveness = sealed, grade = advisory
```

The third outcome is the common one for codes not written to be interrupted, and it is a
perfectly good result. It is also the outcome that prevents a decorative slider.

---

## 2. CLI with argparse

### 2.1 Schema dump — E1

Do not scrape `--help`. Ask the parser:

```python
import runpy, sys
mod = runpy.run_path("mysim.py", run_name="__not_main__")
parser = mod["build_parser"]()          # if the parser is reachable
for a in parser._actions:
    print(a.dest, a.type, a.default, a.choices, a.nargs, a.help)
```

Settles everything: `type` → dtype, `choices` → `ratchet`, `default`, `help` → E2.

**Where it lies.** `parser._actions` is private API and will change. It is still better than
parsing `--help`, because `--help` renders through a formatter that line-wraps, and a
wrapped `(default: 0.5, choices: ...)` is a parsing hazard that produces silently wrong
defaults.

When the parser is not reachable (built inline in `__main__`), use `ast` on the
`add_argument` calls — still E1, less reliable, but structural:

```python
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_argument":
        flags = [a.value for a in node.args if isinstance(a, ast.Constant)]
        kwargs = {k.arg: ast.unparse(k.value) for k in node.keywords}
```

### 2.2 Usage string — E2

`--help` output is E2 by definition. Use it when there is no parser object. Extract
`choices` from the `{a,b,c}` metavar form and defaults from `(default: X)`.

**Where it lies.** `--help` frequently omits defaults that are set in `defaults = {...}`
dicts elsewhere in the source, so an absent default in the help text does not mean the
parameter has no default.

---

## 3. Text deck (EPOCH)

### 3.1 Grammar harvest — E1

Decks are structured: `begin:<block>` … `end:<block>`, `key = value` lines, comment `#`.

```python
import re, pathlib
BLOCK = re.compile(r"^\s*(begin|end):(\w+)")
KV    = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*(?:#.*)?$")

def harvest(path):
    block = None
    for lineno, line in enumerate(pathlib.Path(path).read_text().splitlines(), 1):
        if m := BLOCK.match(line): block = m.group(2); continue
        if m := KV.match(line) and block:
            yield {"block": block, "name": m.group(1), "value": m.group(2), "witness": f"{path}:{lineno}"}
```

Settles: `name`, `default` (the deck's value *is* the default), `block` (which is a hint at
liveness: `control` and `boundaries` are read once → `sealed`).

### 3.2 Value grammar — E1/E3

The deck's values carry units as arithmetic: `t_end = 50 * femto`, `x_min = -4 * micron`.
That is E1 evidence for `unit`, and it is the single most valuable thing to extract — a
surface that drops `* micron` turns a 4 μm domain into a 4 m domain.

Expression evaluation is **not** permitted: never `eval()` a deck value. Parse the shape
(`<number> * <unit-symbol>`, `<number>`, `true|false`, `bare_identifier`), map the symbol
through the code's own constant table if you can read it, and otherwise declare the unit as
a string and stop.

### 3.3 Block semantics — E2

The deck's own comments describe intent: `# Final time of simulation`. Use them for `doc`,
never for bounds.

### 3.4 The read-once fact — E1 architecture

EPOCH reads the deck at start-up and never again. No hook reads it mid-run. Therefore every
deck parameter is `liveness: sealed`, and that conclusion requires **no probe** — it is
E1-grade knowledge from the architecture. Declaring a mid-run control for a deck parameter
is the canonical Seam violation.

---

## 4. Tag-value paramfile (Gadget-2)

### 4.1 Grammar harvest — E1

The grammar is defined by the reader's format string, not by the file's appearance. Read
both:

```c
/* param.c */
if(sscanf(buf, "%s%s%s", buf1, buf2, buf3) < 2) continue;
/* so a line is  Tag<whitespace>Value  — and "Tag = Value" makes "=" the value */
```

This is the highest-value E1 fact about Gadget-2 and it is *not* visible in the paramfile
itself: the file looks like it accepts `=` and it does not. An agent that writes
`OutputDir = out` produces a run whose output goes to a directory named `=`.

Settles: the grammar (tag, whitespace, value), the tag list (from `read_parameter_file`'s
`strcmp` chain), and `dtype` per tag (`atoi` → int, `atof` → float, `strcpy` → string).

### 4.2 The dtype from the reader — E1

```python
# For each tag, find its handler: atoi/atof/strcpy. That is the dtype, definitively.
# The paramfile's own appearance ("1.0" vs "1") is not evidence: atof("1") == 1.0.
```

### 4.3 Units — E2, and a trap worth its own field

The paramfile declares `UnitLength_in_cm`, `UnitMass_in_g`, `UnitVelocity_in_cm_per_s`. The
code's time unit is `UnitLength/UnitVelocity`, which for the standard kpc/1e10 Msun/km/s
choice is **0.978 Gyr, not 1 Gyr**. An interface that labels `TimeMax` as "Gyr" and does no
conversion produces runs that are 2.2 % short — and 2.2 % is small enough to survive review
and large enough to invalidate a comparison.

Rule: **if a paramfile declares its own unit system, any interface over it must compute the
derived unit rather than assume it.** `unit` in the manifest is a string for display; the
conversion factor belongs in the adapter, and the manifest should say so:

```toml
[[param]]
name = "TimeMax"
unit = "Gyr"
display_scale = 0.9778   # Gyr per code time unit, derived from the paramfile's unit block
```

---

## 5. Julia `@kwdef` struct (AstroNbodySim.jl)

### 5.1 Field harvest — E1

```julia
using AstroNbodySim
# fields, their types, and their defaults
for f in fieldnames(Simulation)
    T = fieldtype(Simulation, f)
    d = hasfield(...) # defaults live in the generated kwarg constructor
end
```

More reliable than reflection over defaults: read the `@kwdef` block in the source with a
text harvest. The struct declaration is the schema, and it is static:

```julia
@kwdef struct Simulation
    N::Int = 20000
    t_end::Float64 = 1.0
    ...
end
```

Settles: `name`, `dtype` (from the field type), `default` (from the `=` in the block),
`doc` (from the `"""` immediately above the field, if present).

### 5.2 Type-based domain hints — E1/E3

Julia's type system often encodes the domain: `Union{...}` or an `@enum` is a `ratchet`;
`Float64` with a nearby `@assert` or `clamp` is a `dial` with bounds; `Bool` is a 2-ratchet.
`@enum` is the strongest E1 signal available in any of the four exposure types — it is a
declared finite domain, not an inferred one.

### 5.3 Step-boundary callbacks — E1 → `perstep`

If the integration loop accepts a callback (a `callback` kwarg, an `@info` hook, a
`step_hook`), then `perstep` liveness is available *by construction* — the callback is the
channel. This is the cheapest `perstep` in any of the four codes, and it is E1 evidence
because the signature declares the channel exists.

---

## 6. What none of these tell you

Every recipe above stops short of the two questions that matter most, and it is worth being
explicit:

**Whether a write takes effect.** Only E4 answers this. A code can accept a keyword, store
it, and never read it again. Nothing in the source structure reveals that; only a run does.

**Whether an affordance is the right one for the domain.** Derivation establishes what the
code accepts. It cannot establish that `t_end = 50 fs` is a physically sensible default.
That is the author's E0 contribution, and no amount of structural evidence replaces it.

The honest division of labour: **machine derives the shape, author supplies the meaning,
and the trace records which was which.**
