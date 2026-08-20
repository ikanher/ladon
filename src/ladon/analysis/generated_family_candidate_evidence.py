"""Canonical source evidence preparation for numbered-module candidates."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import groupby
from pathlib import PurePosixPath

from ladon.analysis.generated_family_candidate_models import (
    CandidateMember,
    CandidateModuleEvidence,
    CandidateSourceAnchor,
)
from ladon.analysis.generated_family_candidate_profile import (
    COMMAND_SKELETON_VERSION,
    DECLARATION_STEM_VERSION,
    GROUPING_SUFFIX_WIDTH_VERSION,
    GROUPING_VERSION,
)
from ladon.ir import LeanModule, LeanTextDeclaration

NUMBERED_BASENAME_RE = re.compile(r"^(?P<prefix>.+?)(?P<suffix>[0-9]+)$")
IDENTIFIER_COMPONENT_RE = re.compile(r"[^\W_]+")
LOWER_ASCII_IDENTIFIER_RE = re.compile(r"[a-z0-9_']*\Z")
LOWER_ASCII_TOKEN_RE = re.compile(r"[a-z]+|[0-9]+")
INTERNAL_IMPORT_VERSION = "direct-internal-import-v1"
CONTENT_HASH_VERSION = "source-content-sha256-v1"
DECLARATION_BLOCK_HASH_VERSION = "normalized-declaration-block-hash-v1"
PartitionKey = tuple[str, str, int | None]


@dataclass(frozen=True)
class NumberedPath:
    """Normalized numbered basename and its structural parent."""

    parent: str
    prefix: str
    suffix_value: int
    suffix_spelling: str


@dataclass(frozen=True)
class PreparedMember:
    """Public member evidence plus bounded aggregation inputs."""

    public: CandidateMember
    declaration_anchors: tuple[tuple[str, LeanTextDeclaration], ...]
    block_hash_versions: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class AggregateInput:
    """One member-local feature contribution before partition aggregation."""

    kind: str
    version: str
    value: str
    authority: str
    member_id: str
    anchor: CandidateSourceAnchor | None = None


def declaration_stem_v1(name: str) -> str | None:
    """Normalize one local declaration name into a lexical stem.

    Namespace components are discarded.  Underscore and apostrophe separators,
    Unicode case transitions and all letter/digit transitions form token
    boundaries. Digit tokens become ``<number>``; other spelling is retained.
    """

    local_name = name.rsplit(".", 1)[-1]
    if local_name.isascii() and LOWER_ASCII_IDENTIFIER_RE.fullmatch(local_name):
        return _lower_ascii_declaration_stem(local_name)
    tokens = [
        token
        for chunk in re.split(r"[_']+", local_name)
        for token in _identifier_tokens(chunk)
    ]
    if not tokens:
        return None
    normalized = [
        "<number>" if token.isdigit() else token
        for token in tokens
    ]
    return "_".join(normalized)


def _lower_ascii_declaration_stem(name: str) -> str | None:
    """Normalize the common lowercase ASCII case in compiled regex loops."""

    tokens = [
        "<number>" if token[0].isdigit() else token
        for token in LOWER_ASCII_TOKEN_RE.findall(name)
    ]
    return "_".join(tokens) if tokens else None


def _identifier_tokens(chunk: str) -> Iterable[str]:
    """Yield Unicode-safe digit and case-transition tokens."""

    for component in IDENTIFIER_COMPONENT_RE.findall(chunk):
        for digits, characters in groupby(component, key=str.isdigit):
            token = "".join(characters)
            if digits:
                yield token
            else:
                yield from _case_transition_tokens(token)


def _case_transition_tokens(token: str) -> Iterable[str]:
    """Split lower/upper and acronym/word boundaries without ASCII loss."""

    start = 0
    for index in range(1, len(token)):
        previous = token[index - 1]
        current = token[index]
        following = token[index + 1] if index + 1 < len(token) else ""
        if current.isupper() and (
            previous.islower()
            or (previous.isupper() and following.islower())
        ):
            yield token[start:index]
            start = index
    yield token[start:]


def candidate_module_evidence(
    modules: Mapping[str, LeanModule],
    *,
    populations: Mapping[str, str] | None = None,
    content_hashes: Mapping[str, str] | None = None,
    command_skeletons: Mapping[str, Sequence[str]] | None = None,
    incomplete_structural_modules: Collection[str] = (),
    incomplete_import_modules: Collection[str] = (),
    incomplete_lexical_modules: Collection[str] = (),
) -> tuple[CandidateModuleEvidence, ...]:
    """Adapt existing ``LeanModule`` rows without rescanning source text."""

    module_names = frozenset(modules)
    _validate_module_mapping(modules)
    _validate_optional_keys(populations, module_names, "population")
    _validate_optional_keys(content_hashes, module_names, "content hash")
    _validate_optional_keys(
        command_skeletons,
        module_names,
        "command skeleton",
    )
    incomplete_structural = _validated_module_names(
        incomplete_structural_modules,
        module_names,
        "structural completeness",
    )
    incomplete_imports = _validated_module_names(
        incomplete_import_modules,
        module_names,
        "import completeness",
    )
    incomplete_lexical = _validated_module_names(
        incomplete_lexical_modules,
        module_names,
        "lexical completeness",
    )
    return tuple(
        CandidateModuleEvidence(
            module=module,
            population=_population_for(name, populations),
            content_sha256=_optional_value(name, content_hashes),
            command_skeletons=_command_skeletons_for(
                name,
                command_skeletons,
            ),
            structural_complete=name not in incomplete_structural,
            imports_complete=name not in incomplete_imports,
            lexical_complete=name not in incomplete_lexical,
        )
        for name, module in sorted(modules.items())
    )


def validate_evidence_population(
    evidence: tuple[CandidateModuleEvidence, ...],
) -> None:
    """Reject duplicate canonical module or path identities."""

    names = [row.module.name for row in evidence]
    paths = [row.module.path for row in evidence]
    if len(names) != len(set(names)):
        raise ValueError("candidate evidence contains duplicate modules")
    if len(paths) != len(set(paths)):
        raise ValueError("candidate evidence contains duplicate paths")


def internal_module_universe(
    rows: tuple[CandidateModuleEvidence, ...],
    module_names: Collection[str] | None,
) -> frozenset[str]:
    """Resolve the import-membership universe without adding candidates."""

    selected = frozenset(row.module.name for row in rows)
    if module_names is None:
        return selected
    internal = frozenset(_normalized_internal_module_names(module_names))
    missing = sorted(selected - internal)
    if missing:
        raise ValueError(
            "internal module universe omits candidate modules: "
            + ", ".join(missing)
        )
    return internal


def internal_module_universe_fingerprint(
    module_names: Collection[str],
) -> str:
    """Fingerprint the identities used only for internal-import membership."""

    normalized = _normalized_internal_module_names(module_names)
    payload = {
        "version": "generated-family-internal-module-universe-v1",
        "modules": list(normalized),
    }
    return stable_digest(payload)


def prepare_members(
    rows: Iterable[CandidateModuleEvidence],
    internal_modules: frozenset[str],
) -> tuple[PreparedMember, ...]:
    """Prepare candidate members from already extracted evidence."""

    return tuple(
        _prepare_member(row, internal_modules)
        for row in rows
    )


def partition_members(
    members: tuple[PreparedMember, ...],
    *,
    grouping_version: str = GROUPING_VERSION,
) -> tuple[
    dict[PartitionKey, tuple[PreparedMember, ...]],
    tuple[PreparedMember, ...],
]:
    """Partition valid numbered paths and retain all ungrouped members."""

    groups: defaultdict[
        PartitionKey,
        list[PreparedMember],
    ] = defaultdict(list)
    ungrouped: list[PreparedMember] = []
    for member in members:
        key = numbered_partition_key(
            member.public,
            grouping_version=grouping_version,
        )
        if key is None:
            ungrouped.append(member)
        else:
            groups[key].append(member)
    return (
        {
            key: tuple(sorted(value, key=member_sort_key))
            for key, value in groups.items()
        },
        tuple(sorted(ungrouped, key=lambda row: row.public.identifier)),
    )


def numbered_partition_key(
    member: CandidateMember,
    *,
    grouping_version: str = GROUPING_VERSION,
) -> PartitionKey | None:
    """Return the exact structural partition key for a numbered member."""

    if (
        member.parent is None
        or member.basename_prefix is None
        or member.suffix_value is None
    ):
        return None
    if grouping_version == GROUPING_VERSION:
        return member.parent, member.basename_prefix, None
    if grouping_version == GROUPING_SUFFIX_WIDTH_VERSION:
        spelling = member.suffix_spelling
        if spelling is None:
            return None
        return member.parent, member.basename_prefix, len(spelling)
    raise ValueError(f"unsupported candidate grouping version {grouping_version!r}")


def member_feature_inputs(
    member: PreparedMember,
) -> Iterable[AggregateInput]:
    """Yield canonical aggregate contributions for one prepared member."""

    public = member.public
    yield from (
        AggregateInput(
            kind="direct_internal_import",
            version=INTERNAL_IMPORT_VERSION,
            value=value,
            authority="module_import_graph",
            member_id=public.identifier,
        )
        for value in public.direct_internal_imports
    )
    yield from (
        AggregateInput(
            kind="declaration_stem",
            version=DECLARATION_STEM_VERSION,
            value=stem,
            authority="lexical_text",
            member_id=public.identifier,
            anchor=candidate_source_anchor(public, declaration),
        )
        for stem, declaration in member.declaration_anchors
    )
    yield from (
        AggregateInput(
            kind="command_skeleton",
            version=COMMAND_SKELETON_VERSION,
            value=value,
            authority="lexical_text",
            member_id=public.identifier,
        )
        for value in public.command_skeletons
    )
    if public.content_sha256 is not None:
        yield AggregateInput(
            kind="exact_source_hash",
            version=CONTENT_HASH_VERSION,
            value=public.content_sha256,
            authority="source_index_content_hash",
            member_id=public.identifier,
        )
    yield from (
        AggregateInput(
            kind="normalized_declaration_block_hash",
            version=version,
            value=value,
            authority="lexical_declaration_block_hash",
            member_id=public.identifier,
        )
        for version, value in member.block_hash_versions
    )


def stable_id(prefix: str, payload: Mapping[str, object]) -> str:
    """Return a stable identifier derived from a canonical JSON payload."""

    return f"{prefix}.{stable_digest(payload).removeprefix('sha256:')[:24]}"


def stable_digest(payload: Mapping[str, object]) -> str:
    """Return the canonical SHA-256 digest for one mapping."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def member_sort_key(
    row: PreparedMember,
) -> tuple[int, str, str]:
    """Sort numbered members by numeric suffix and canonical identity."""

    return (
        known_suffix(row.public),
        row.public.identifier,
        row.public.path,
    )


