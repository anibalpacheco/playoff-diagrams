# CLAUDE.md

Guidance for working in this repository.

## What this project is

A small library that renders a **football (soccer) playoff bracket** as an **SVG**,
on the fly, from a **JSON source document**.

The motivating use case: on a results website, the bracket source text lives in a
field of the *championship* entity in the database. When results are updated, only
that JSON field changes — never the code, and no per-cup HTML templates are
maintained. The renderer turns the JSON into an SVG deterministically.

## Core decisions (already made — do not relitigate without reason)

- **Source format: JSON** (e.g. Postgres `JSONB`). Chosen over a custom DSL and over
  Graphviz `.dot` because of native database support and because a bracket node can
  evolve from a *placeholder* into a *reference to a business match entity* without
  changing the language. See `spec/format.md`.
- **Implementation language: Python.**
- **Bracket connections are explicit** via `winner_of`, not implicit by position.
- **Layout is deterministic** — geometry of the bracket tree is computed in code.
  No external layout engine (no Graphviz), no heavy dependencies. SVG is emitted
  directly as a string.
- **Winner is computed by default**: aggregate of `legs`; on a tie, `pens` decides;
  an optional explicit `winner` field overrides. No away-goals rule in the MVP.
- **Display preferences live in the document**, under a top-level `render` object
  (e.g. `{"scores": "aggregate" | "legs"}`), so presentation changes need no code
  change. Add new presentation knobs there.
- **Key naming: `snake_case`** in the JSON, for affinity with the Python backend.
- **Scope (MVP): single-elimination**, supporting single matches and two-legged ties
  with penalty shootouts. NOT yet: group stages, double elimination, away-goals rule.

## Language / spec

The authoritative description of the JSON "language" is **`spec/format.md`**, with a
machine-checkable **`spec/schema.json`** (JSON Schema) and worked examples under
**`examples/`**. If you change the language, update all three together.

## Layout (planned package structure)

```
src/playoff_diagrams/
  model.py      # data models (parsed representation of the JSON)
  parse.py      # JSON -> validated model
  layout.py     # deterministic bracket geometry
  render.py     # model -> SVG string
tests/
  test_render.py  # golden/snapshot SVG tests
  golden/*.svg
```

## Testing

The only executable code is the renderer plus **diagram-generation tests**, done as
**golden (snapshot) tests**: generate the SVG for each example and compare against a
versioned reference SVG. This catches visual regressions without a browser.

When SVG output legitimately changes, regenerate the golden files and review the diff.

## Conventions

- The codebase, identifiers, comments, docs and commit messages are **all in English**.
- Keep dependencies minimal; prefer the standard library.
