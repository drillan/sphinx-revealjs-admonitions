"""Render Sphinx admonitions as standalone Reveal.js slides."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sphinx_revealjs_admonitions.transform import AdmonitionToSlide

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "0.1.0"


def setup(app: Sphinx) -> dict[str, Any]:
    """Entry point called by Sphinx."""
    app.setup_extension("sphinx_revealjs")
    app.add_post_transform(AdmonitionToSlide)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
