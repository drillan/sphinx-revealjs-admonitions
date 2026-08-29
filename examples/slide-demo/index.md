# sphinx-revealjs-admonitions

A deck that demonstrates the extension. Build it with `make revealjs`.

## Splitting

Text before the admonition stays on this slide.

:::{note}
:class: slide

Marked with `:class: slide`, so this note becomes a slide of its own.
:::

Text after the admonition gets a slide of its own too. All three carry the
section heading, because that is what `revealjs-break` does.

## Without the marker

:::{warning}
No `:class: slide` here, so this warning stays inline — it renders inside the
section's own slide, next to the surrounding text.
:::

That is the difference the marker makes.

## Styling

The sample stylesheet in `_static/slide-admonition.css` gives a marked
admonition the room to fill the slide.

:::{tip}
:class: slide

The marker stays on the rendered element, so `slide` doubles as a CSS hook:
`<div class="slide admonition tip">`.
:::

Rules must be written as `.admonition.slide`, never a bare `.slide` — Reveal.js
puts the transition name on the deck wrapper, so a bare rule hits everything.

## Every type works

:::{danger}
:class: slide

Any directive that accepts a `:class:` option and produces an admonition node
can be marked. The Reveal.js theme colours each type differently.
:::

## Where it does not split

An admonition must be a direct child of a section.

- Inside a list item, it cannot be split — the build says so rather than
  splitting something else by mistake.

Nothing here is silent: unsupported placements produce a warning, and a
`-W` build fails on them.
