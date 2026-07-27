from __future__ import annotations

from ladon.analysis.audit_roles import finalize_audit_roles
from ladon.analysis.module_readiness import facade_rows


def test_command_only_audit_facade_replaces_pure_barrel_pressure() -> None:
    dag = fixture_dag()

    finalize_audit_roles(dag)

    row = dag["module_metadata"]["Pkg.AuditFacade"]
    assert row["facadeSubtype"] == "command_only_audit_facade"
    assert row["roles"] == [
        "facade",
        "command_only_audit_facade",
        "audit_surface",
    ]
    assert "pure_barrel" not in row["roles"]
    assert dag["facade_subtype_summary"] == {
        "command_only_audit_facade": 1,
        "generated_all": 1,
    }
    assert facade_rows(dag) == []


def test_isolated_and_mixed_audit_modules_do_not_gain_facade_roles() -> None:
    dag = fixture_dag()

    finalize_audit_roles(dag)

    isolated = dag["module_metadata"]["Pkg.Isolated"]
    assert isolated["roles"] == ["audit_surface"]
    assert isolated["facadeSubtype"] == ""
    mixed = dag["module_metadata"]["Pkg.Mixed"]
    assert mixed["roles"] == []
    assert mixed["facadeSubtype"] == ""


def test_generated_audit_aggregation_retains_owning_subtype() -> None:
    dag = fixture_dag()

    finalize_audit_roles(dag)

    generated = dag["module_metadata"]["Pkg.Generated.All"]
    assert generated["facadeSubtype"] == "generated_all"
    assert generated["roles"] == [
        "facade",
        "generated_all",
        "audit_surface",
    ]


def fixture_dag() -> dict:
    metadata = {
        "Pkg.AuditFacade": metadata_row(
            subtype="pure_barrel",
            roles=["facade", "pure_barrel"],
            imports=2,
        ),
        "Pkg.Isolated": metadata_row(),
        "Pkg.Mixed": metadata_row(declarations=1),
        "Pkg.Generated.All": metadata_row(
            subtype="generated_all",
            roles=["facade", "generated_all"],
            imports=4,
            tags=["generated"],
        ),
    }
    return {
        "module_metadata": metadata,
        "audit_surfaces": [
            audit_surface("Pkg.AuditFacade", command_only=True),
            audit_surface("Pkg.Isolated", command_only=True),
            audit_surface("Pkg.Mixed", command_only=False),
            audit_surface("Pkg.Generated.All", command_only=True),
        ],
        "facade_modules": ["Pkg.AuditFacade", "Pkg.Generated.All"],
        "facade_module_count": 2,
        "facade_subtype_summary": {
            "generated_all": 1,
            "pure_barrel": 1,
        },
        "top_facade_like_modules": [],
    }


def metadata_row(
    *,
    subtype: str = "",
    roles: list[str] | None = None,
    imports: int = 0,
    declarations: int = 0,
    tags: list[str] | None = None,
) -> dict:
    return {
        "path": "Pkg/Fixture.lean",
        "importCount": imports,
        "declarationCount": declarations,
        "tags": tags or [],
        "roles": roles or [],
        "facadeSubtype": subtype,
    }


def audit_surface(module: str, *, command_only: bool) -> dict:
    return {
        "module": module,
        "commandOnly": command_only,
        "auditCommands": [{"id": f"audit:{module}"}],
    }
