"""Request-owned source compilation; never a reusable proof certificate."""

from __future__ import annotations

import hashlib
import re
import secrets
import stat
from contextlib import contextmanager
from pathlib import Path

from ladon._source_goal_helpers import helper_source
from ladon.correspondence_execution_accounting import stage
from ladon.lean_toolchain import verify_toolchain_identities
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_inventory import _compiled_roots, _resolve_one_compiled_module
from ladon.source_association_io import (
    MAX_AUXILIARY_OBSERVED_BYTES,
    _uncached_file_identity,
)

RESET = (
    '\nrun_cmd Lean.Elab.Command.modifyScope '
    '(fun scope => { header := scope.header, opts := '
    'Lean.internal.cmdlineSnapshots.set (Lean.Elab.async.set {} false) true })\n'
    'set_option autoImplicit false\n'
)


def helper_material_paths():
    directory = Path(__file__).parent / 'lean'
    return [directory / 'ladon_typed_subject_helper.lean', directory / 'ladon_expr_graph.lean']


def typed_helper():
    return helper_source(helper_material_paths()[0])


def source_prelude(source, helper=None):
    return b'import Lean\n' + source + RESET.encode() + (typed_helper() if helper is None else helper)


def _fingerprint(path):
    if not path.exists():
        if path.is_symlink():
            raise ValueError('stale prepared context symlink')
        return None
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('stale prepared context nonregular artifact')
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _identity(path):
    before = _fingerprint(path)
    digest = _uncached_file_identity(path) if before is not None else None
    if _fingerprint(path) != before:
        raise ValueError('stale prepared context during snapshot')
    return before, digest


def _artifact_paths(olean):
    return [olean, Path(str(olean)+'.private'), Path(str(olean)+'.server'),
            olean.with_suffix('.ir'), olean.with_suffix('.ir.sig')]


def _original_import_files(fresh, toolchain):
    files = {}
    for row in fresh['compiledInventory']['modules']:
        if row['module'] != fresh['selection']['module']:
            files[_resolve_one_compiled_module(row['module'], _compiled_roots(toolchain))] = row['digest']
    return files


def _imports(fresh, toolchain):
    files = _original_import_files(fresh, toolchain)
    paths = [item for path in files for item in _artifact_paths(path)]
    directories = {p.parent: PreparedSourceContext.directory_fingerprint(p.parent) for p in paths}
    identities = {path: _identity(path) for path in paths}
    _validate_import_snapshots(files, identities, directories)
    return identities, directories


def _validate_import_snapshots(files, identities, directories):
    for path, expected in files.items():
        if identities[path][1][0] != expected:
            raise ValueError('stale original compiled import during source preparation')
    if sum(i[1][1] for i in identities.values() if i[1]) > MAX_AUXILIARY_OBSERVED_BYTES:
        raise ValueError('source preparation import snapshot exceeds byte bound')
    for path, expected in directories.items():
        if PreparedSourceContext.directory_fingerprint(path) != expected:
            raise ValueError('stale compiled import directory during snapshot')


def _snapshot_typed_helper():
    materials = {p: _identity(p) for p in helper_material_paths()}
    helper = typed_helper()
    if any(_identity(p) != expected for p, expected in materials.items()):
        raise ValueError('stale helper changed during preparation snapshot')
    return materials, helper


class SourcePreparationFailure(ValueError):
    def __init__(self, process):
        if process.memory_limited:
            message = memory_limit_message(
                DEFAULT_MAX_RSS_BYTES,
                process.peak_rss_bytes,
                supports_override=False,
            )
        else:
            message = 'request source preparation failed; no correspondence obligation was attempted'
        super().__init__(message)
        self.process = process
        self.plan_id = None
        self.unattempted = []