def known_suffix(member: CandidateMember) -> int:
    """Return the validated numeric suffix of a partition member."""

    if member.suffix_value is None:
        raise AssertionError("numbered partition contains no suffix")
    return member.suffix_value


def anchor_sort_key(
    anchor: CandidateSourceAnchor,
) -> tuple[str, int, int, str]:
    """Sort lexical anchors by source location and declaration name."""

    return (
        anchor.module,
        anchor.line,
        anchor.column,
        anchor.declaration_name,
    )


def candidate_source_anchor(
    member: CandidateMember,
    declaration: LeanTextDeclaration,
) -> CandidateSourceAnchor:
    """Materialize one source anchor only for a retained aggregate feature."""

    candidate_name = getattr(declaration, "candidate_name", None)
    raw_identifier = getattr(declaration, "identifier", None)
    return CandidateSourceAnchor(
        module=member.identifier,
        path=member.path,
        declaration_name=declaration.name,
        declaration_kind=declaration.kind,
        line=declaration.line,
        column=declaration.column,
        candidate_name=(
            candidate_name
            if isinstance(candidate_name, str) and candidate_name
            else None
        ),
        declaration_id=(
            raw_identifier
            if isinstance(raw_identifier, str) and raw_identifier
            else None
        ),
    )


def _prepare_member(
    evidence: CandidateModuleEvidence,
    internal_modules: frozenset[str],
) -> PreparedMember:
    module = evidence.module
    numbered = _numbered_path(module.path)
    declaration_anchors, block_hash_versions = _declaration_features(module)
    member = _candidate_member(
        evidence,
        numbered,
        internal_modules,
        declaration_anchors,
        block_hash_versions,
    )
    return PreparedMember(
        public=member,
        declaration_anchors=declaration_anchors,
        block_hash_versions=block_hash_versions,
    )


