# admonition を 1 枚のスライドとして扱う拡張 — 設計

- 日付: 2026-08-29
- パッケージ: `sphinx-revealjs-admonitions`
- リポジトリ: <https://github.com/drillan/sphinx-revealjs-admonitions>

## 1. 目的

sphinx-revealjs で作るスライドにおいて、admonition ディレクティブ（`note`、`warning` など）を
**独立した 1 枚のスライドとして表示する**手段を提供する。

対象は、現在は admonition が本文の途中に埋め込まれてしまい、
1 枚使って見せたい注意書きや補足をスライドとして独立させられない、という不便である。

## 2. 実現機構

### 2.1 スタイルだけでは実現できない

Reveal.js のスライドは `<section>` 要素そのものであり、
キー操作・進行状況・fragment はすべてこの DOM 構造から駆動される。
CSS には `<section>` を生成する手段がないため、スタイル単独では
「既存スライド内で admonition を全画面カード風に見せる」ところまでしかできない。
本設計が目的とする「独立したスライド」には DOM の分割が必須である。

### 2.2 採用する機構

sphinx-revealjs の `revealjs-break` ディレクティブは、対応する `revealjs_break` ノードの
visit で `</section>` を 1 つ閉じ、depart で `<section>` を 1 つ開き、
さらに親 section の title を再描画する。

本拡張は **doctree の post-transform で、対象 admonition の前後に `revealjs_break` ノードを
兄弟として挿入する**。これにより、

- タグの開閉数が、作者が手書きした `revealjs-break` と完全に一致する
- 分割後スライドへの見出し引き継ぎが既存実装のまま得られる
- sphinx-revealjs 本体への変更が一切不要である

`revealjs_break` は `sphinx_revealjs.nodes` から import できるため、外部パッケージで完結する。

### 2.3 ラップではなく兄弟挿入である理由

`depart_revealjs_break` は `node.parent.first_child_matching_class(title)` を参照する。
admonition をコンテナで包むと親が section でなくなり、見出しの引き継ぎが機能しない。
したがって挿入位置は「admonition と同じ親の、admonition の直前・直後」でなければならない。

## 3. 公開仕様

### 3.1 有効化

```python
# conf.py
extensions = ["sphinx_revealjs", "sphinx_revealjs_admonitions"]
```

スライドのビルド手順は変わらない。`sphinx-build -b revealjs` のままであり、
post-transform であるため追加のビルドステップも中間生成物も発生しない。

### 3.2 記法

admonition の `:class:` オプションにマーカー `slide` を指定する。

MyST:

```markdown
:::{note}
:class: slide

この note が独立したスライドになる
:::
```

reStructuredText:

```rst
.. note::
   :class: slide

   この note が独立したスライドになる
```

MyST と RST はどちらも同一の docutils ノードを生成するため、記法による差はない。

### 3.3 マーカー名

マーカーは文字列 `slide` に固定する。conf.py の設定項目にはしない。
クラス名を可変にする利得がなく、設定面を増やすだけであるため。

`slide` は Reveal.js がラッパー要素（`<div class="reveal slide ...">`、
既定 transition が `slide` のため通常は必ず付く）に用いるクラス名でもある。
ただし reveal.css 内の該当セレクタは `.reveal.slide ...` の 4 つのみで、
`.reveal` と同一要素であることを要求するため、配下の admonition には一致しない。
既存スタイルが壊れる経路はない。

一方で、本拡張向けのスタイルを `.slide { ... }` と書くとデッキ全体のラッパーにも当たる。
**スタイルは必ず `.admonition.slide` の複合セレクタで書く**こと。README に明記する。

### 3.4 対象ノード

`docutils.nodes.Admonition` のインスタンスで、クラス属性に `slide` を持つもの。

実際にマーカーを指定できるのは `:class:` オプションを持つディレクティブであり、
以下が該当する。

`note` / `warning` / `tip` / `danger` / `caution` / `attention` / `error` /
`hint` / `important` / `seealso` / 汎用 `admonition`