class PreparedSourceContext:
    """Only this request owns the freshly compiled ordinary import."""

    def __init__(self, root, fresh, source, toolchain, compiled_root):
        self.root, self.toolchain = root, toolchain
        self.original_path = root / fresh['selection']['sourceFile']
        if hashlib.sha256(source).hexdigest() != fresh['source']['sha256']:
            raise ValueError('stale original source before preparation')
        self.source_digest = fresh['source']['sha256']
        self.original = _identity(self.original_path)
        if self.original[1][0] != 'sha256:' + fresh['source']['sha256']:
            raise ValueError('stale original source snapshot')
        self.helper_materials, self.helper = _snapshot_typed_helper()
        self.namespace = 'LadonPrepared' + secrets.token_hex(16)
        self.module = self.namespace + '.Context'
        self.directory = compiled_root / self.namespace
        self.compiled_root = compiled_root
        self.source_path = self.directory / 'Context.lean'
        self.olean = self.directory / 'Context.olean'
        self.outputs = [self.source_path, *_artifact_paths(self.olean)]
        if any(path.exists() or path.is_symlink() for path in self.outputs):
            raise ValueError('prepared context output collision')
        if any((r / self.namespace).exists() for r in _compiled_roots(toolchain)):
            raise ValueError('prepared module resolution collision')
        self.owned = {}
        self.closed = False
        self.stale = False
        self.cached_import_reads = 0
        self.directory.mkdir()
        try:
            self.imports, self.import_directories = _imports(fresh, toolchain)
        except BaseException:
            self.directory.rmdir()
            raise

    @property
    def import_prefix(self):
        self.verify()
        return f'import {self.module}\n'.encode()

    def compile(self, source):
        if hashlib.sha256(source).hexdigest() != self.source_digest:
            raise ValueError('prepared context compilation source identity mismatch')
        with self.source_path.open('xb') as output:
            self.owned[self.source_path] = _identity(self.source_path)
            try:
                output.write(source_prelude(source, self.helper))
            finally:
                output.flush()
                self.owned[self.source_path] = _identity(self.source_path)
        execution = prepare_direct_lean_execution(self.root, None, self.toolchain,
                                                  require_compiled_module=False)
        result = self._compile_process(execution)
        if not result.succeeded:
            raise SourcePreparationFailure(result)
        resolved = _resolve_one_compiled_module(self.module, _compiled_roots(self.toolchain))
        if resolved != self.olean:
            raise ValueError('prepared context compiled resolution changed')
        self.process_receipt = result
        self.verify()

    def _compile_process(self, execution):
        try:
            return run_bounded_target_process(
            [*execution.command, '-R', str(self.compiled_root), '-o', str(self.olean),
             str(self.source_path)], cwd=self.root, env=execution.environment,
            timeout_seconds=60, max_output_bytes=8*1024**2, max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
        finally:
            # Preserve incremental ownership even if a later output is malformed.
            for path in self.outputs:
                self.owned[path] = _identity(path)

    def verify_inputs(self, root, source, toolchain):
        if (root != self.root or toolchain != self.toolchain
                or hashlib.sha256(source).hexdigest() != self.source_digest):
            raise ValueError('stale prepared context source or toolchain identity mismatch')
        self.verify()

    @staticmethod
    def directory_fingerprint(path):
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or path.resolve(strict=True) != path:
            raise ValueError('stale prepared import directory resolution changed')
        return (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns)

    def verify_cached_import(self, path):
        if self.stale:
            raise ValueError('stale prepared import cache remains tainted')
        expected = self.imports[path]
        try:
            if (path.resolve(strict=True) != path or _fingerprint(path) != expected[0]
                    or self.directory_fingerprint(path.parent) != self.import_directories[path.parent]):
                raise ValueError('stale prepared compiled import changed during request')
        except (OSError, ValueError):
            self.stale = True
            raise
        self.cached_import_reads += 1
        return expected[1]

    def verify(self, *, full=False):
        if self.stale:
            raise ValueError('stale prepared context remains tainted after mutation')
        try:
            self._verify(full=full)
        except (OSError, ValueError):
            self.stale = True
            raise

    def _verify(self, *, full=False):
        if self.closed:
            raise ValueError('stale prepared context after request cleanup')
        verify_toolchain_identities(self.toolchain)
        if typed_helper() != self.helper or _fingerprint(self.original_path) != self.original[0]:
            raise ValueError('stale source or typed helper changed during preparation')
        self._verify_materials(full=full)
        for path, expected in {**self.imports, **self.owned}.items():
            if _fingerprint(path) != expected[0] or (full and _identity(path) != expected):
                raise ValueError('stale prepared context import or artifact changed')

    def _verify_materials(self, *, full):
        for path, expected in self.helper_materials.items():
            if _fingerprint(path) != expected[0] or (full and _identity(path) != expected):
                raise ValueError('stale typed helper material changed during preparation')
        for directory, expected in self.import_directories.items():
            if self.directory_fingerprint(directory) != expected:
                raise ValueError('stale prepared import sidecar directory changed')

    def cleanup(self):
        residue = []
        for path, expected in self.owned.items():
            if _identity(path) != expected:
                residue.append(str(path))
            elif expected[0] is not None:
                path.unlink()
        self.closed = True
        if getattr(self, 'directory', None) is not None:
            try:
                self.directory.rmdir()
            except OSError:
                residue.append(str(self.directory))
        if residue:
            raise ValueError('stale prepared context cleanup residue: ' + ', '.join(residue))


@contextmanager
def prepare_source_context(root, fresh, source, toolchain):
    """Fail closed on execution/mutation; unsupported shapes use ordinary checks."""
    compiled = root / '.lake/build/lib/lean'
    if (compiled not in toolchain.library_roots or re.search(rb'\b(?:private|local)\b', source)
            or len(source_prelude(source)) > 8*1024**2):
        yield None
        return
    context = PreparedSourceContext(root, fresh, source, toolchain, compiled)
    try:
        with stage("source-preparation"):
            context.compile(source)
        yield context
        context.verify(full=True)
    finally:
        context.cleanup()
