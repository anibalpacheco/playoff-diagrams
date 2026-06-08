"""Unit tests for result logic and parsing."""

import json
import os

import pytest

from playoff_diagrams import parse_bracket
from playoff_diagrams.model import Leg, Match, Pens, Slot, Resolver, winner_side
from playoff_diagrams.parse import BracketError, validate_document

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def _match(home_legs, away_legs=None, **kw):
    legs = [Leg(h, a) for h, a in home_legs]
    return Match(id="m", home=Slot(team="H"), away=Slot(team="A"), legs=legs, **kw)


def test_winner_by_aggregate():
    m = _match([(2, 1), (0, 0)])
    assert winner_side(m) == "home"


def test_winner_away_on_aggregate():
    m = _match([(1, 1), (2, 3)])
    assert winner_side(m) == "away"


def test_tie_decided_by_pens():
    m = Match(
        id="m",
        home=Slot(team="H"),
        away=Slot(team="A"),
        legs=[Leg(1, 1), Leg(0, 0, Pens(home=4, away=2))],
    )
    assert winner_side(m) == "home"


def test_tie_without_pens_is_undecided():
    assert winner_side(_match([(1, 1)])) is None


def test_not_played_has_no_winner():
    m = Match(id="m", home=Slot(team="H"), away=Slot(team="A"))
    assert winner_side(m) is None


def test_explicit_winner_override():
    m = _match([(3, 0)], winner="away")
    assert winner_side(m) == "away"


def test_no_away_goals_rule():
    # Equal aggregate (2-2) with more away goals must remain undecided.
    m = _match([(2, 0), (0, 2)])
    assert winner_side(m) is None


def test_resolver_follows_winner_of():
    data = {
        "tournament": "T",
        "rounds": [
            {"name": "SF", "matches": [
                {"id": "sf1", "home": {"team": "X"}, "away": {"team": "Y"},
                 "legs": [{"home": 1, "away": 0}]},
            ]},
            {"name": "Final", "matches": [
                {"id": "f", "home": {"winner_of": "sf1"}, "away": {"tbd": True}},
            ]},
        ],
    }
    bracket = parse_bracket(data)
    resolver = Resolver(bracket)
    final = bracket.matches_by_id()["f"]
    assert resolver.label(final.home) == "X"
    assert resolver.label(final.away) == "TBD"


def test_unresolved_winner_of_is_placeholder():
    data = {
        "tournament": "T",
        "rounds": [
            {"name": "SF", "matches": [
                {"id": "sf1", "home": {"team": "X"}, "away": {"team": "Y"}},
            ]},
            {"name": "Final", "matches": [
                {"id": "f", "home": {"winner_of": "sf1"}, "away": {"tbd": True}},
            ]},
        ],
    }
    bracket = parse_bracket(data)
    assert Resolver(bracket).label(bracket.matches_by_id()["f"].home) == "Winner SF1"


def test_unknown_reference_is_rejected():
    data = {
        "tournament": "T",
        "rounds": [
            {"name": "Final", "matches": [
                {"id": "f", "home": {"winner_of": "ghost"}, "away": {"tbd": True}},
            ]},
        ],
    }
    with pytest.raises(BracketError):
        parse_bracket(data)


def test_render_option_defaults_to_aggregate():
    bracket = parse_bracket({"tournament": "T", "rounds": [
        {"name": "Final", "matches": [
            {"id": "f", "home": {"team": "X"}, "away": {"team": "Y"}}]}]})
    assert bracket.render.scores == "aggregate"


def test_score_text_modes():
    from playoff_diagrams.layout import _score_text

    m = Match(id="m", home=Slot(team="H"), away=Slot(team="A"),
              legs=[Leg(2, 1), Leg(0, 0)])
    assert _score_text(m, "home", "aggregate") == "2"
    assert _score_text(m, "home", "legs") == "2 0"
    assert _score_text(m, "away", "legs") == "1 0"

    shoot = Match(id="m", home=Slot(team="H"), away=Slot(team="A"),
                  legs=[Leg(1, 1), Leg(0, 0, Pens(4, 2))])
    assert _score_text(shoot, "home", "aggregate") == "1 (4)"
    assert _score_text(shoot, "home", "legs") == "1 0 (4)"


@pytest.mark.parametrize("name", ["libertadores-2026.json", "knockout-8.json"])
def test_examples_match_schema(name):
    pytest.importorskip("jsonschema")
    with open(os.path.join(EXAMPLES, name), encoding="utf-8") as fh:
        validate_document(json.load(fh))