`versionadded` / `deprecated` が生成する `versionmodified` ノードは
`nodes.Admonition` の派生だが、これらのディレクティブは `:class:` オプションを持たない。
`:class: slide` と書いても本文テキストとして出力されるだけで、マーカーは付与できない。
**対象外**として README に明記する。

## 4. 内部設計

`SphinxPostTransform` のサブクラス 1 つで構成する。

### 4.1 ビルダーの限定

```python
builders = ("revealjs", "dirrevealjs")
```

`RevealjsHTMLBuilder` は `format` を上書きせず `StandaloneHTMLBuilder` から `"html"` を継承する。
`formats = ("html",)` で限定すると通常の HTML ビルドでも発火し、出力を破壊する。
必ず `builders` で限定する。

### 4.2 優先度

```python
default_priority = 450
```

400 は latex ビルダーの post-transform 4 つが占有している。
ビルダーが異なるため実害はないが、同値の実行順序は未定義であるため未使用の値を選ぶ。

### 4.3 変換規則

対象 admonition ごとに以下を行う。

1. 親が `nodes.section` でない場合は警告を出し、そのノードは変換しない（4.5 参照）
2. 親の子リストにおける admonition の位置を求める
3. 後続の兄弟に**可視ノードが 1 つ以上ある場合のみ**、admonition の直後に `revealjs_break()` を挿入
4. admonition の直前に `revealjs_break()` を挿入

挿入は後方から先に行う。前方を先に挿入すると位置がずれるため。

### 4.4 可視判定

後続の兄弟が不可視ノードだけの場合に後方の break を挿すと、
見出しだけの空スライドが生成される。これを避けるため、以下を不可視として扱う。

- `docutils.nodes.Invisible` の派生（`comment`、`target`、`substitution_definition`、
  `pending`、`sphinx.addnodes.index` がいずれも該当する）
- `docutils.nodes.system_message`（`Invisible` の派生ではないため個別に列挙する）

`comment` は `revealjs_notes_from_comments = True` のとき `<aside class="notes">` を出力するが、
話者ノートは直前のスライドに属するのが正しい挙動であるため、不可視扱いで問題ない。

### 4.5 エラー処理

親が `nodes.section` でない場合（リスト項目内、引用ブロック内など）、
挿入した `</section>` は意図しない祖先を閉じることになる。この構成は**非対応**とする。

このとき `logger.warning` を出し、当該 admonition は変換しない。
既定値で処理を続行することはせず、利用者に必ず可視化する。
`-W` 付きのビルドではエラーとして扱われる。

### 4.6 深い見出しの扱い

sphinx-revealjs の writer は `section_level >= 4` でスライドを開かない。
この深さにある admonition にマーカーを付けた場合、挿入した break は
最も近い開いているスライド（level 3 のもの）を閉じて開き直す。

検証の結果、開閉数は釣り合い、出力も破綻しない。
後続の兄弟セクションが分割後スライドに吸収されるが、
これは変換前と同じ意味論である（level 4 以深の見出しは元々スライドを作らない）。

**現状の動作をそのまま許容し、警告も出さない。**正しく動作するものへの警告はノイズにしかならない。

## 5. パッケージ構成

```
sphinx-revealjs-admonitions/
├── pyproject.toml
├── src/sphinx_revealjs_admonitions/
│   ├── __init__.py          # setup()
│   └── transform.py         # AdmonitionToSlide
├── examples/
│   └── slide-admonition.css
├── tests/
│   ├── conftest.py
│   ├── roots/test-myst/
│   ├── roots/test-rst/
│   └── test_transform.py
├── README.md
└── LICENSE
```

- build backend: `uv_build`（同一メンテナの `sphinx-oceanid` と運用を揃える。
  sphinx-revealjs 本体は `flit_core` + Taskfile + aqua + lefthook だが、これは本家の運用都合であり追随しない）
- `requires-python = ">=3.13"`
- `dependencies = ["sphinx-revealjs>=3.2,<4"]`
- 開発依存: `pytest`、`myst-parser`、`ruff`、`mypy`
- `myst-parser` は**実行時依存にしない**。RST だけでも動作するため

### 5.1 依存の上限を固定する理由

