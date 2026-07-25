from __future__ import annotations

import json

import pytest

from ladon.analysis.audit_surface import extract_audit_surface


def test_extracts_stable_bounded_audit_commands() -> None:
    source = (
        "import Pkg.Owner\n"
        "#check Pkg.Owner.someVeryLongDeclaration\n"
        "#print axioms Pkg.Owner.someVeryLongDeclaration\n"
    )

    first = extract_audit_surface(
        "Pkg.Audit",
        "Pkg/Audit.lean",
        source,
        declaration_count=0,
        subject_limit=18,
    )
    second = extract_audit_surface(
        "Pkg.Audit",
        "Pkg/Audit.lean",
        source,
        declaration_count=0,
        subject_limit=18,
    )

    assert {
        "commandOnly": first.command_only,
        "kinds": [row.kind for row in first.commands],
        "truncated": [row.subject_truncated for row in first.commands],
        "totalCharacters": [
            row.subject_total_characters for row in first.commands
        ],
        "authorities": [row.authority for row in first.commands],
        "referencedDeclarations": [
            row.referenced_declaration for row in first.commands
        ],
        "resultStatuses": [row.result_status for row in first.commands],
        "nonclaimPrefixes": [
            row.nonclaim.split(";", 1)[0] for row in first.commands
        ],
    } == {
        "commandOnly": True,
        "kinds": ["check", "print_axioms"],
        "truncated": [True, True],
        "totalCharacters": [
            len("Pkg.Owner.someVeryLongDeclaration"),
            len("Pkg.Owner.someVeryLongDeclaration"),
        ],
        "authorities": ["lexical_text", "lexical_text"],
        "referencedDeclarations": [None, None],
        "resultStatuses": ["unavailable", "unavailable"],
        "nonclaimPrefixes": [
            "Lexical #check intent only",
            "Lexical #print axioms intent only",
        ],
    }
    assert first.to_dict() == second.to_dict()
    assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(
        second.to_dict(),
        sort_keys=True,
    )


def test_comments_and_strings_do_not_create_audit_rows() -> None:
    source = (
        '-- "#check Pkg.Commented"\n'
        '/- #print axioms Pkg.Blocked /- #check Pkg.Nested -/ -/\n'
        'def text := "#print axioms Pkg.String"\n'
        "#check Pkg.Real -- #check Pkg.Trailing\n"
    )

    surface = extract_audit_surface(
        "Pkg.Audit",
        "Pkg/Audit.lean",
        source,
        declaration_count=1,
    )

    assert surface.command_only is False
    assert len(surface.commands) == 1
    assert surface.commands[0].subject == "Pkg.Real"
    assert surface.commands[0].source_range.start.line == 4
    assert surface.commands[0].source_range.start.column == 1


def test_string_only_subject_is_preserved_as_honest_unparsed_command() -> None:
    surface = extract_audit_surface(
        "Pkg.Audit",
        "Pkg/Audit.lean",
        '#check "not a declaration identity"\n',
        declaration_count=0,
    )

    row = surface.commands[0]
    assert row.status == "unparsed"
    assert row.subject == ""
    assert row.diagnostics[0].code == "audit.subject_unparsed"
    assert row.referenced_declaration is None


def test_resource_directives_preserve_value_scope_and_nonclaims() -> None:
    source = (
        "set_option maxHeartbeats 250000 in\n"
        "theorem bounded : True := by trivial\n"
        "set_option maxHeartbeats 0\n"
        "set_option maxRecDepth 4096\n"
    )

    surface = extract_audit_surface(
        "Pkg.Owner",
        "Pkg/Owner.lean",
        source,
        declaration_count=1,
    )
    heartbeat_local, heartbeat_unlimited, recursion = surface.resource_directives

    assert {
        "local": (
            heartbeat_local.numeric_value,
            heartbeat_local.normalized_meaning,
            heartbeat_local.lexical_scope,
        ),
        "unlimited": (
            heartbeat_unlimited.raw_value,
            heartbeat_unlimited.normalized_meaning,
            heartbeat_unlimited.lexical_scope,
        ),
        "recursion": (
            recursion.option,
            recursion.numeric_value,
            recursion.normalized_meaning,
        ),
        "nonclaims": [
            "not measured runtime" in row.nonclaim
            for row in surface.resource_directives
        ],
    } == {
        "local": (250000, "finite", "command_local"),
        "unlimited": ("0", "unlimited", "module"),
        "recursion": ("maxRecDepth", 4096, "finite"),
        "nonclaims": [True, True, True],
    }


def test_unsupported_resource_expression_is_explicitly_unparsed() -> None:
    source = (
        "set_option maxHeartbeats budget * 2 in theorem x : True := by trivial\n"
        "-- set_option maxRecDepth 9999\n"
        'def text := "set_option maxHeartbeats 0"\n'
    )

    surface = extract_audit_surface(
        "Pkg.Owner",
        "Pkg/Owner.lean",
        source,
        declaration_count=2,
    )

    assert len(surface.resource_directives) == 1
    row = surface.resource_directives[0]
    assert row.raw_value == "budget * 2"
    assert row.numeric_value is None
    assert row.normalized_meaning is None
    assert row.lexical_scope == "command_local"
    assert row.status == "unparsed"
    assert row.diagnostics[0].code == "audit.resource_value_unparsed"


def test_repeated_subjects_keep_distinct_source_anchored_identities() -> None:
    surface = extract_audit_surface(
        "Pkg.Audit",
        "Pkg/Audit.lean",
        "#check Pkg.Owner.x\n#check Pkg.Owner.x\n",
        declaration_count=0,
    )

    assert len({row.identifier for row in surface.commands}) == 2
    assert [row.source_range.start.line for row in surface.commands] == [1, 2]


@pytest.mark.parametrize(
    ("module", "path", "declaration_count", "subject_limit"),
    [
        ("", "Pkg/Audit.lean", 0, 10),
        ("Pkg.Audit", "/tmp/Audit.lean", 0, 10),
        ("Pkg.Audit", "../Audit.lean", 0, 10),
        ("Pkg.Audit", "Pkg/Audit.lean", -1, 10),
        ("Pkg.Audit", "Pkg/Audit.lean", 0, 0),
    ],
)
def test_audit_surface_rejects_unstable_input_identity(
    module: str,
    path: str,
    declaration_count: int,
    subject_limit: int,
) -> None:
    with pytest.raises(ValueError):
        extract_audit_surface(
            module,
            path,
            "#check Pkg.Owner.x\n",
            declaration_count=declaration_count,
            subject_limit=subject_limit,
        )
