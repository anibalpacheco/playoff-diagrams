"""Parsed, in-memory representation of a bracket document, plus result logic.

The shapes here mirror the JSON language described in ``spec/format.md``. Keeping the
models as plain dataclasses avoids any third-party dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

Id = Union[str, int]


@dataclass
class Pens:
    """Penalty shootout result for a leg."""

    home: int
    away: int


@dataclass
class Leg:
    """A single played game within a match.

    ``home`` and ``away`` always refer to the match's home/away sides, regardless of
    which venue the leg was played at.
    """

    home: int
    away: int
    pens: Optional[Pens] = None


@dataclass
class Slot:
    """One side of a match. Exactly one of the three shapes is populated."""

    team: Optional[str] = None
    team_id: Optional[Id] = None
    seed: Optional[int] = None
    winner_of: Optional[str] = None
    tbd: bool = False

    @property
    def kind(self) -> str:
        if self.team is not None:
            return "team"
        if self.winner_of is not None:
            return "winner_of"
        return "tbd"


@dataclass
class Match:
    """One bracket node: two sides plus an optional, possibly multi-leg result."""

    id: str
    home: Slot
    away: Slot
    legs: list[Leg] = field(default_factory=list)
    ref: Optional[Id] = None
    winner: Optional[str] = None  # explicit override: "home" | "away"


@dataclass
class Round:
    name: str
    matches: list[Match]


@dataclass
class RenderOptions:
    """Document-level display preferences.

    ``scores``: how a played match's result is shown on each side.
      - ``"aggregate"`` (default): a single total, e.g. ``2`` (``4`` for a shootout).
      - ``"legs"``: each leg's goals in order, e.g. ``2 0`` (with ``(4)`` for pens).
    """

    scores: str = "aggregate"


@dataclass
class Bracket:
    tournament: str
    rounds: list[Round]
    season: Optional[str] = None
    format: str = "single-elimination"
    render: RenderOptions = field(default_factory=RenderOptions)

    def matches_by_id(self) -> dict[str, Match]:
        return {m.id: m for r in self.rounds for m in r.matches}


def aggregate(match: Match) -> Optional[tuple[int, int]]:
    """Return (home_total, away_total) across all legs, or None if not played."""
    if not match.legs:
        return None
    home = sum(leg.home for leg in match.legs)
    away = sum(leg.away for leg in match.legs)
    return home, away


def winner_side(match: Match) -> Optional[str]:
    """Compute the winning side ("home"/"away"), or None if undecided.

    Implements the rules in ``spec/format.md``: explicit override, then aggregate, then
    the last leg carrying ``pens``. The away-goals rule is intentionally not applied.
    """
    if match.winner in ("home", "away"):
        return match.winner
    agg = aggregate(match)
    if agg is None:
        return None
    home, away = agg
    if home > away:
        return "home"
    if away > home:
        return "away"
    for leg in reversed(match.legs):
        if leg.pens is not None:
            if leg.pens.home > leg.pens.away:
                return "home"
            if leg.pens.away > leg.pens.home:
                return "away"
            return None
    return None


def shootout(match: Match) -> Optional[Pens]:
    """Return the deciding penalty shootout, if this match went to one."""
    agg = aggregate(match)
    if agg is None or agg[0] != agg[1]:
        return None
    for leg in reversed(match.legs):
        if leg.pens is not None:
            return leg.pens
    return None


class Resolver:
    """Resolves placeholder slots to display labels by walking ``winner_of`` links."""

    def __init__(self, bracket: Bracket) -> None:
        self._by_id = bracket.matches_by_id()

    def label(self, slot: Slot) -> str:
        if slot.kind == "team":
            return slot.team  # type: ignore[return-value]
        if slot.kind == "tbd":
            return "TBD"
        match = self._by_id.get(slot.winner_of or "")
        if match is None:
            return "?"
        side = winner_side(match)
        if side is None:
            return f"Winner {match.id.upper()}"
        return self.label(match.home if side == "home" else match.away)
