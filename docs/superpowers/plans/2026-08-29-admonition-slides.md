# sphinx-revealjs-admonitions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `:class: slide` を付けた admonition を、Reveal.js の独立したスライドとして描画する Sphinx 拡張を作る。

**Architecture:** `SphinxPostTransform` を 1 つだけ持つ。対象 admonition の前後に sphinx-revealjs の `revealjs_break` ノードを兄弟として挿入し、スライド分割そのものは既存の visit/depart に委ねる。sphinx-revealjs 本体への変更は行わない。

**Tech Stack:** Python 3.13+ / Sphinx / sphinx-revealjs / docutils / pytest（`sphinx.testing`）/ uv / ruff / mypy

**Spec:** `docs/superpowers/specs/2026-08-29-admonition-slides-design.md`

## Global Constraints

これらは全タスクの要件に含まれる。

- `requires-python = ">=3.13"`
- build backend は `uv_build>=0.11.0,<0.12.0`、src レイアウト
- 実行時依存は `sphinx-revealjs>=3.2,<4` のみ。`myst-parser` は test グループに置き、実行時依存にしない
- マーカー文字列は `slide` に固定。conf.py の設定項目にしない
- post-transform の `default_priority = 450`（400 は latex ビルダーの 4 つが占有）
- post-transform は `builders = ("revealjs", "dirrevealjs")` で限定する。`formats` は使わない
- ライセンスは Apache-2.0（リポジトリの `LICENSE` は既に Apache-2.0）
- author は `{ name = "driller", email = "eleshis@gmail.com" }`（`sphinx-oceanid` と同一。変更が必要なら着手前に指摘すること）
- README は英語のみ
- **フォールバック禁止**: 親が `nodes.section` でない場合は既定値で処理を続行せず、`logger.warning` で必ず可視化する
- 各コミットの前に `uv run ruff check --fix . && uv run ruff format . && uv run mypy .` を実行し、全て通してからコミットする

---

### Task 1: パッケージ雛形とテスト基盤

拡張を読み込んだ状態で revealjs ビルドが通ることまでを作る。変換ロジックはまだ入れない。

**Files:**
- Create: `pyproject.toml`
- Create: `src/sphinx_revealjs_admonitions/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/roots/test-myst/conf.py`
- Create: `tests/roots/test-myst/index.md`
- Test: `tests/test_transform.py`

**Interfaces:**
- Consumes: なし
- Produces: `sphinx_revealjs_admonitions.setup(app: Sphinx) -> dict[str, Any]` — Sphinx 拡張のエントリポイント。`tests/roots/test-myst` は `testroot="myst"` で参照できるテストルート。

- [ ] **Step 1: `pyproject.toml` を作る**

```toml
[build-system]
requires = ["uv_build>=0.11.0,<0.12.0"]
build-backend = "uv_build"

[project]
name = "sphinx-revealjs-admonitions"
version = "0.1.0"
description = "Render Sphinx admonitions as standalone Reveal.js slides"
readme = "README.md"
license = "Apache-2.0"
license-files = ["LICENSE"]
requires-python = ">=3.13"
keywords = ["sphinx", "revealjs", "slides", "admonition", "presentation"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Sphinx :: Extension",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Documentation :: Sphinx",
]
authors = [
    { name = "driller", email = "eleshis@gmail.com" },
]
dependencies = [
    "sphinx-revealjs>=3.2,<4",
]

[project.urls]
Homepage = "https://github.com/drillan/sphinx-revealjs-admonitions"
Repository = "https://github.com/drillan/sphinx-revealjs-admonitions"

[dependency-groups]
test = [
    "pytest",
    "myst-parser",
]
dev = [
    "ruff",
    "mypy",
    "types-docutils",
    { include-group = "test" },
]

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "ANN", "D"]
ignore = ["D203", "D213"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D", "ANN"]

[tool.mypy]
python_version = "3.13"
strict = true
exclude = ["^tests/"]

[[tool.mypy.overrides]]
module = ["sphinx_revealjs.*"]
ignore_missing_imports = true
```

- [ ] **Step 2: テストルートを作る**

`tests/roots/test-myst/conf.py`:

