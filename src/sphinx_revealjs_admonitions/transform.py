"""Post-transform that turns marked admonitions into standalone slides."""

from __future__ import annotations

from typing import Any

from docutils import nodes
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx_revealjs.nodes import revealjs_break

MARKER = "slide"

logger = logging.getLogger(__name__)


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
            if isinstance(node, (nodes.Invisible, nodes.system_message)):
                continue
            return not isinstance(node, (nodes.section, revealjs_break))
        return False

    @staticmethod
    def _leading_break_needed(head: list[nodes.Node]) -> bool:
        """Tell whether a break before the admonition leaves a slide with content."""
        for node in reversed(head):
            if isinstance(node, (nodes.Invisible, nodes.system_message)):
                continue
            return not isinstance(node, (nodes.title, revealjs_break))
        return False
