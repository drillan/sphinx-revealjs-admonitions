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