```python
extensions = [
    "myst_parser",
    "sphinx_revealjs",
    "sphinx_revealjs_admonitions",
]
myst_enable_extensions = ["colon_fence"]
```

`tests/roots/test-myst/index.md`:

````markdown
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
````

- [ ] **Step 3: `tests/conftest.py` を作る**

`rootdir` を上書きしないと `testroot="myst"` が解決されない。

```python
from pathlib import Path

import pytest

pytest_plugins = "sphinx.testing.fixtures"


@pytest.fixture(scope="session")
def rootdir() -> Path:
    return Path(__file__).parent.resolve() / "roots"
```

- [ ] **Step 4: 失敗するテストを書く**

`tests/test_transform.py`:

```python
import pytest


@pytest.mark.sphinx("revealjs", testroot="myst")
def test_revealjs_build_succeeds_with_extension(app):
    app.build()
    assert (app.outdir / "index.html").exists()
```

- [ ] **Step 5: テストを走らせて失敗を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: FAIL。`sphinx_revealjs_admonitions` が import できず `ExtensionError` になる。

- [ ] **Step 6: 拡張のエントリポイントを作る**

`src/sphinx_revealjs_admonitions/__init__.py`:

```python
"""Render Sphinx admonitions as standalone Reveal.js slides."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "0.1.0"


def setup(app: Sphinx) -> dict[str, Any]:
    """Entry point called by Sphinx."""
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
```

- [ ] **Step 7: テストを走らせて成功を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: PASS

- [ ] **Step 8: lint と型検査を通す**

Run: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
Expected: エラーなし

- [ ] **Step 9: コミット**

```bash
git add pyproject.toml src tests
git commit -m "feat: add package skeleton and sphinx test harness"
```

---

### Task 2: マーカー付き admonition をスライドに分割する

**Files:**
- Create: `src/sphinx_revealjs_admonitions/transform.py`
- Modify: `src/sphinx_revealjs_admonitions/__init__.py`（`setup()` に登録を追加）
- Test: `tests/test_transform.py`（テストを追加）

**Interfaces:**
- Consumes: `sphinx_revealjs_admonitions.setup`（Task 1）、テストルート `test-myst`（Task 1）
- Produces: `sphinx_revealjs_admonitions.transform.AdmonitionToSlide`（`SphinxPostTransform` のサブクラス）、モジュール定数 `MARKER: str = "slide"`

分割後スライドには親 section の見出しが再描画される。したがって「見出しの出現回数」が分割数の指標になる。

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_transform.py` に追記する。

```python
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
```

- [ ] **Step 2: テストを走らせて失敗を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: `test_marked_admonition_splits_into_three_slides` が FAIL（`<h2>Splitting</h2>` は 1 回しか現れない）。`test_unmarked_admonition_is_not_split` は PASS する。

- [ ] **Step 3: transform を実装する**

`src/sphinx_revealjs_admonitions/transform.py`:

```python
"""Post-transform that turns marked admonitions into standalone slides."""

from __future__ import annotations

from typing import Any

from docutils import nodes
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx_revealjs.nodes import revealjs_break

MARKER = "slide"


class AdmonitionToSlide(SphinxPostTransform):
    """Insert ``revealjs_break`` siblings around marked admonitions."""

    default_priority = 450
    builders = ("revealjs", "dirrevealjs")

    def run(self, **kwargs: Any) -> None:
        """Split every marked admonition into its own slide."""
        targets = [
            node
            for node in self.document.findall(nodes.Admonition)
            if MARKER in node.get("classes", [])
        ]
        for node in targets:
            parent = node.parent
            if not isinstance(parent, nodes.section):
                continue
            index = parent.index(node)
            parent.insert(index + 1, revealjs_break())
            parent.insert(index, revealjs_break())
```

挿入は後方から先に行う。前方を先に入れると後方の位置がずれる。

`isinstance(parent, nodes.section)` をこの時点で入れるのは、`node.parent` が
`Element | None` 型であり、strict な mypy が `.index()` の呼び出しを拒否するためである。
この段階のテストルートには非 section 親のケースが無いので、握り潰しは起きない。
警告の送出は Task 4 で加える。

- [ ] **Step 4: `setup()` に登録する**

`src/sphinx_revealjs_admonitions/__init__.py` の `setup()` を差し替える。

```python
def setup(app: Sphinx) -> dict[str, Any]:
    """Entry point called by Sphinx."""
    app.setup_extension("sphinx_revealjs")
    app.add_post_transform(AdmonitionToSlide)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
