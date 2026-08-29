"""Post-transform that turns marked admonitions into standalone slides."""

from __future__ import annotations

from typing import Any

from docutils import nodes
from sphinx import addnodes
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx_revealjs.nodes import (
    revealjs_break,
    revealjs_section,
    revealjs_slide,
    revealjs_vertical,
)

MARKER = "slide"

# Node types known to render no HTML output of their own, so their presence
# next to a marked admonition cannot make a slide non-empty. This list is
# NOT exhaustive -- it is a blocklist of types found empirically to render
# nothing, and grows as more are found. Some types can't be judged by type
# alone (a `raw` node's emptiness depends on its `format`; a hidden toctree
# is only empty once resolved) -- see `_renders_nothing`.
IGNORED = (
    nodes.Invisible,
    nodes.system_message,
    revealjs_section,
    revealjs_vertical,
    revealjs_slide,
)

logger = logging.getLogger(__name__)


def _renders_nothing(node: nodes.Node) -> bool:
    """Tell whether a sibling node is known to render no HTML output.

    Beyond the static ``IGNORED`` blocklist, two node types render nothing
    only conditionally:

    - a ``raw`` node renders nothing unless "html" is one of its (possibly
      space-separated) ``format`` values;
    - a ``toctree`` directive's sibling is a ``compound`` node classed
      "toctree-wrapper", not the ``addnodes.toctree`` node itself -- that
      node is wrapped inside it. At the point this post-transform runs the
      toctree has not yet been resolved into a rendered list, so it is still
      an ``addnodes.toctree`` child carrying a ``hidden`` attribute; it
      renders nothing only when every such child is hidden (or, after
      resolution, when the compound is simply empty). A visible toctree
      renders a list of links and must not be ignored.
    """
    if isinstance(node, IGNORED):
        return True
    if isinstance(node, nodes.raw):
        return "html" not in node.get("format", "").split()
    if isinstance(node, nodes.compound) and "toctree-wrapper" in node.get(
        "classes", []
    ):
        return all(
            isinstance(child, addnodes.toctree) and child.get("hidden", False)
            for child in node.children
        )
    return False


class AdmonitionToSlide(SphinxPostTransform):
    """Insert ``revealjs_break`` siblings around marked admonitions."""

    default_priority = 450
    builders = ("revealjs", "dirrevealjs")

    def run(self, **kwargs: Any) -> None:
        """Split every marked admonition into its own slide."""
        targets: list[nodes.Element] = [
            node
            for node in self.document.findall(nodes.Element)
            if isinstance(node, nodes.Admonition) and MARKER in node.get("classes", [])
        ]
        for node in targets:
            parent = node.parent
            if not isinstance(parent, nodes.section):
                logger.warning(
                    "admonition marked '%s' is not a direct child of a section "
                    "(parent=%s); not split into a slide.",
                    MARKER,
                    type(parent).__name__,
                    location=node,
                )
                continue
            index = parent.index(node)
            if self._trailing_break_needed(parent.children[index + 1 :]):
                parent.insert(index + 1, revealjs_break())
            if self._leading_break_needed(parent.children[:index]):
                parent.insert(index, revealjs_break())

    @staticmethod
    def _trailing_break_needed(tail: list[nodes.Node]) -> bool:
        """Tell whether a break after the admonition would open a slide with content."""
        for node in tail:
            if _renders_nothing(node):
                continue
            return not isinstance(node, (nodes.section, revealjs_break))
        return False

    @staticmethod
    def _leading_break_needed(head: list[nodes.Node]) -> bool:
        """Tell whether a break before the admonition leaves a slide with content."""
        for node in reversed(head):
            if _renders_nothing(node):
                continue
            return not isinstance(node, (nodes.title, revealjs_break))
        return False
