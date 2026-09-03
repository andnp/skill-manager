---
name: python-style
description: "MANDATORY: Use this skill before writing or modifying any Python code—a new module, a single function, a one-line edit, a test helper, or a script. Also use it when reviewing Python, or when deciding whether a comment, docstring, nested block, or new helper belongs in a change. Triggers on any .py file, any Python snippet in a notebook or docs, and any request phrased as \"write/refactor/fix this Python\"."
---

# Python Style

House style for Python. It governs what does *not* get written—comments that
restate code, nesting that hides the happy path, helpers that already exist
somewhere in the repository.

## Comments and docstrings

- Default to no comment and no docstring. Add one only if it states a
  non-obvious WHY: a hidden constraint, a performance tradeoff with evidence, a
  subtle invariant. Never restate WHAT the code does.
- Never reference another function or line by name ("see `_resolve`",
  "caller's job (`load_all`)"). If the reader needs that context, it belongs in
  the shape of the code, not in a cross-reference that rots on the next rename.
- Don't bake in numbers likely to drift—a one-off profiling percentage, a
  benchmark from a single run. If a performance rationale is worth keeping,
  state it qualitatively.
- One line beats a paragraph. Cut until only the load-bearing sentence remains.
- Deleting a stale or redundant comment is part of editing the code it sits on,
  not a separate cleanup to defer.

```python
# no
def merge(base, overlay):
    """Merge overlay into base and return the result."""
    # iterate over the overlay keys
    for key, value in overlay.items():
        base[key] = value
    return base

# yes
def merge(base, overlay):
    # Callers hold references to `base`, so this mutates in place.
    for key, value in overlay.items():
        base[key] = value
    return base
```

## Nesting

- Avoid `for: if: else: for:` shapes. Flatten instead: split "collect" from
  "dispatch" into two passes, or use `continue` in place of `else` to drop a
  level.
- Avoid a long `if/else` where one branch is a one-liner and the other is a
  multi-statement block. Prefer an early-return guard for the simple case. If
  logic must run on both paths, pull it into a small helper called from each
  path—not a dangling `else`.

```python
# no
for item in items:
    if item.ready:
        for dep in item.deps:
            results.append(build(dep))
    else:
        skipped.append(item)

# yes
for item in items:
    if not item.ready:
        skipped.append(item)
        continue
    results.extend(build(dep) for dep in item.deps)
```

## Reuse before reinventing

- Before writing a recursive or tree-walking helper—flatten a nested dict, deep
  merge two structures, walk a path expression—search the repository's shared
  utilities first.
- Search by behavior, not by name: the existing helper is rarely called what you
  would have called it, and it is rarely in the file you are already editing.
- Don't duplicate logic that already exists elsewhere just because it isn't in
  view. If the existing helper is close but not quite right, extend it or say
  why it cannot be extended.
