# Affordance

> Four kinds. Closed set. The widget is a consequence, not a decision.

## The claim

An agent asked to "build a GUI for this simulation" guesses. It puts a slider on a
parameter that cannot change after submission; a text box on a boolean; a plot on a
quantity nobody samples. The guesses are not random — they are pattern-matched from the
parameter's *name* and *type*, which is the weakest available evidence.

Seam replaces the guess with a decision over three declared facts:

```
writeability  ×  domain shape  ×  liveness   →   affordance
```

Three facts have a small product. Four affordances cover all of it. The mapping is
mechanical, which means it can be *audited* — and an audited guess is a derivation.

## The four

### `trigger` — discrete, atomic, no value

An action. `stop`, `checkpoint`, `dump`, `pause`, `resume`.

- Fires once per activation. Has no state of its own.
- Cannot be `sealed`: an action that only works before submission has no meaning.
- Binds to a button; projects to a zero-argument tool.
- **Recognition:** the thing is a verb, not a noun. Calling it changes something and
  returns nothing useful. In an API it is a method with side effects and no return; in a
  CLI it is a verb subcommand; in a deck it is a directive with no argument.

### `dial` — continuous, bounded

A quantity. `resolution`, `dt`, `t_end`, `softening`, `intensity`.

- Admitted values form an interval `[lo, hi]`, discretised by `step` or by `log`.
- Binds to a slider or spin box; projects to a number with bounds.
- **Recognition:** the value is numeric, the code compares it against thresholds, and two
  nearby values give two different behaviours. If a small change gives an identical run,
  it is not a dial — it is a `ratchet` wearing a float.

### `ratchet` — discrete, finite domain

A choice. `boundary=open`, `integrator=leapfrog`, `output_format=hdf5`, `comoving=on`.

- Admitted values are enumerable. An integer with three meaningful settings is a ratchet,
  not a dial, even if it is stored as an `int`.
- Binds to a segmented control, select, or checkbox; projects to an enum.
- **Recognition:** there is a switch statement, a lookup table, a `choices=` kwarg, or a
  docstring saying "must be one of". Booleans are ratchets with two positions — declaring a
  boolean as `dial` produces a slider with two stops, which is a UI crime with no upside.

### `gauge` — read-only

An observation. Everything in `[[observe]]`.

- Never interactive. Never written.
- Binds to a plot, readout, table, or thumbnail — chosen from `shape`, freely, by the
  renderer; projects to a read-only resource.
- **Recognition:** the code computes it and stores it; nothing reads it back in.

## Why closed

An open set of widget kinds is what makes GUI generation undecidable in practice. Every
framework has forty widgets, every parameter seems to want a different one, and the
decision has no right answer to check against.

Four kinds with a mechanical mapping gives three properties that matter:

1. **Totality.** Every value falls into exactly one kind, or is `unresolved`. There is no
   "it depends".
2. **Auditability.** A reviewer can ask of each affordance: *which evidence settled it, and
   is that evidence checkable?* A widget choice has no such question.
3. **Portability.** The affordance is the invariant; the binding is not. One manifest binds
   to a browser, a terminal, a Gradio app, and an MCP tool schema without change — because
   nothing in it names a widget.

## What to do when four is not enough

The set is closed by rule, so a value that seems to need a fifth kind must be resolved one
of two ways.

**Decompose.** A "range slider" is two dials. A "file picker" is a ratchet over admissible
paths, or a dial over an index. A "colour" is three dials or a ratchet over a palette. In
practice every apparent fifth kind has decomposed so far.

**Mark unresolved.** If it will not decompose, it is `unresolved`, it renders as a labelled
read-only value with its provenance, and it is never guessed. The presence of `unresolved`
points is a signal to the code's author, and hiding it destroys the signal.

The falsifier for the closed set is a real parameter surface that needs a fifth primitive.
Four codes across two physics domains and four different exposure mechanisms (Python
object, text deck, tag-value paramfile, Julia struct) have not produced one. That is weak
evidence that four is right, and it is the only evidence available.

## Affordance is not binding

| Affordance | Browser | Terminal | Gradio | Agent |
| :--- | :--- | :--- | :--- | :--- |
| `trigger` | `<button>` | `[k]` keypress | `gr.Button` | `tool()` |
| `dial` | `<input type=range>` | `/set name=value` | `gr.Slider` | `tool(x: float)` |
| `ratchet` | `<select>` | `/set name=label` | `gr.Radio` | `tool(x: Enum)` |
| `gauge` | `<canvas>` | sparkline in ANSI | `gr.Plot` | resource |

A binding may add nothing to the affordance. It may not clamp wider than `[lo, hi]`, may
not offer options outside the domain, and may not make a `gauge` writable. Bindings differ;
admission does not.

## Anti-patterns

**Affordance by type.** `float → slider`, `int → number`, `bool → checkbox`, `str → text`.
This is the type-driven mapping and it is wrong on the two cases that matter most: a float
enum (silently becomes a slider over three values, and intermediate values make the code
throw) and an int that cannot change after submission (becomes a live control that does
nothing).

**Affordance by name.** `resolution` sounds like a dial, so it is declared a dial — but in
a spectral code it may legitimately be `sealed` while looking exactly like something you
would slide. Name is E3 evidence: it corroborates, it never settles.

**Affordance by ambition.** "It would be nice if the user could change this during the
run." Nice, and false, and the interface now lies. `liveness` comes from the code, not from
what would be pleasant.