本拡張は `revealjs_break` ノードと writer のセクション処理という、
sphinx-revealjs のバージョニングポリシーが保護対象として宣言していない内部実装に依存する。
`doc/api.rst` は autodoc のみで、公開 API の契約が文書化されていない。
メジャー更新で壊れうる前提を置き、上限を `<4` で固定し、テストで実際の破綻を検知する。

## 6. テスト計画

`sphinx.testing` のフィクスチャを使い、実際にビルドした HTML を検査する。
`conftest.py` に `pytest_plugins = "sphinx.testing.fixtures"` と `rootdir` フィクスチャを置く。

`transform.py` に 1 対 1 で対応する `tests/test_transform.py` に以下を置く。

1. マーカー付き admonition が、前・admonition・後の 3 スライドに分割される
2. マーカーのない admonition は分割されない
3. section 末尾のマーカー付き admonition で、見出しだけの空スライドが生成されない
4. 後続が不可視ノード（コメント）だけの場合も空スライドが生成されない
5. リスト項目内のマーカー付き admonition で警告が出て、分割されない
6. RST フィクスチャが MyST フィクスチャと同一の分割結果になる
7. `-b html` ビルドでは transform が発火せず、出力が変わらない
8. `<section>` の開閉数が、変換なしのビルドに対して挿入した break の数だけ増える

6 は「記法非依存」という主張をテストとして保持するために置く。

## 7. CSS サンプル

`examples/slide-admonition.css` に、`.admonition.slide` を全画面カード風に見せる例を置く。
パッケージからの注入は行わない。利用者が `_static` にコピーし、
`revealjs_css_files` に追加して使う。README にその手順と、
`.slide` 単独セレクタを使ってはならない理由（3.3 参照）を記載する。

同梱・自動注入を選ばないのは、テーマ（black / white / カスタム）ごとの
見た目調整を背負わないためである。

## 8. ドキュメント

README.md は**英語のみ**とする。PyPI の説明文としてそのまま使う。

記載内容: 機能の説明、インストール、conf.py の設定、MyST と RST の記法例、
CSS サンプルの適用手順、制約（9 章）。

## 9. 既知の制約

- リスト項目内など、section の直接の子でない admonition は分割できない（警告を出す）
- `versionadded` / `deprecated` はマーカーを指定できないため対象外
- 分割後のスライドには id が付かないため、個別スライドへのリンクは張れない
  （既存の `revealjs-break` と同じ制約）
- level 4 以深の見出し配下では、後続の兄弟セクションが分割後スライドに吸収される

## 10. スコープ外

- マーカー名の設定項目化
- CSS の同梱・自動注入
- admonition の種類ごとの背景色・アイコン
- level 4 以深の特別扱い

## 付録: 検証済み事実

sphinx-revealjs 3.2.1（PyPI リリース版）、Sphinx 9.1.0 で確認した。

| 確認項目 | 結果 |
|---|---|
| ビルダー限定 | `RevealjsHTMLBuilder` は `format` を上書きせず `"html"` を継承。`builders` での限定が必要 |
| ノード判定 | `isinstance(node, nodes.Admonition)` が note/warning/tip/danger/caution/attention/error/hint/important/seealso/汎用 admonition/versionmodified を捕捉 |
| `versionadded` | `:class:` オプションを持たず、マーカー指定不可 |
| タグ釣り合い | 水平スライド・縦積み・level 4 以深のすべてで、挿入した break 1 つにつき開閉が +1 ずつ |
| 空スライド | 末尾 admonition、および後続が不可視ノードだけの場合に生成されないことを確認 |
| id 重複 | `revealjs_use_section_ids = True` でも重複なし。分割後スライドには id が付かない |
| html ビルダー | `builders` 限定により発火せず、admonition が通常どおり出力される |
| 非 section 親 | リスト項目内で警告が出て、分割されないことを確認 |
| 優先度 | 400 は latex ビルダーの 4 つが占有。450 は未使用 |
| reveal.css | `.reveal.slide ...` の 4 セレクタのみ。単独 `.slide` セレクタは 0 件 |
