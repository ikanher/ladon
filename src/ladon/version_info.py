"""Read-only installed-package and local-source identity reporting."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from urllib.parse import unquote, urlparse


def version_payload() -> dict[str, object]:
    """Return machine-readable package bytes and optional source revision identity."""

    distribution = _distribution()
    package = _package_identity(distribution)
    source = _source_identity(distribution)
    return {
        "schema": "ladon-version-result-v1",
        "status": "available",
        "package": package,
        "source": source,
        "runtime": {"pythonExecutable": sys.executable},
        "nonclaims": [
            "A local source revision is installation provenance, not proof that installed bytes equal the current checkout."
        ],
    }


def _distribution() -> metadata.Distribution | None:
    try:
        return metadata.distribution("ladon")
    except metadata.PackageNotFoundError:
        return None


def _package_identity(distribution: metadata.Distribution | None) -> dict[str, object]:
    if distribution is None:
        return {
            "name": "ladon",
            "version": "source-tree",
            "distributionIdentity": None,
            "installedContentIdentity": None,
            "filesHashed": 0,
        }
    name = distribution.metadata.get("Name", "ladon")
    version = distribution.version
    content_identity, files_hashed = _installed_content_identity(distribution)
    identity_payload = {
        "name": name,
        "version": version,
        "installedContentIdentity": content_identity,
        "directUrl": distribution.read_text("direct_url.json"),
    }
    encoded = json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode()
    return {
        "name": name,
        "version": version,
        "distributionIdentity": "sha256:" + hashlib.sha256(encoded).hexdigest(),
        "installedContentIdentity": content_identity,
        "filesHashed": files_hashed,
    }


def _installed_content_identity(
    distribution: metadata.Distribution,
) -> tuple[str | None, int]:
    files = sorted(
        (file for file in distribution.files or () if not str(file).endswith((".pyc", ".pyo"))),
        key=str,
    )
    if not files or len(files) > 4096:
        return None, 0
    digest = hashlib.sha256()
    total = 0
    hashed = 0
    for relative in files:
        path = Path(distribution.locate_file(relative))
        if not path.is_file():
            continue
        content = path.read_bytes()
        total += len(content)
        if total > 256 * 1024 * 1024:
            return None, 0
        name = str(relative).encode()
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(hashlib.sha256(content).digest())
        hashed += 1
    return ("sha256:" + digest.hexdigest(), hashed) if hashed else (None, 0)


def _source_identity(distribution: metadata.Distribution | None) -> dict[str, object]:
    source = _direct_url_source(distribution) or _checkout_source()
    if source is None:
        return {"status": "unavailable", "path": None, "commit": None, "dirty": None}
    commit = _git_output(source, "rev-parse", "HEAD")
    dirty = _git_dirty(source) if commit is not None else None
    return {
        "status": "observed" if commit is not None else "unavailable",
        "path": str(source),
        "commit": commit,
        "dirty": dirty,
    }


def _direct_url_source(distribution: metadata.Distribution | None) -> Path | None:
    if distribution is None:
        return None
    raw = distribution.read_text("direct_url.json")
    if not raw:
        return None
    try:
        url = json.loads(raw).get("url")
    except (json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(url, str):
        return None
    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None
    path = Path(unquote(parsed.path)).resolve()
    return path if path.is_dir() else None


def _checkout_source() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / ".git").exists():
            return parent
    return None


def _git_output(root: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ("git", "-C", str(root), *arguments),
            text=True,
            capture_output=True,
            check=False,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = result.stdout.strip()
    return output if result.returncode == 0 and output else None


def _git_dirty(root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ("git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=normal"),
            text=True,
            capture_output=True,
            check=False,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return bool(result.stdout) if result.returncode == 0 else None


__all__ = ["version_payload"]
