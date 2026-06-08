"""Golden (snapshot) tests for SVG generation.

Each example is rendered and compared against a versioned reference SVG under
``tests/golden/``. When the output legitimately changes, regenerate the goldens with::

    PD_REGEN=1 pytest tests/test_render.py

and review the diff before committing.
"""

import glob
import os

import pytest

from playoff_diagrams import load_bracket, render_svg

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")
GOLDEN = os.path.join(os.path.dirname(__file__), "golden")

EXAMPLE_FILES = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(EXAMPLES, "*.json"))
)


def _golden_path(name: str) -> str:
    return os.path.join(GOLDEN, name.replace(".json", ".svg"))


@pytest.mark.parametrize("name", EXAMPLE_FILES)
def test_svg_matches_golden(name):
    svg = render_svg(load_bracket(os.path.join(EXAMPLES, name)))
    path = _golden_path(name)

    if os.environ.get("PD_REGEN"):
        os.makedirs(GOLDEN, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        pytest.skip(f"regenerated {os.path.basename(path)}")

    assert os.path.exists(path), f"missing golden {path}; run with PD_REGEN=1"
    with open(path, encoding="utf-8") as fh:
        assert svg == fh.read()


@pytest.mark.parametrize("name", EXAMPLE_FILES)
def test_svg_is_well_formed(name):
    import xml.dom.minidom

    svg = render_svg(load_bracket(os.path.join(EXAMPLES, name)))
    xml.dom.minidom.parseString(svg)  # raises on malformed XML
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
