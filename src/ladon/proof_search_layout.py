"""Source ownership checks for the lexical SQLite inventory."""

from pathlib import Path

from ladon.lean_layout import (
    FATAL_OWNERSHIP_DIAGNOSTICS,
    SOURCE_LAYOUT_CONFIG,
    LeanSourceMap,
    discover_lean_source_map,
)


def discover_index_source_map(root: Path) -> LeanSourceMap:
    """Apply SQLite's resolved-path identity and reject unresolved ownership."""

    from ladon.proof_search_index import ProofSearchIndexError

    layout = discover_lean_source_map(root, resolve_paths=True)
    for diagnostic in layout.diagnostics:
        if diagnostic["id"] in FATAL_OWNERSHIP_DIAGNOSTICS:
            raise ProofSearchIndexError(
                diagnostic["message"],
                exit_class="operational",
                code=diagnostic["id"].rsplit(".", 1)[1].replace("_", "-"),
                remediation=(
                    f"Set [module_owners] in {SOURCE_LAYOUT_CONFIG} to select a "
                    "discovered module name for the source, or correct the Lake roots."
                ),
                details={
                    "path": diagnostic["subject"],
                    **{key: diagnostic[key] for key in ("candidateModules", "selectedModule")
                       if key in diagnostic},
                },
            )
    return layout
