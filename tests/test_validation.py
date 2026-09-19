from pathlib import Path

from skill_manager.validation import validate


def _write_skill(root: Path, name: str, description: str, invocation: str | None = None) -> None:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    frontmatter = f'name: {name}\ndescription: "{description}"\n'
    if invocation is not None:
        frontmatter += f"invocation: {invocation}\n"
    (skill / "SKILL.md").write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")


def test_validate_accepts_manual_skill_with_prefix_and_clause(tmp_path: Path):
    """A manual-invocation skill passes when prefixed and carrying the clause."""
    _write_skill(
        tmp_path,
        "p_demo",
        "Do the thing. Invoke only when explicitly requested by name; do not self-trigger.",
        invocation="manual",
    )

    result = validate(tmp_path)

    assert result.valid, result.errors


def test_validate_rejects_manual_skill_missing_prefix(tmp_path: Path):
    """A manual-invocation skill without the 'p_' prefix fails validation."""
    _write_skill(
        tmp_path,
        "demo",
        "Do the thing. Invoke only when explicitly requested by name; do not self-trigger.",
        invocation="manual",
    )

    result = validate(tmp_path)

    assert not result.valid
    assert any("must be prefixed 'p_'" in error for error in result.errors)


def test_validate_rejects_manual_skill_missing_clause(tmp_path: Path):
    """A manual-invocation skill without the standard clause fails validation."""
    _write_skill(tmp_path, "p_demo", "Do the thing.", invocation="manual")

    result = validate(tmp_path)

    assert not result.valid
    assert any("manual clause" in error for error in result.errors)


def test_validate_rejects_auto_skill_with_prefix(tmp_path: Path):
    """An auto-invocation skill must not use the 'p_' prefix."""
    _write_skill(tmp_path, "p_demo", "Do the thing.")

    result = validate(tmp_path)

    assert not result.valid
    assert any("must not use the 'p_' prefix" in error for error in result.errors)


def test_validate_rejects_unknown_invocation_value(tmp_path: Path):
    """An invocation value outside auto/manual fails validation."""
    _write_skill(tmp_path, "demo", "Do the thing.", invocation="sometimes")

    result = validate(tmp_path)

    assert not result.valid
    assert any("invalid invocation" in error for error in result.errors)


def test_validate_accepts_default_auto_skill(tmp_path: Path):
    """A skill with no invocation field defaults to auto and needs no prefix."""
    _write_skill(tmp_path, "demo", "Do the thing.")

    result = validate(tmp_path)

    assert result.valid, result.errors
