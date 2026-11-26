"""The Marketplace exclude markers in the README pair up."""

from pathlib import Path
import re

import pytest

ROOT = Path(__file__).parent.parent
# Before initialization the integration's README is still the template.
README = ROOT / "README.template.md" if (ROOT / "README.template.md").exists() else ROOT / "README.md"

MARKER = re.compile(r"<!--\s*ha-marketplace:exclude-(start|end)\s*-->")
# Markers inside a code block or inline code are text, not markers.
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


@pytest.mark.unit
def test_exclude_markers_alternate_and_close() -> None:
    """A start without its end hides the rest of the README in the Marketplace, and GitHub shows neither."""
    text = CODE.sub("", README.read_text(encoding="utf-8"))
    kinds = [match.group(1) for match in MARKER.finditer(text)]

    assert kinds == ["start", "end"] * (len(kinds) // 2), f"unbalanced exclude markers in {README.name}: {kinds}"
