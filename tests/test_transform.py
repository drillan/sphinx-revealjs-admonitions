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
    assert html.count("<h2>Comment tail</h2>") == 2


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

    # Splitting: 2 breaks, Trailing: 1, Comment tail: 1, In list: 0
    assert marked.count("<section") - plain.count("<section") == 4
    assert marked.count("</section>") - plain.count("</section>") == 4
