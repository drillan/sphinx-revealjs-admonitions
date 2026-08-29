# Test deck

## Splitting

Before text.

:::{note}
:class: slide

Marked note.
:::

After text.

## Inline

:::{warning}
Unmarked stays inline.
:::

## Trailing

Only text before.

:::{tip}
:class: slide

Trailing tip.
:::

## Comment tail

:::{important}
:class: slide

Followed only by a comment.
:::

% speaker comment

## In list

- item

  :::{danger}
  :class: slide

  Parent is a list_item.
  :::

## Leading

:::{caution}
:class: slide

First content in the section.
:::

Text after.

## Subsection tail

Intro text.

:::{hint}
:class: slide

Followed only by a subsection.
:::

### Sub heading

Subsection body.

## Adjacent

Intro text.

:::{error}
:class: slide

First of two.
:::

:::{attention}
:class: slide

Second of two.
:::

## Directive sibling

```{revealjs-section}
:data-background-color: red
```

:::{warning}
:class: slide

Only content in the section.
:::

## Trailing raw

:::{seealso}
:class: slide

Marked seealso, followed only by non-html raw.
:::

```{raw} latex
non-html raw content
```

## Trailing hidden toctree

:::{admonition} Marked generic
:class: slide

Followed only by a hidden toctree.
:::

```{toctree}
:hidden:

other
```

## Leading hidden toctree

```{toctree}
:hidden:

other2
```

:::{tip}
:class: slide

Preceded only by a hidden toctree.
:::

## Trailing html raw

:::{warning}
:class: slide

Marked warning, followed by html raw.
:::

```{raw} html
<p>Real html content.</p>
```

## Trailing visible toctree

:::{hint}
:class: slide

Marked hint, followed by a visible toctree.
:::

```{toctree}

other3
```
