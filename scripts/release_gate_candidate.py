"""Explicit candidate selection and outside-checkout materialization."""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from release_gate_types import GateError, MaterializedCandidate

REQUIRED_INPUT_PATHS = (
    ".github",
    ".gitignore",
    "README.md",
    "build-constraints.txt",
    "docs",
    "openspec",
    "pyproject.toml",
    "scripts",
    "src",
    "tests",
    "uv.lock",
)
REQUIRED_CANDIDATE_ENTRIES = (
    "README.md",
    "build-constraints.txt",
    "pyproject.toml",
    "scripts",
    "src",
    "tests",
    "uv.lock",
)
COPY_IGNORED_NAMES = frozenset(
    {
        ".codex",
        ".git",
        ".idea",
        ".lake",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        ".vscode",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "temp",
        "wheels",
    }
)


def git_output(repo_root: Path, arguments: Sequence[str]) -> bytes:
    """Return stdout from one repository-local Git command."""

    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise GateError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def tracked_paths(repo_root: Path) -> tuple[str, ...]:
    """Return every index-tracked path, including staged additions."""

    raw = git_output(repo_root, ["ls-files", "-z"])
    return tuple(value.decode() for value in raw.split(b"\0") if value)


def untracked_required_paths(repo_root: Path) -> tuple[str, ...]:
    """Return untracked, nonignored files under maintained input roots."""

    raw = git_output(
        repo_root,
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            *REQUIRED_INPUT_PATHS,
        ],
    )
    return tuple(value.decode() for value in raw.split(b"\0") if value)


def require_tracked_inputs(repo_root: Path) -> None:
    """Reject a worktree whose maintained behavior depends on untracked files."""

    untracked = untracked_required_paths(repo_root)
    if untracked:
        rendered = "\n".join(f"  - {path}" for path in untracked)
        raise GateError(f"untracked required candidate inputs:\n{rendered}")


def copy_tracked_worktree(repo_root: Path, destination: Path) -> None:
    """Copy current contents for every index-tracked worktree path."""

    require_tracked_inputs(repo_root)
    for relative in tracked_paths(repo_root):
        copy_tracked_path(repo_root, destination, relative)


def copy_tracked_path(repo_root: Path, destination: Path, relative: str) -> None:
    """Copy one tracked path while preserving a tracked symlink."""

    source = repo_root / relative
    target = destination / relative
    if not source.exists() and not source.is_symlink():
        raise GateError(f"tracked path is absent from worktree: {relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
    else:
        shutil.copy2(source, target)


def copy_ignore(_directory: str, names: list[str]) -> set[str]:
    """Return local-only directory entries to omit from a directory candidate."""

    ignored = {
        name
        for name in names
        if name in COPY_IGNORED_NAMES or name.endswith(".egg-info")
    }
    ignored.update(name for name in names if name.endswith((".pyc", ".pyo")))
    return ignored


def copy_directory_candidate(source: Path, destination: Path) -> None:
    """Copy a materialized directory while omitting local generated state."""

    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=copy_ignore,
        symlinks=True,
    )


def candidate_directory(candidate: str, repo_root: Path) -> Path | None:
    """Resolve a candidate argument to an existing directory when applicable."""

    raw = Path(candidate).expanduser()
    resolved = raw if raw.is_absolute() else repo_root / raw
    return resolved.resolve() if resolved.is_dir() else None


def collection_comparison_root(
    candidate: str,
    repo_root: Path,
    candidate_kind: str,
) -> Path | None:
    """Return the selected source to compare with its materialized collection."""

    if candidate_kind == "worktree":
        return repo_root.resolve()
    if candidate_kind == "directory":
        directory = candidate_directory(candidate, repo_root)
        if directory is None:
            raise GateError(f"directory candidate is unavailable: {candidate}")
        return directory
    if candidate_kind == "treeish":
        return None
    raise GateError(f"unknown materialized candidate kind: {candidate_kind}")


def repository_is_dirty(repo_root: Path) -> bool:
    """Return whether tracked worktree or index content differs from HEAD."""

    status = git_output(
        repo_root,
        ["status", "--porcelain=v1", "--untracked-files=no"],
    )
    return bool(status.strip())


def reject_stale_head(candidate: str, repo_root: Path) -> None:
    """Reject selecting the current committed tree from a dirty checkout."""

    candidate_oid = git_output(
        repo_root,
        ["rev-parse", "--verify", f"{candidate}^{{tree}}"],
    )
    head_oid = git_output(repo_root, ["rev-parse", "--verify", "HEAD^{tree}"])
    if candidate_oid == head_oid and repository_is_dirty(repo_root):
        raise GateError(
            f"candidate {candidate!r} resolves to stale HEAD while tracked files are dirty; "
            "use --candidate worktree or a different explicit treeish"
        )


def archive_treeish(candidate: str, repo_root: Path, destination: Path) -> None:
    """Materialize an explicit Git treeish without using the live checkout."""

    reject_stale_head(candidate, repo_root)
    archive = destination.parent / "candidate.tar"
    result = subprocess.run(
        ["git", "archive", "--format=tar", f"--output={archive}", candidate],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise GateError(f"cannot materialize candidate {candidate!r}: {detail}")
    extract_trusted_git_archive(archive, destination)


def extract_trusted_git_archive(archive: Path, destination: Path) -> None:
    """Extract a Git-created archive after rejecting unsafe member paths."""

    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            require_safe_member(member)
        bundle.extractall(destination)


def require_safe_member(member: tarfile.TarInfo) -> None:
    """Reject archive traversal and links before extraction."""

    member_path = Path(member.name)
    if member_path.is_absolute() or ".." in member_path.parts:
        raise GateError(f"unsafe candidate archive member: {member.name}")
    if member.issym() or member.islnk():
        raise GateError(f"candidate archive links are unsupported: {member.name}")


@contextmanager
def materialize_candidate(
    candidate: str,
    repo_root: Path,
) -> Iterator[MaterializedCandidate]:
    """Yield one explicit candidate in a fresh outside-checkout directory."""

    source_root = repo_root.resolve()
    with tempfile.TemporaryDirectory(prefix="ladon-candidate-") as temporary:
        root = Path(temporary) / "source"
        kind = populate_candidate(candidate, source_root, root)
        require_candidate_shape(root)
        yield MaterializedCandidate(root=root, kind=kind)


def populate_candidate(candidate: str, repo_root: Path, destination: Path) -> str:
    """Populate one candidate and return its selection kind."""

    directory = candidate_directory(candidate, repo_root)
    if candidate == "worktree":
        destination.mkdir()
        copy_tracked_worktree(repo_root, destination)
        return "worktree"
    if directory is not None:
        copy_directory_candidate(directory, destination)
        return "directory"
    archive_treeish(candidate, repo_root, destination)
    return "treeish"


def require_candidate_shape(candidate_root: Path) -> None:
    """Require the minimum bootstrap/build/test surface in a candidate."""

    missing = [
        relative
        for relative in REQUIRED_CANDIDATE_ENTRIES
        if not (candidate_root / relative).exists()
    ]
    if missing:
        raise GateError(f"candidate is missing required inputs: {', '.join(missing)}")
