import pytest


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_revealjs_build_succeeds_with_extension(app):
    app.build()
    assert (app.outdir / "index.html").exists()


def read_deck(app) -> str:
    return (app.outdir / "index.html").read_text(encoding="utf-8")


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_marked_admonition_splits_into_three_slides(app):
    app.build()
    html = read_deck(app)
    assert html.count("<h2>Splitting</h2>") == 3
    # This div-class count is page-wide, not scoped to this section: a new
    # fixture section that marks a {note} with :class: slide would also be
    # counted here, so pick a different admonition type for new fixtures.
    assert html.count('<div class="slide admonition note">') == 1


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_unmarked_admonition_is_not_split(app):
    app.build()
    html = read_deck(app)
    assert html.count("<h2>Inline</h2>") == 1


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_trailing_admonition_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    assert html.count("<h2>Trailing</h2>") == 2


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_invisible_tail_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # The admonition opens the section, so it stays on the section's own slide;
    # the trailing comment is invisible, so nothing splits off after it.
    assert html.count("<h2>Comment tail</h2>") == 1


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_admonition_outside_section_warns_and_is_not_split(app, warning):
    app.build()
    html = read_deck(app)
    assert html.count("<h2>In list</h2>") == 1
    assert "not a direct child of a section" in warning.getvalue()


@pytest.mark.sphinx("html", testroot="myst")
def test_html_builder_emits_no_warning(app, warning):
    app.build()
    assert "not a direct child of a section" not in warning.getvalue()


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_inserted_breaks_keep_section_tags_balanced(app, make_app, app_params):
    app.build()
    marked = read_deck(app)

    args, kwargs = app_params
    kwargs = dict(kwargs)
    kwargs["confoverrides"] = {"extensions": ["myst_parser", "sphinx_revealjs"]}
    kwargs["freshenv"] = True
    baseline = make_app(*args, **kwargs)
    baseline.build()
    plain = (baseline.outdir / "index.html").read_text(encoding="utf-8")

    # Splitting 2, Trailing 1, Leading 1, Subsection tail 1, Adjacent 2.
    # Directive sibling, Trailing raw, Trailing hidden toctree, and Leading
    # hidden toctree each contribute 0: their only sibling renders nothing,
    # so no break is inserted on that side, and the admonition in each is
    # otherwise alone in its section (no other side needs a break either).
    # Trailing html raw and Trailing visible toctree each contribute 1: their
    # sibling DOES render, so the trailing break fires as usual.
    # 2+1+1+1+2 + 0+0+0+0 + 1+1 = 9
    assert marked.count("<section") - plain.count("<section") == 9
    assert marked.count("</section>") - plain.count("</section>") == 9


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_admonition_first_in_section_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # The section's own slide holds the admonition; only "Text after." splits off.
    assert html.count("<h2>Leading</h2>") == 2


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_subsection_tail_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # A subsection opens its own slide, so no trailing break is needed.
    assert html.count("<h2>Subsection tail</h2>") == 2


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_adjacent_admonitions_make_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # Intro, first admonition, second admonition — nothing empty between them.
    assert html.count("<h2>Adjacent</h2>") == 3


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_non_rendering_sibling_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # revealjs-section renders nothing, so the admonition still opens the slide.
    assert html.count("<h2>Directive sibling</h2>") == 1


# The three tests below pin only the suppression side of the break
# predicates: that a break is NOT inserted next to a sibling that renders
# nothing. The general positive side -- that a break IS inserted when there
# is real content -- is already pinned by
# test_marked_admonition_splits_into_three_slides and
# test_inserted_breaks_keep_section_tags_balanced; the positive side specific
# to raw/toctree siblings (html raw, a visible toctree) is pinned by the two
# tests further below.


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_trailing_non_html_raw_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # A raw node whose format is not html renders nothing, so no trailing
    # break should follow the admonition.
    assert html.count("<h2>Trailing raw</h2>") == 1


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_trailing_hidden_toctree_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # A hidden toctree resolves to an empty compound node, so no trailing
    # break should follow the admonition.
    assert html.count("<h2>Trailing hidden toctree</h2>") == 1


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_leading_hidden_toctree_makes_no_empty_slide(app):
    app.build()
    html = read_deck(app)
    # A hidden toctree resolves to an empty compound node, so no leading
    # break should precede the admonition.
    assert html.count("<h2>Leading hidden toctree</h2>") == 1


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_trailing_html_raw_still_splits(app):
    app.build()
    html = read_deck(app)
    # A raw node whose format includes html renders real output, so the
    # trailing break must still be inserted -- this is the positive
    # counterpart to test_trailing_non_html_raw_makes_no_empty_slide.
    assert html.count("<h2>Trailing html raw</h2>") == 2


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_trailing_visible_toctree_still_splits(app):
    app.build()
    html = read_deck(app)
    # A non-hidden toctree renders a list of links, so the trailing break
    # must still be inserted -- this is the positive counterpart to
    # test_trailing_hidden_toctree_makes_no_empty_slide.
    assert html.count("<h2>Trailing visible toctree</h2>") == 2


@pytest.mark.sphinx("revealjs", testroot="rst")
def test_rst_behaves_like_myst(app, warning):
    app.build()
    html = read_deck(app)
    assert html.count("<h2>Splitting</h2>") == 3
    assert html.count("<h2>Inline</h2>") == 1
    assert html.count("<h2>Trailing</h2>") == 2
    assert html.count("<h2>In list</h2>") == 1
    assert "not a direct child of a section" in warning.getvalue()
