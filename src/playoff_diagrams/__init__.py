"""Render a football playoff bracket as an SVG from a JSON source document."""

from .model import Bracket, Match, Round, Slot, Leg, Pens
from .parse import load_bracket, parse_bracket
from .render import render_svg

__all__ = [
    "Bracket",
    "Match",
    "Round",
    "Slot",
    "Leg",
    "Pens",
    "load_bracket",
    "parse_bracket",
    "render_svg",
]
