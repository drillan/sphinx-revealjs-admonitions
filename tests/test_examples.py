import re
from pathlib import Path

CSS = (
    Path(__file__).parent.parent
    / "examples"
    / "slide-demo"
    / "_static"
    / "slide-admonition.css"
)


def test_example_css_never_uses_a_bare_slide_selector():
    # Comments explain the rule and mention `.slide` in prose; strip them first.
    text = re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)
    bare = [
        match.group(0)
        for match in re.finditer(r"\.slide\b", text)
        if not text[: match.start()].endswith(".admonition")
    ]
    assert bare == [], f"bare .slide selector found: {bare}"