```

ファイル先頭に import を足す。

```python
from sphinx_revealjs_admonitions.transform import AdmonitionToSlide
```

- [ ] **Step 5: テストを走らせて成功を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: 3 件すべて PASS

- [ ] **Step 6: lint と型検査を通す**

Run: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
Expected: エラーなし

- [ ] **Step 7: コミット**

```bash
git add src tests
git commit -m "feat: split marked admonitions into standalone slides"
```

---

### Task 3: 末尾の admonition で空スライドを作らない

後続に可視ノードが無い場合に後方の break を挿すと、見出しだけのスライドができる。これを抑止する。

**Files:**
- Modify: `src/sphinx_revealjs_admonitions/transform.py`
- Modify: `tests/roots/test-myst/index.md`（節を追加）
- Test: `tests/test_transform.py`（テストを追加）

**Interfaces:**
- Consumes: `AdmonitionToSlide`（Task 2）
- Produces: `AdmonitionToSlide._has_visible_tail(tail: list[nodes.Node]) -> bool` — 後続の兄弟に可視ノードがあるかを返す内部メソッド

- [ ] **Step 1: テストルートに節を 2 つ追加する**

`tests/roots/test-myst/index.md` の末尾に追記する。

````markdown
## Trailing

Only text before.

:::{tip}
:class: slide

Trailing tip.
:::

## Comment tail

:::{note}
:class: slide

Followed only by a comment.
:::

% speaker comment
````

- [ ] **Step 2: 失敗するテストを書く**

`tests/test_transform.py` に追記する。

```python
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
```

- [ ] **Step 3: テストを走らせて失敗を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: 追加した 2 件が FAIL（どちらも 3 になる。後方の break が無条件に挿さるため）

- [ ] **Step 4: 可視判定を実装する**

`transform.py` の `run()` を差し替え、メソッドを 1 つ足す。

```python
    def run(self, **kwargs: Any) -> None:
        """Split every marked admonition into its own slide."""
        targets = [
            node
            for node in self.document.findall(nodes.Admonition)
            if MARKER in node.get("classes", [])
        ]
        for node in targets:
            parent = node.parent
            if not isinstance(parent, nodes.section):
                continue
            index = parent.index(node)
            if self._has_visible_tail(parent.children[index + 1 :]):
                parent.insert(index + 1, revealjs_break())
            parent.insert(index, revealjs_break())

    @staticmethod
    def _has_visible_tail(tail: list[nodes.Node]) -> bool:
        """Tell whether any following sibling renders output."""
        return any(
            not isinstance(node, (nodes.Invisible, nodes.system_message))
            for node in tail
        )
