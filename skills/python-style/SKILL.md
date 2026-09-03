---
name: python-style
description: "MANDATORY: Use this skill before writing or modifying any Python code—a new module, a single function, a one-line edit, a test, or a script. Also use it when reviewing Python, or when deciding whether a comment, docstring, annotation, nested block, or new helper belongs in a change. Triggers on any .py file, any Python snippet in a notebook or docs, and any request phrased as \"write/refactor/fix this Python\"."
---

# Python Style

House style. Existing repository conventions win where they conflict.

## Comments and docstrings

- Default to none. Add one only for a non-obvious WHY: a hidden constraint, a
  perf tradeoff with evidence, a subtle invariant. Never restate WHAT.
- Never name another function or line ("see `_resolve`", "caller's job"). If the
  reader needs that context, it belongs in the code shape.
- No numbers that drift—a one-off profiling percentage, a single-run benchmark.
  State a perf rationale qualitatively or not at all.
- One line beats a paragraph. Cut to the load-bearing sentence.
- Deleting a stale comment is part of editing the code under it.
- No docstrings unless asked. No Google-style unless the repo already uses it.

## Typing

- Annotate inputs always. Never annotate return types—rely on inference.
- Avoid `Any`.
- No `# type: ignore` or other suppressions. When one looks necessary, trace the
  value backward to where its type was widened or erased: an `object`/`Any`
  container upstream, a generic returned without its type arguments, a test
  double returning `object`. Fix it there; the suppression often hides a bug.
- Built-in generics: `list[str]`, not `List[str]`. `X | None`, not `Optional[X]`.
- Alias numeric unions (`IntLike = int | np.integer`). Convert numpy scalars to
  native types at the boundary: `idx = int(idx)`.

## Language use

- Avoid `hasattr` and `getattr`.
- Imports at the top of the file, never inside a function.
- No `__init__.py` exports.

## Nesting

- Avoid `for: if: else: for:`. Flatten: split collect from dispatch into two
  passes, or `continue` instead of `else` to drop a level.
- Avoid a long `if/else` where one branch is a one-liner and the other a block.
  Use an early-return guard for the simple case; if logic must run on both
  paths, pull it into a helper called from each—not a dangling `else`.

## Reuse before reinventing

- Before writing a recursive or tree-walking helper—flatten a nested dict, deep
  merge, walk a path expression—search the repo's shared utilities.
- Search by behavior, not name. The helper is rarely called what you'd call it,
  and rarely in the file you're editing.
- Extend a near-miss helper, or say why it can't be extended.

## Design

- Inject dependencies from outside; centralize construction in factories.
- Protocol-based strategies for swappable components. Composition over
  inheritance.
- No hidden instantiation of mutable storage.

## Tests

- Never `patch` or `mock` unless asked. `monkeypatch` only for env vars.
- Every test gets a brief multiline docstring: what it verifies, plus why if
  useful. No docstrings on fixtures or helpers.
- Group tests semantically, in classes or under header comments.
- `np.allclose` / `jnp.allclose` over `np.testing.assert_allclose`.
- Numeric code: deterministic seeds, shape assertions, boolean params exercised
  both ways, nested-JIT paths covered.

## Tooling

- Never run `ruff format`. `ruff check` and `ruff check --fix` only.
- Establish a baseline before calling a static-analysis finding pre-existing—CI
  on the prior SHA, or stash and rerun.