def _declaration_features(
    module: LeanModule,
) -> tuple[
    tuple[tuple[str, LeanTextDeclaration], ...],
    tuple[tuple[str, str], ...],
]:
    declaration_rows = tuple(
        _declaration_feature(declaration)
        for declaration in module.declaration_evidence
    )
    anchors = tuple(row for row in declaration_rows if row is not None)
    blocks = tuple(
        block
        for declaration in module.declaration_evidence
        for block in [_declaration_block_hash(declaration)]
        if block is not None
    )
    return anchors, tuple(sorted(set(blocks)))


def _candidate_member(
    evidence: CandidateModuleEvidence,
    numbered: NumberedPath | None,
    internal_modules: frozenset[str],
    declaration_anchors: tuple[
        tuple[str, LeanTextDeclaration],
        ...,
    ],
    block_hash_versions: tuple[tuple[str, str], ...],
) -> CandidateMember:
    module = evidence.module
    return CandidateMember(
        identifier=module.name,
        path=module.path,
        population=evidence.population,
        parent=numbered.parent if numbered is not None else None,
        basename_prefix=numbered.prefix if numbered is not None else None,
        suffix_value=numbered.suffix_value if numbered is not None else None,
        suffix_spelling=(
            numbered.suffix_spelling if numbered is not None else None
        ),
        direct_internal_imports=tuple(
            sorted(set(module.imports) & internal_modules)
        ),
        declaration_stems=tuple(
            sorted({stem for stem, _ in declaration_anchors})
        ),
        command_skeletons=evidence.command_skeletons,
        content_sha256=evidence.content_sha256,
        normalized_block_hashes=tuple(
            sorted({value for _, value in block_hash_versions})
        ),
        structural_complete=evidence.structural_complete,
        imports_complete=evidence.imports_complete,
        lexical_complete=evidence.lexical_complete,
    )