```

`nodes.Invisible` は `comment`・`target`・`substitution_definition`・`pending`・
`sphinx.addnodes.index` を一括で捕捉する。`system_message` は `Invisible` の派生ではないため個別に列挙する。

- [ ] **Step 5: テストを走らせて成功を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: 5 件すべて PASS

- [ ] **Step 6: lint と型検査を通す**

Run: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
Expected: エラーなし

- [ ] **Step 7: コミット**

```bash
git add src tests
git commit -m "feat: skip the trailing break when nothing visible follows"
```

---

### Task 4: 非 section 親を警告し、revealjs ビルドに限定されていることを確かめる

親が `nodes.section` でない admonition に break を挿すと、意図しない祖先を閉じる。この構成は非対応とし、必ず警告する。

同時に、この警告が **html ビルドでは出ない**ことを確かめる。これが `builders` による限定の唯一の観測可能な効果である（html 出力そのものは、`revealjs_break` が html ビルダーで `skip_node` 登録されているため、限定の有無にかかわらず壊れない）。

**Files:**
- Modify: `src/sphinx_revealjs_admonitions/transform.py`
- Modify: `tests/roots/test-myst/index.md`（節を追加）
- Test: `tests/test_transform.py`（テストを追加）

**Interfaces:**
- Consumes: `AdmonitionToSlide`（Task 2、Task 3）
- Produces: モジュール変数 `logger`（`sphinx.util.logging.getLogger(__name__)`）

- [ ] **Step 1: テストルートに節を追加する**

`tests/roots/test-myst/index.md` の末尾に追記する。

````markdown
## In list

- item

  :::{danger}
  :class: slide

  Parent is a list_item.
  :::
````

- [ ] **Step 2: 失敗するテストを書く**

`tests/test_transform.py` に追記する。

```python
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
```

3 つ目は spec 6 章の項目 8 にあたる。挿入した `revealjs_break` 1 つにつき
`<section>` の開きと閉じがちょうど 1 つずつ増えることを、拡張を外したビルドとの差分で確かめる。
`revealjs_break` に委ねている限り釣り合いが崩れないという設計の中核を、テストとして保持する。

- [ ] **Step 3: テストを走らせて失敗を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: `test_admonition_outside_section_warns_and_is_not_split` が FAIL。
`<h2>In list</h2>` が 1 回であることは Task 2 の section 判定により既に満たされているが、
警告文字列が出力に無いため落ちる。`test_html_builder_emits_no_warning` と
`test_inserted_breaks_keep_section_tags_balanced` は PASS する。

- [ ] **Step 4: 親の検査と警告を実装する**

`transform.py` の import に足す。

```python
from sphinx.util import logging

logger = logging.getLogger(__name__)
```

Task 2 で入れた素の `continue` を、警告付きに置き換える。

```python
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
```

既定値で処理を続行せず、当該ノードだけを変換対象から外す。`-W` 付きビルドではエラーになる。

- [ ] **Step 5: テストを走らせて成功を確認する**

Run: `uv run pytest tests/test_transform.py -v`
Expected: 8 件すべて PASS

- [ ] **Step 6: lint と型検査を通す**

Run: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
Expected: エラーなし

- [ ] **Step 7: コミット**

```bash
git add src tests
git commit -m "feat: warn instead of splitting admonitions outside a section"
```

---

### Task 5: RST でも同じ結果になることをテストで保持する

「MyST と RST はどちらも同一の docutils ノードを生成するため記法による差はない」という spec の主張を、会話の記録ではなく回帰テストとして保持する。

**Files:**
- Create: `tests/roots/test-rst/conf.py`
- Create: `tests/roots/test-rst/index.rst`
- Test: `tests/test_transform.py`（テストを追加）

**Interfaces:**
- Consumes: `AdmonitionToSlide`（Task 2〜4）
- Produces: テストルート `test-rst`（`testroot="rst"` で参照）

- [ ] **Step 1: RST のテストルートを作る**

`tests/roots/test-rst/conf.py`:

```python
extensions = [
    "sphinx_revealjs",
    "sphinx_revealjs_admonitions",
]
```

`myst_parser` を入れない。この拡張が RST だけで動くことをここで示す。

`tests/roots/test-rst/index.rst`:

```rst
=========
Test deck
=========

Splitting
=========

Before text.

.. note::
   :class: slide

   Marked note.

After text.

Inline
======

.. warning::

   Unmarked stays inline.

Trailing
========

Only text before.

.. tip::
   :class: slide

   Trailing tip.

In list
=======

- item

  .. danger::
     :class: slide

     Parent is a list_item.
```

- [ ] **Step 2: テストを書く**

`tests/test_transform.py` に追記する。

```python
@pytest.mark.sphinx("revealjs", testroot="rst")
def test_rst_behaves_like_myst(app, warning):
    app.build()
    html = read_deck(app)
    assert html.count("<h2>Splitting</h2>") == 3
    assert html.count("<h2>Inline</h2>") == 1
    assert html.count("<h2>Trailing</h2>") == 2
    assert html.count("<h2>In list</h2>") == 1
    assert "not a direct child of a section" in warning.getvalue()
