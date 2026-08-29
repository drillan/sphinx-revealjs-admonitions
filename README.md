# sphinx-revealjs-admonitions

Render Sphinx admonitions as standalone [Reveal.js](https://revealjs.com/) slides
in decks built with [sphinx-revealjs](https://github.com/attakei/sphinx-revealjs).

Mark an admonition with `:class: slide` and it becomes its own slide, carrying
the section heading over from the slide it was written in.

## Installation

Not on PyPI yet — install from the repository:

```console
pip install git+https://github.com/drillan/sphinx-revealjs-admonitions.git
```

With uv:

```console
uv add git+https://github.com/drillan/sphinx-revealjs-admonitions.git
```

## Usage

Add the extension to `conf.py`:

```python
extensions = [
    "sphinx_revealjs",
    "sphinx_revealjs_admonitions",
]
```

Then mark any admonition with `:class: slide`.

MyST:

```markdown
:::{note}
:class: slide

This note becomes a slide of its own.
:::
```

reStructuredText:

```rst
.. note::
   :class: slide

   This note becomes a slide of its own.
```

Build your deck exactly as before — `sphinx-build -b revealjs`. This extension
is a post-transform, so it adds no build step and no intermediate artifacts.

## Which admonitions can be marked

Any directive that accepts a `:class:` option and produces a
`docutils.nodes.Admonition` node:

`note`, `warning`, `tip`, `danger`, `caution`, `attention`, `error`, `hint`,
`important`, `seealso`, and the generic `admonition`.

`versionadded` and `deprecated` accept no `:class:` option, so they cannot be
marked.

## Styling

The marker stays on the rendered element, so `slide` doubles as a CSS hook:

```html
<div class="slide admonition note">…</div>
```

A ready-made sample lives in
[`examples/slide-demo/_static/slide-admonition.css`](https://github.com/drillan/sphinx-revealjs-admonitions/blob/main/examples/slide-demo/_static/slide-admonition.css).
Copy it into your own static directory and wire it up:

```python
revealjs_static_path = ["_static"]
revealjs_css_files = ["slide-admonition.css"]
```

If your project already sets `revealjs_static_path`, append to that list
instead of overwriting it.

That stylesheet is not shipped inside the installed package — it is a starting
point to copy and edit, not a dependency.

## Example project

**[View the deck live](https://drillan.github.io/sphinx-revealjs-admonitions/)** —
deployed from `main` on every push.

[`examples/slide-demo/`](https://github.com/drillan/sphinx-revealjs-admonitions/blob/main/examples/slide-demo) is a small deck that
exercises everything above: the split, the heading carried onto each slide, an
unmarked admonition for contrast, and the sample stylesheet applied. Build it
locally with:

```console
cd examples/slide-demo
make revealjs
```

**Always write `.admonition.slide`, never a bare `.slide`.** Reveal.js puts the
transition name on the deck wrapper — `<div class="reveal slide …">` with the
default transition — so a bare `.slide` rule also hits the whole deck.

## Limitations

- An admonition must be a direct child of a section. One nested in a list item
  or a block quote cannot be split; the build emits a warning and leaves it
  inline.
- Split slides carry no `id`, so they cannot be linked to individually. This
  matches the behaviour of the `revealjs-break` directive.
- Under headings deeper than the third level, sphinx-revealjs does not open
  slides at all; a following sibling section is absorbed into the split slide.
  This mirrors the behaviour without this extension. A subsection at that depth
  following a marked admonition is merged into the admonition's own slide.
- With `revealjs_notes_from_comments` enabled, a comment written directly
  after a marked admonition attaches its speaker notes to the *next* slide,
  not the admonition's own slide — the trailing break is inserted between
  the admonition and the comment.
- A `revealjs-section` directive's `:data-background-color:` (or any other
  `data-*` attribute) applies only to the section's first slide. Slides
  produced by an inserted break do not carry it, so marking an admonition in
  a section that also sets a background loses that background on the split
  slides.

## License

Apache-2.0
