# Playoff bracket source format

This document specifies the JSON "language" used to describe a football playoff
bracket. A document of this format is the single source of truth from which an SVG
diagram is rendered.

The canonical, machine-checkable definition is [`schema.json`](schema.json). This
prose document explains intent and the rules a renderer must implement.

## Top-level document

```jsonc
{
  "tournament": "Copa Libertadores", // required, string
  "season": "2026",                  // optional, string
  "format": "single-elimination",    // optional, default "single-elimination"
  "render": { "scores": "legs" },    // optional, display preferences (see below)
  "rounds": [ /* Round, ... */ ]      // required, ordered first round -> final
}
```

`rounds` are ordered from the earliest round to the final. The order is significant:
it determines the columns of the bracket, left to right.

## Render options

The optional top-level `render` object lets the document declare how it should be
displayed, so the same renderer serves different presentation choices without code
changes.

```jsonc
{
  "scores": "aggregate" // "aggregate" (default) | "legs"
}
```

- `"aggregate"` — each side shows a single total across all legs, e.g. `2`. A shootout
  is appended in parentheses, e.g. `1 (4)`.
- `"legs"` — each side shows the goals of every leg in order, e.g. `2 0`. A shootout is
  appended in parentheses on the relevant side, e.g. `0 0 (4)`.

In both modes the winning side is emphasized. For single-match ties (one leg) the two
modes render identically.

## Round

```jsonc
{
  "name": "Quarterfinals",   // required, display label
  "matches": [ /* Match, ... */ ]  // required
}
```

## Match

A match is one bracket node: two sides plus an optional result.

```jsonc
{
  "id": "qf1",            // required, unique within the document
  "ref": 84021,           // optional, id of the business match entity
  "home": { /* Slot */ }, // required
  "away": { /* Slot */ }, // required
  "legs": [ /* Leg, ... */ ], // optional; absent => not played yet
  "winner": "home"        // optional; overrides the computed winner
}
```

- `id` — internal identifier, referenced by `winner_of` (see Slot). Not a display
  value.
- `ref` — optional pointer to the real match entity in the host system's database.
  The renderer does not require it; it exists so a node can carry the link once the
  business match exists. A node can therefore mutate from a pure placeholder into a
  referenced, played match without any change to the language.

## Slot

A slot is one side of a match. It is exactly one of these shapes:

```jsonc
{ "team": "Flamengo", "id": 123, "seed": 1 } // a concrete team; id and seed optional
{ "winner_of": "qf1" }                       // placeholder: winner of another match
{ "tbd": true }                              // to be defined
```

Bracket connections are **explicit** through `winner_of`, which must reference the
`id` of another match in the document. References must not form a cycle.

## Leg

A single played game within a match. Two-legged ties have two legs.

```jsonc
{
  "home": 2,                       // required, goals by the match's home side
  "away": 1,                       // required, goals by the match's away side
  "pens": { "home": 4, "away": 2 } // optional, penalty shootout result
}
```

`home`/`away` in a leg always refer to the match's `home`/`away` sides, regardless of
which venue the leg was played at.

## Determining the winner

A renderer computes the winner of a played match as follows:

1. If an explicit `winner` field is present, use it.
2. Otherwise sum goals across all `legs`: `home_total` vs `away_total`.
3. If one total is greater, that side wins.
4. If totals are equal, the last leg that carries `pens` decides; higher `pens` wins.
5. If still tied (no `pens`), the match has no winner yet (treat as undecided).

The away-goals rule is intentionally **not** applied in this version.

A match with no `legs` is "not played yet" and has no winner.

## Rendering notes (non-normative)

- Layout is deterministic: rounds map to columns left-to-right; within the bracket,
  a match in round *n+1* is drawn vertically centered between the two matches it
  consumes (resolved via `winner_of`).
- A `winner_of` slot should display the resolved team name once that match has a
  winner, and the placeholder label (e.g. "Winner QF1") otherwise.