```

- [ ] **Step 3: テストを走らせる**

Run: `uv run pytest tests/test_transform.py::test_rst_behaves_like_myst -v`
Expected: **PASS**。これは特性化テストであり、実装の追加は不要。

FAIL した場合は spec の「記法非依存」という主張が誤っていることになる。実装を変えて通すのではなく、**まず失敗の内容を報告すること**。

- [ ] **Step 4: lint と型検査を通す**

Run: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
Expected: エラーなし

- [ ] **Step 5: コミット**

```bash
git add tests
git commit -m "test: hold the parser-independence claim with an rst test root"
```

---

### Task 6: CSS サンプルと README

**Files:**
- Create: `examples/slide-admonition.css`
- Create: `README.md`
- Test: `tests/test_examples.py`

**Interfaces:**
- Consumes: なし
- Produces: `examples/slide-admonition.css`（利用者がコピーして使うサンプル）

パッケージからの CSS 注入は行わない。テーマごとの見た目調整を背負わないためである。

- [ ] **Step 1: 失敗するテストを書く**

`.slide` 単独セレクタはデッキ全体のラッパー（`<div class="reveal slide ...">`）にも一致してしまう。サンプルがその規則を破っていないことをテストで保持する。

`tests/test_examples.py`:

```python
import re
from pathlib import Path

CSS = Path(__file__).parent.parent / "examples" / "slide-admonition.css"


def test_example_css_never_uses_a_bare_slide_selector():
    text = CSS.read_text(encoding="utf-8")
    bare = [
        match.group(0)
        for match in re.finditer(r"(?<![\w.-])\.slide\b", text)
        if not text[: match.start()].rstrip().endswith(".admonition")
    ]
    assert bare == [], f"bare .slide selector found: {bare}"
```

- [ ] **Step 2: テストを走らせて失敗を確認する**

Run: `uv run pytest tests/test_examples.py -v`
Expected: FAIL（`examples/slide-admonition.css` が存在せず `FileNotFoundError`）

- [ ] **Step 3: CSS サンプルを書く**

`examples/slide-admonition.css`:

```css
/*
 * Sample styling for admonitions turned into standalone slides.
 *
 * Copy this file into your Sphinx project's static directory and add it to
 * `revealjs_css_files` in conf.py:
 *
 *     revealjs_static_path = ["_static"]
 *     revealjs_css_files = ["slide-admonition.css"]
 *
 * Always use the compound selector `.admonition.slide`. A bare `.slide`
 * selector also matches the deck wrapper element, because Reveal.js puts the
 * transition name (`slide` by default) on `<div class="reveal slide ...">`.
 */

.reveal .admonition.slide {
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
  min-height: 60vh;
  padding: 1.2em 1.5em;
  border-left: 0.25em solid currentColor;
  border-radius: 0.2em;
  background: rgba(127, 127, 127, 0.12);
  text-align: left;
}

.reveal .admonition.slide > .admonition-title {
  margin: 0 0 0.6em;
  font-weight: 700;
  font-size: 1.1em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.75;
}

.reveal .admonition.slide > p:last-child {
  margin-bottom: 0;
}
```

- [ ] **Step 4: テストを走らせて成功を確認する**

Run: `uv run pytest tests/test_examples.py -v`
Expected: PASS

- [ ] **Step 5: README を書く（英語のみ）**

`README.md`:

````markdown
# sphinx-revealjs-admonitions

Render Sphinx admonitions as standalone [Reveal.js](https://revealjs.com/) slides
in decks built with [sphinx-revealjs](https://github.com/attakei/sphinx-revealjs).

Mark an admonition with `:class: slide` and it becomes its own slide, carrying
the section heading over from the slide it was written in.

## Installation

```console
pip install sphinx-revealjs-admonitions
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

A ready-made sample lives in [`examples/slide-admonition.css`](examples/slide-admonition.css).
Copy it into your static directory and wire it up:

```python
revealjs_static_path = ["_static"]
revealjs_css_files = ["slide-admonition.css"]
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
  This mirrors the behaviour without this extension.

## License

Apache-2.0
````

- [ ] **Step 6: lint と型検査を通す**

Run: `uv run ruff check --fix . && uv run ruff format . && uv run mypy .`
Expected: エラーなし

- [ ] **Step 7: テスト全体を走らせる**

Run: `uv run pytest -v`
Expected: 10 件すべて PASS

- [ ] **Step 8: コミット**

```bash
git add examples README.md tests
git commit -m "docs: add the css sample and the english readme"
```
