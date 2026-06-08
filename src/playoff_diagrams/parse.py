"""Load a bracket document (dict / JSON) into the dataclass model.

Structural validation against ``spec/schema.json`` is available via
:func:`validate_document` when the optional ``jsonschema`` package is installed; the
parser itself depends only on the standard library and raises clear errors.
"""

from __future__ import annotations

import json
import os
from typing import Any

from .model import Bracket, Leg, Match, Pens, RenderOptions, Round, Slot

_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "spec", "schema.json"
)


class BracketError(ValueError):
    """Raised when a document cannot be parsed into the model."""


def _require(obj: dict, key: str, where: str) -> Any:
    if key not in obj:
        raise BracketError(f"missing '{key}' in {where}")
    return obj[key]


def _parse_slot(data: dict, where: str) -> Slot:
    if "team" in data:
        return Slot(team=data["team"], team_id=data.get("id"), seed=data.get("seed"))
    if "winner_of" in data:
        return Slot(winner_of=data["winner_of"])
    if data.get("tbd") is True:
        return Slot(tbd=True)
    raise BracketError(
        f"slot in {where} must have one of 'team', 'winner_of' or 'tbd'"
    )


def _parse_leg(data: dict, where: str) -> Leg:
    pens = None
    if "pens" in data:
        p = data["pens"]
        pens = Pens(home=_require(p, "home", where), away=_require(p, "away", where))
    return Leg(
        home=_require(data, "home", where),
        away=_require(data, "away", where),
        pens=pens,
    )


def _parse_match(data: dict) -> Match:
    mid = _require(data, "id", "match")
    where = f"match '{mid}'"
    legs = [_parse_leg(leg, where) for leg in data.get("legs", [])]
    return Match(
        id=mid,
        home=_parse_slot(_require(data, "home", where), where),
        away=_parse_slot(_require(data, "away", where), where),
        legs=legs,
        ref=data.get("ref"),
        winner=data.get("winner"),
    )


def parse_bracket(data: dict) -> Bracket:
    """Build a :class:`Bracket` from an already-loaded JSON dict."""
    rounds = []
    for rd in _require(data, "rounds", "document"):
        name = _require(rd, "name", "round")
        matches = [_parse_match(m) for m in _require(rd, "matches", f"round '{name}'")]
        rounds.append(Round(name=name, matches=matches))
    render = RenderOptions(scores=(data.get("render") or {}).get("scores", "aggregate"))
    bracket = Bracket(
        tournament=_require(data, "tournament", "document"),
        rounds=rounds,
        season=data.get("season"),
        format=data.get("format", "single-elimination"),
        render=render,
    )
    _check_references(bracket)
    return bracket


def _check_references(bracket: Bracket) -> None:
    """Ensure every ``winner_of`` points at an existing match id."""
    known = set(bracket.matches_by_id())
    for rd in bracket.rounds:
        for match in rd.matches:
            for slot in (match.home, match.away):
                if slot.winner_of is not None and slot.winner_of not in known:
                    raise BracketError(
                        f"match '{match.id}' references unknown match "
                        f"'{slot.winner_of}'"
                    )


def load_bracket(path: str) -> Bracket:
    """Read a JSON file from ``path`` and parse it into a :class:`Bracket`."""
    with open(path, encoding="utf-8") as fh:
        return parse_bracket(json.load(fh))


def validate_document(data: dict) -> None:
    """Validate ``data`` against ``spec/schema.json`` (requires ``jsonschema``)."""
    from jsonschema import Draft202012Validator  # optional dependency

    with open(_SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft202012Validator(schema).validate(data)