def _declaration_feature(
    declaration: LeanTextDeclaration,
) -> tuple[str, LeanTextDeclaration] | None:
    candidate_name = getattr(declaration, "candidate_name", None)
    source_name = (
        candidate_name
        if isinstance(candidate_name, str) and candidate_name
        else declaration.name
    )
    stem = declaration_stem_v1(source_name)
    if stem is None:
        return None
    return stem, declaration


def _declaration_block_hash(
    declaration: LeanTextDeclaration,
) -> tuple[str, str] | None:
    raw_hash = getattr(declaration, "normalized_block_hash", None)
    if not isinstance(raw_hash, str) or not raw_hash:
        raw_hash = getattr(
            declaration,
            "normalized_block_sha256",
            None,
        )
    if not isinstance(raw_hash, str) or not raw_hash:
        return None
    raw_version = getattr(
        declaration,
        "block_normalization_version",
        None,
    )
    version = (
        raw_version
        if isinstance(raw_version, str) and raw_version
        else DECLARATION_BLOCK_HASH_VERSION
    )
    return version, raw_hash


def _numbered_path(path: str) -> NumberedPath | None:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or pure.suffix != ".lean"
    ):
        return None
    match = NUMBERED_BASENAME_RE.fullmatch(pure.stem)
    if match is None:
        return None
    parent = "" if str(pure.parent) == "." else str(pure.parent)
    spelling = match.group("suffix")
    return NumberedPath(
        parent=parent,
        prefix=match.group("prefix"),
        suffix_value=int(spelling, 10),
        suffix_spelling=spelling,
    )


def _population_for(
    name: str,
    populations: Mapping[str, str] | None,
) -> str:
    return populations.get(name, "unclassified") if populations else "unclassified"


def _optional_value(
    name: str,
    values: Mapping[str, str] | None,
) -> str | None:
    return values.get(name) if values is not None else None


def _command_skeletons_for(
    name: str,
    values: Mapping[str, Sequence[str]] | None,
) -> tuple[str, ...]:
    return tuple(values.get(name, ())) if values is not None else ()


def _normalized_internal_module_names(
    module_names: Collection[str],
) -> tuple[str, ...]:
    if isinstance(module_names, (str, bytes)):
        raise TypeError("internal module universe must be a collection")
    normalized: set[str] = set()
    for name in module_names:
        if not isinstance(name, str) or not name or name.strip() != name:
            raise ValueError(
                "internal module universe contains an invalid module identity"
            )
        normalized.add(name)
    return tuple(sorted(normalized))


def _validate_module_mapping(
    modules: Mapping[str, LeanModule],
) -> None:
    if any(name != module.name for name, module in modules.items()):
        raise ValueError("module mapping keys must match LeanModule names")
    paths = [module.path for module in modules.values()]
    if len(paths) != len(set(paths)):
        raise ValueError("candidate analysis requires unique module paths")


def _validate_optional_keys(
    values: Mapping[str, object] | None,
    module_names: frozenset[str],
    label: str,
) -> None:
    if values is None:
        return
    unknown = sorted(set(values) - module_names)
    if unknown:
        raise ValueError(
            f"{label} mapping names unknown modules: {unknown}"
        )


def _validated_module_names(
    values: Collection[str],
    module_names: frozenset[str],
    label: str,
) -> frozenset[str]:
    normalized = frozenset(values)
    unknown = sorted(normalized - module_names)
    if unknown:
        raise ValueError(
            f"{label} names unknown modules: {unknown}"
        )
    return normalized


__all__ = [
    "CONTENT_HASH_VERSION",
    "INTERNAL_IMPORT_VERSION",
    "AggregateInput",
    "PreparedMember",
    "anchor_sort_key",
    "candidate_module_evidence",
    "declaration_stem_v1",
    "internal_module_universe",
    "internal_module_universe_fingerprint",
    "known_suffix",
    "member_feature_inputs",
    "partition_members",
    "prepare_members",
    "stable_id",
    "validate_evidence_population",
]
