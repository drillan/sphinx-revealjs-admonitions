project = "sphinx-revealjs-admonitions demo"

extensions = [
    "myst_parser",
    "sphinx_revealjs",
    "sphinx_revealjs_admonitions",
]
myst_enable_extensions = ["colon_fence"]
exclude_patterns = ["_build"]

revealjs_style_theme = "white"
revealjs_static_path = ["_static"]
revealjs_css_files = ["slide-admonition.css"]
