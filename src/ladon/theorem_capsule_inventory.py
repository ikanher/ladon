"""Bounded source discovery for one theorem capsule.

The capsule path reuses Ladon's Lake layout, lexical declaration scanner, and
import parser, but it deliberately does not construct the report-facing source
index.  Planning retains source text only for the selected import closure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ladon.extraction import parse_import_sites
from ladon.ir import LeanTextDeclaration
from ladon.lean_layout import LeanSourceMap, discover_lean_source_map
from ladon.lexical_declarations import scan_text_declarations
from ladon.lexical_mask import mask_lean_source
from ladon.theorem_capsule_models import (
    CapsuleInvocationError,
    CapsuleOperationalError,
    canonical_json_bytes,
    sha256_bytes,
)


@dataclass(frozen=True)
class CapsuleLayout:
    """Small module-to-path inventory used by theorem-capsule planning."""

    root: Path
    source_map: LeanSourceMap
    paths: Mapping[str, str]
    fingerprint: str

    @property
    def modules(self) -> tuple[str, ...]:
        """Return stable repository module names."""

        return tuple(sorted(self.paths))

    def repository_payload(self) -> dict[str, Any]:
        """Return the stable, root-independent layout evidence."""

        return {
            "status": self.source_map.status,
            "sourceRoots": [
                source_root.to_dict(self.root)
                for source_root in self.source_map.roots
            ],
            "modules": [
                {"module": module, "path": self.paths[module]}
                for module in self.modules
            ],
        }


@dataclass(frozen=True)
class CapsuleSource:
    """Exact bytes and imports retained for one selected repository module."""

    module: str
    path: str
    content: bytes
    imports: tuple[str, ...]

    @property
    def source_sha256(self) -> str:
        """Return the exact source-byte identity."""

        return sha256_bytes(self.content)


@dataclass(frozen=True)
class LocatedTheorem:
    """One exact lexical theorem candidate and its owner source."""

    source: CapsuleSource
    declaration: LeanTextDeclaration


def discover_capsule_layout(repo_root: Path) -> CapsuleLayout:
    """Discover module ownership without retaining declaration-rich rows."""

    root = repo_root.resolve()
    try:
        source_map = discover_lean_source_map(root)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise CapsuleOperationalError(
            f"Lean source layout discovery failed: {exc}"
        ) from exc
    ambiguity = next(
        (
            row
            for row in source_map.diagnostics
            if row.get("id") == "lean.layout.ambiguous_module"
        ),
        None,
    )
    if ambiguity is not None:
        raise CapsuleOperationalError(str(ambiguity.get("message")))
    paths = {
        module: path.relative_to(root).as_posix()
        for module, path in source_map.modules.items()
    }
    stable = {
        "status": source_map.status,
        "sourceRoots": [
            source_root.to_dict(root) for source_root in source_map.roots
        ],
        "modules": [
            {"module": module, "path": paths[module]}
            for module in sorted(paths)
        ],
    }
    return CapsuleLayout(
        root=root,
        source_map=source_map,
        paths=paths,
        fingerprint=sha256_bytes(canonical_json_bytes(stable)),
    )


def locate_exact_theorem(
    layout: CapsuleLayout,
    theorem_name: str,
) -> LocatedTheorem:
    """Find one lexical candidate while parsing only plausible source files."""

    needle = theorem_name.rsplit(".", 1)[-1].encode("utf-8")
    candidates: list[LocatedTheorem] = []
    for module in layout.modules:
        path = layout.root / layout.paths[module]
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise CapsuleOperationalError(
                f"Lean source is unreadable: {layout.paths[module]}: {exc}"
            ) from exc
        if needle not in content:
            continue
        text = _decode_source(content, layout.paths[module])
        masked = mask_lean_source(text).lexical
        declarations = scan_text_declarations(
            text,
            masked,
            module=module,
            source_path=layout.paths[module],
        )
        for declaration in declarations:
            if declaration.candidate_name != theorem_name:
                continue
            candidates.append(
                LocatedTheorem(
                    source=_capsule_source(
                        module,
                        layout.paths[module],
                        content,
                        text,
                        masked,
                    ),
                    declaration=declaration,
                )
            )
    if not candidates:
        raise CapsuleInvocationError(
            f"no exact lexical source candidate exists for {theorem_name}"
        )
    if len(candidates) != 1:
        locations = ", ".join(
            f"{candidate.source.path}:{candidate.declaration.line}"
            for candidate in candidates[:5]
        )
        raise CapsuleInvocationError(
            f"ambiguous lexical source candidates for {theorem_name}: {locations}"
        )
    candidate = candidates[0]
    if candidate.declaration.block_end_offset is None:
        raise CapsuleOperationalError(
            f"source command boundary is unavailable for {theorem_name}"
        )
    return candidate


def repository_module_closure(
    layout: CapsuleLayout,
    root: CapsuleSource,
) -> dict[str, CapsuleSource]:
    """Read and retain only the repository import closure of ``root``."""

    selected = {root.module: root}
    pending = [
        imported
        for imported in root.imports
        if imported in layout.paths and imported != root.module
    ]
    while pending:
        module = pending.pop()
        if module in selected:
            continue
        source = read_capsule_source(layout, module)
        selected[module] = source
        pending.extend(
            imported
            for imported in source.imports
            if imported in layout.paths and imported not in selected
        )
    return dict(sorted(selected.items()))


def read_capsule_source(
    layout: CapsuleLayout,
    module: str,
) -> CapsuleSource:
    """Read one known module with exact bytes and bounded import evidence."""

    relative = layout.paths.get(module)
    if relative is None:
        raise CapsuleOperationalError(f"repository module closure lost {module}")
    try:
        content = (layout.root / relative).read_bytes()
    except OSError as exc:
        raise CapsuleOperationalError(
            f"Lean source is unreadable: {relative}: {exc}"
        ) from exc
    text = _decode_source(content, relative)
    return _capsule_source(
        module,
        relative,
        content,
        text,
        mask_lean_source(text).lexical,
    )


def source_inventory_fingerprint(
    layout: CapsuleLayout,
    sources: Mapping[str, CapsuleSource],
    configuration: tuple[dict[str, Any], ...],
) -> str:
    """Bind the selected source bytes, configuration, and module layout."""

    return sha256_bytes(
        canonical_json_bytes(
            {
                "layoutFingerprint": layout.fingerprint,
                "sources": [
                    {
                        "module": source.module,
                        "path": source.path,
                        "sha256": source.source_sha256,
                        "bytes": len(source.content),
                    }
                    for source in sources.values()
                ],
                "configuration": list(configuration),
            }
        )
    )


def verify_selected_sources(
    layout: CapsuleLayout,
    sources: Mapping[str, CapsuleSource],
) -> None:
    """Fail if selected bytes or module ownership drifted during planning."""

    current = discover_capsule_layout(layout.root)
    if current.fingerprint != layout.fingerprint:
        raise CapsuleOperationalError(
            "source module layout drifted during Lean theorem extraction"
        )
    for module, source in sources.items():
        if current.paths.get(module) != source.path:
            raise CapsuleOperationalError(
                f"source module ownership drifted during planning: {module}"
            )
        try:
            content = (layout.root / source.path).read_bytes()
        except OSError as exc:
            raise CapsuleOperationalError(
                f"selected source disappeared during planning: {source.path}"
            ) from exc
        if sha256_bytes(content) != source.source_sha256:
            raise CapsuleOperationalError(
                f"selected source drifted during planning: {source.path}"
            )


def _capsule_source(
    module: str,
    path: str,
    content: bytes,
    text: str,
    masked: str,
) -> CapsuleSource:
    imports = tuple(
        site.module for site in parse_import_sites(text, masked_text=masked)
    )
    return CapsuleSource(module, path, content, imports)


def _decode_source(content: bytes, path: str) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CapsuleOperationalError(
            f"Lean source is not UTF-8: {path}: {exc}"
        ) from exc


__all__ = [
    "CapsuleLayout",
    "CapsuleSource",
    "LocatedTheorem",
    "discover_capsule_layout",
    "locate_exact_theorem",
    "read_capsule_source",
    "repository_module_closure",
    "source_inventory_fingerprint",
    "verify_selected_sources",
]
