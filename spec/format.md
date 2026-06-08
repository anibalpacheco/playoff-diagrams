# Playoff bracket source format

This document specifies the JSON "language" used to describe a football playoff
bracket. A document of this format is the single source of truth from which an SVG
diagram is rendered.

The canonical, machine-checkable definition is [`schema.json`](schema.json). This
prose document explains intent and the rules a renderer must implement.

## Top-level document

```jsonc
{
  "tournament": "Copa Libertadores", // optional, string (may be supplied dynamically)
  "season": "2026",                  // optional, string (may be supplied dynamically)
  "format": "single-elimination",    // optional, default "single-elimination"
  "render": { "scores": "legs" },    // optional, display preferences (see below)
  "rounds": [ /* Round, ... */ ]      // required, ordered first round -> final
}
```

`rounds` are ordered from the earliest round to the final. The order is significant:
it determines the columns of the bracket, left to right.

`tournament` and `season` are optional in the document because a host system may want
to supply them dynamically at render time (e.g. from the championship entity) rather
than store them in the JSON. See "Host integration" below.

## Render options

The optional top-level `render` object lets the document declare how it should be
displayed, so the same renderer serves different presentation choices without code
changes.

```jsonc
{
  "scores": "aggregate",  // "aggregate" (default) | "legs"
  "max_label_chars": 22,  // optional, longest team label before it is truncated
  "box_width": 190        // optional, width of every match box in SVG units
}
```

- `"scores"`:
  - `"aggregate"` — each side shows a single total across all legs, e.g. `2`. A shootout
    is appended in parentheses, e.g. `1 (4)`.
  - `"legs"` — each side shows the goals of every leg in order, e.g. `2 0`. A shootout is
    appended in parentheses on the relevant side, e.g. `0 0 (4)`.
- `"max_label_chars"` (default `22`) — the maximum team-label width, in characters.
  Longer labels are truncated with an ellipsis. Cups with long team names can raise it;
  a host's `get_match` can also read it and return shorter names.
- `"box_width"` (default `190`) — the width of every match box. Widen it (instead of, or
  together with, lowering `max_label_chars`) to fit long names without truncation.

In both modes the winning side is emphasized when the `winner` field says so. For
single-match ties (one leg) the two modes render identically.

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
  "home": { /* Slot */ }, // required
  "away": { /* Slot */ }, // required
  "legs": [ /* Leg, ... */ ], // optional; absent => not played yet
  "winner": "home"        // optional; "home" | "away"
}
```

- `id` — internal identifier, referenced by `winner_of` (see Slot). Not a display
  value.
- `winner` — which side won, `"home"` or `"away"`. This is the **only** source of the
  winner: the renderer never computes it from the scores. Whatever maintains the JSON
  is responsible for setting it when a tie is decided. Absent means undecided.

## Slot

A slot is one side of a match. It is one of these shapes:

```jsonc
{ "team": "Flamengo", "id": 123, "seed": 1 }       // a concrete team; id and seed optional
{ "winner_of": "qf1" }                             // placeholder: winner of another match
{ "winner_of": "qf1", "team": "Flamengo" }         // linked, with the resolved name filled in
{ "tbd": true }                                    // to be defined
```

Bracket connections are **explicit** through `winner_of`, which must reference the
`id` of another match in the document. References must not form a cycle.

A `winner_of` slot may *also* carry a `team` (and optional `id`/`seed`). The link still
drives the bracket connector, while the name is shown instead of the placeholder. This
is how an advancing team is recorded: whatever maintains the JSON writes the resolved
`team` onto the next round's slot. The renderer does **not** work this out by itself.

## Leg

A single game within a match. Two-legged ties have two legs.

```jsonc
{
  "home": 2,                        // goals by the match's home side
  "away": 1,                        // goals by the match's away side
  "pens": { "home": 4, "away": 2 }, // optional, penalty shootout result
  "ref": 84021                      // optional, id of the real game in the host system
}
```

- `home`/`away` always refer to the match's `home`/`away` sides, regardless of which
  venue the leg was played at.
- `ref` is a pointer to the real game in the host system's database. A leg may carry
  **only** a `ref` and have its scores (and teams) filled in dynamically at render time
  — see "Host integration". A leg must have either `home`+`away` or a `ref`.
- A match with no played legs is "not played yet".

## Determining the winner

The winner of a match is exactly its `winner` field (`"home"` / `"away"`), or undecided
if absent. **No winner is computed** — not from the aggregate, not from penalties, and
the away-goals rule does not exist here. Advancing teams and decided series are written
into the document by whatever updates it.

## Host integration (non-normative)

A leg's `ref` lets a host system inject live data. When using the Python renderer's
`PlayoffDiagram` class, override `get_match(ref)` to return the data of that one game as
a positional pair `[home_side, away_side]` (the first element is the game's local/home
side). Each side may carry `team`, `goals` and `pens`. The renderer fills the leg's
scores and, where a slot has no team yet, its team name — keeping any `winner_of` link.
`get_tournament()` and `get_season()` can likewise supply those values dynamically.

## Rendering notes (non-normative)

- Layout is deterministic: rounds map to columns left-to-right; within the bracket,
  a match in round *n+1* is drawn vertically centered between the two matches it
  consumes (resolved via `winner_of`).
- A `winner_of` slot displays its resolved `team` when present, otherwise the
  placeholder label (e.g. "Winner QF1").
- The winning side of a match is emphasized only when the `winner` field says so.
