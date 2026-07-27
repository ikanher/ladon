from __future__ import annotations

from ladon.extraction import mask_lean_source
from ladon.lexical_command_skeleton import scan_command_skeleton


def skeleton_value(source: str) -> str:
    masks = mask_lean_source(source)
    rows = scan_command_skeleton(
        masks.command_shape,
        module="Demo",
        path="Demo.lean",
    )
    assert len(rows) == 1
    return rows[0].value


def test_mask_preserves_offsets_across_lean_literal_forms() -> None:
    source = """\
def raw := r##"set_option maxHeartbeats 0 /- hidden -/"##
def char := '-'
def named := «space name»
theorem visible : True := by trivial
"""

    masks = mask_lean_source(source)

    assert len(masks.lexical) == len(source)
    assert len(masks.command_shape) == len(source)
    assert [
        index for index, char in enumerate(masks.lexical) if char == "\n"
    ] == [index for index, char in enumerate(source) if char == "\n"]
    assert "maxHeartbeats" not in masks.lexical
    assert "space name" not in masks.lexical
    assert "«space name»" in masks.command_shape
    assert "theorem visible" in masks.lexical


def test_identifier_and_operator_boundaries_remain_significant() -> None:
    assert skeleton_value("#check α42\n") != skeleton_value("#check α 42\n")
    assert skeleton_value("#check foo!\n") != skeleton_value("#check foo !\n")
    assert skeleton_value("#check «foo bar»\n") != skeleton_value(
        "#check «foo  bar»\n"
    )
    assert skeleton_value("#check %%%\n") != skeleton_value("#check % % %\n")


def test_numeric_spellings_and_unicode_serials_normalize() -> None:
    assert skeleton_value("#eval 15\n") == skeleton_value("#eval 0o17\n")
    assert skeleton_value("#check f₁\n") == skeleton_value("#check f₂\n")


def test_literal_contents_normalize_without_swallowing_following_commands() -> None:
    assert skeleton_value("def x := 'a'\n") == skeleton_value("def x := 'β'\n")
    assert skeleton_value('def x := r##"first"##\n') == skeleton_value(
        'def x := r##"second"##\n'
    )
    assert skeleton_value('def x := r##"first"##\n#check Nat\n') != (
        skeleton_value('def x := r##"second"##\n#check Bool\n')
    )
