"""Supervisor-owned scratch leases for generated correspondence goals."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

ENV_KEYS = (
    'LADON_INTERNAL_GOAL_WORKSPACE',
    'LADON_INTERNAL_GOAL_WORKSPACE_ID',
    'LADON_INTERNAL_GOAL_WORKSPACE_PARENT_ID',
    'LADON_INTERNAL_GOAL_WORKSPACE_ROOT_PARENT_ID',
)
ENV_WORKSPACE = ENV_KEYS[0]
ENV_AUDIT_DELEGATION = 'LADON_INTERNAL_AUDIT_GOAL_DELEGATION'
GOAL_NAME = 'LadonCorrespondence.lean'
GOAL_WORKERS = {
    ('ladon.proof_contract_lift_worker', 'check-nat-rational-lift'),
    ('ladon.proof_contract_route_context_worker', 'check-route-context-goal'),
    ('ladon.proof_contract_context_worker', 'check-context-goal'),
    ('ladon.proof_contract_probe_worker', 'check-probe-goal'),
    ('ladon.proof_contract_bridge_worker', 'check-goal'),
}
_FLAGS = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0)
_FILE_FLAGS = getattr(os, 'O_NOFOLLOW', 0) | os.O_NONBLOCK
MAX_GOAL_BYTES = 8 * 1024**2

def _identity(fd):
    info = os.fstat(fd)
    return [info.st_dev, info.st_ino]

def _id_stat(info):
    return [info.st_dev, info.st_ino]

def _open_at(parent_fd, name, expected=None):
    fd = os.open(name, _FLAGS, dir_fd=parent_fd)
    if expected is not None and _identity(fd) != expected:
        os.close(fd)
        raise OSError('goal scratch directory identity changed')
    return fd

def provision(job, worker_module):
    """Create one exclusive workspace for a supported generated-goal worker."""
    if not isinstance(job, dict) or not _goal_workspace_job(job, worker_module):
        return None
    request = job.get('request')
    if not isinstance(request, dict) or not isinstance(request.get('repoRoot'), str):
        return None
    if worker_module == 'ladon.proof_contract_probe_worker' and job.get('operation') == 'check-probe-goal':
        delegated = os.environ.get(ENV_AUDIT_DELEGATION)
        if delegated is not None:
            return _borrow_workspace(delegated, request['repoRoot'], job, worker_module)
    return _create_workspace(request['repoRoot'], worker_module)

def _create_workspace(repo_root, worker_module):
    root = _selected_root(repo_root)
    root_fd = os.open(root, _FLAGS)
    ladon_fd = state_fd = workspace_fd = None
    try:
        root_id = _identity(root_fd)
        try:
            ladon_fd = _open_at(root_fd, '.ladon')
        except FileNotFoundError:
            os.mkdir('.ladon', dir_fd=root_fd)
            ladon_fd = _open_at(root_fd, '.ladon')
        try:
            state_fd = _open_at(ladon_fd, 'correspondence')
        except FileNotFoundError:
            os.mkdir('correspondence', dir_fd=ladon_fd)
            state_fd = _open_at(ladon_fd, 'correspondence')
        state_id, ladon_id = _identity(state_fd), _identity(ladon_fd)
        name = 'goal-' + secrets.token_hex(12)
        os.mkdir(name, mode=0o700, dir_fd=state_fd)
        workspace_fd = _open_at(state_fd, name)
        workspace_id = _identity(workspace_fd)
        lease = {'root': str(root), 'name': name, 'path': root / '.ladon' / 'correspondence' / name,
                 'rootId': root_id, 'ladonId': ladon_id, 'stateId': state_id,
                 'workspaceId': workspace_id, 'rootFd': root_fd, 'ladonFd': ladon_fd,
                 'stateFd': state_fd, 'workspaceFd': workspace_fd}
        if worker_module == 'ladon.proof_contract_audit_worker':
            lease['delegateModule'] = 'ladon.proof_contract_probe_worker'
            lease['delegateOperation'] = 'check-probe-goal'
        return lease
    except BaseException:
        for fd in (workspace_fd, state_fd, ladon_fd, root_fd):
            if fd is not None:
                os.close(fd)
        raise

def _goal_workspace_job(job, worker_module):
    if (worker_module, job.get('operation')) in GOAL_WORKERS:
        return True
    if worker_module != 'ladon.proof_contract_audit_worker' or job.get('operation') != 'audit-stage':
        return False
    request = job.get('request')
    return isinstance(request, dict) and request.get('operation') == 'check-probe'

def _borrow_workspace(raw, requested_root, job, worker_module):
    record = json.loads(raw)
    required = {'root', 'name', 'rootId', 'ladonId', 'stateId', 'workspaceId',
                'delegateModule', 'delegateOperation'}
    if not isinstance(record, dict) or set(record) != required:
        raise OSError('inherited goal workspace capability is malformed')
    if (record['delegateModule'] != worker_module
            or record['delegateOperation'] != job.get('operation')):
        raise OSError('inherited goal workspace capability does not authorize this worker')
    if _selected_root(record['root']) != _selected_root(requested_root):
        raise OSError('inherited goal workspace belongs to a different repository')
    lease = {**record, 'path': Path(record['root']) / '.ladon' / 'correspondence' / record['name'],
             'borrowed': True}
    lease['rootFd'], lease['ladonFd'], lease['stateFd'], lease['workspaceFd'] = _validate_chain(lease)
    return lease

def _selected_root(path):
    root = Path(path).resolve(strict=True)
    if root.parent == root:
        raise OSError('cannot quarantine goal scratch outside the filesystem root')
    return root

def environment(lease):
    """Return private worker metadata; never add it to the caller's JSON job."""
    if lease is None:
        return {}
    record = {key: lease[key] for key in (
        'root', 'name', 'rootId', 'ladonId', 'stateId', 'workspaceId')}
    for key in ('delegateModule', 'delegateOperation'):
        if key in lease:
            record[key] = lease[key]
    key = (ENV_AUDIT_DELEGATION if 'delegateModule' in lease and not lease.get('borrowed')
           else ENV_WORKSPACE)
    return {key: json.dumps(record, sort_keys=True, separators=(',', ':'))}

def _validate_chain(lease):
    root_fd = os.open(lease['root'], _FLAGS)
    ladon_fd = state_fd = workspace_fd = None
    try:
        if _identity(root_fd) != lease['rootId']:
            raise OSError('selected repository root identity changed')
        ladon_fd = _open_at(root_fd, '.ladon', lease['ladonId'])
        state_fd = _open_at(ladon_fd, 'correspondence', lease['stateId'])
        workspace_fd = _open_at(state_fd, lease['name'], lease['workspaceId'])
        return root_fd, ladon_fd, state_fd, workspace_fd
    except BaseException:
        for fd in (workspace_fd, state_fd, ladon_fd, root_fd):
            if fd is not None:
                os.close(fd)
        raise

@contextmanager
def worker_workspace(state):
    """Validate the supervisor lease, then yield (directory path, owner)."""
    raw = os.environ.pop(ENV_WORKSPACE, None)
    for key in ENV_KEYS[1:]:
        os.environ.pop(key, None)
    if raw is None:
        with tempfile.TemporaryDirectory(prefix='goal-', dir=state) as temporary:
            yield Path(temporary), None
        return
    lease = json.loads(raw)
    expected_state = Path(lease['root']) / '.ladon' / 'correspondence'
    if Path(state).resolve(strict=True) != expected_state:
        raise OSError('goal scratch lease belongs to a different repository')
    root_fd = ladon_fd = state_fd = workspace_fd = None
    try:
        root_fd, ladon_fd, state_fd, workspace_fd = _validate_chain(lease)
        path = Path(lease['root']) / '.ladon' / 'correspondence' / lease['name']
        owner = {'lease': lease, 'rootFd': root_fd, 'ladonFd': ladon_fd,
                 'stateFd': state_fd, 'workspaceFd': workspace_fd,
                 'goalIdentity': None, 'goalDigest': None}
        yield path, owner
    finally:
        if workspace_fd is not None:
            os.close(workspace_fd)
        if state_fd is not None:
            os.close(state_fd)
        if ladon_fd is not None:
            os.close(ladon_fd)
        if root_fd is not None:
            os.close(root_fd)

def write_goal(path, text, owner):
    raw = text.encode()
    if len(raw) > MAX_GOAL_BYTES:
        raise ValueError('generated module exceeds source byte bound')
    if owner is None:
        path.write_text(text)
        return
    _validate_open_owner(owner)
    if owner['goalIdentity'] is None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _FILE_FLAGS
        fd = os.open(GOAL_NAME, flags, 0o600, dir_fd=owner['workspaceFd'])
        owner['goalIdentity'] = _identity(fd)
    else:
        flags = os.O_WRONLY | _FILE_FLAGS
        fd = os.open(GOAL_NAME, flags, dir_fd=owner['workspaceFd'])
        if _identity(fd) != owner['goalIdentity']:
            os.close(fd)
            raise OSError('generated goal file identity changed')
        os.ftruncate(fd, 0)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(raw)
            stream.flush()
    finally:
        os.close(fd)
    info = os.stat(GOAL_NAME, dir_fd=owner['workspaceFd'], follow_symlinks=False)
    if _id_stat(info) != owner['goalIdentity'] or not stat.S_ISREG(info.st_mode):
        raise OSError('generated goal file identity changed after write')
    owner['goalDigest'] = hashlib.sha256(raw).hexdigest()

def _validate_open_owner(owner):
    lease = owner['lease']
    checked = _validate_chain(lease)
    for fd in checked:
        os.close(fd)
    for key, fd in (('rootId', owner['rootFd']), ('ladonId', owner['ladonFd']),
                    ('stateId', owner['stateFd']), ('workspaceId', owner['workspaceFd'])):
        if _identity(fd) != lease[key]:
            raise OSError('owned goal workspace identity changed')

def cleanup_worker_goal(owner):
    """Unlink only the regular goal inode created by this worker."""
    if owner is None or owner['goalIdentity'] is None:
        return
    if owner['goalDigest'] is None:
        raise OSError('generated goal bytes are incomplete; preserving scratch')
    _validate_open_owner(owner)
    flags = os.O_RDONLY | _FILE_FLAGS
    fd = os.open(GOAL_NAME, flags, dir_fd=owner['workspaceFd'])
    try:
        info = os.fstat(fd)
        if _id_stat(info) != owner['goalIdentity'] or not stat.S_ISREG(info.st_mode):
            raise OSError('generated goal file was replaced; preserving foreign material')
        if _bounded_digest(fd, info.st_size) != owner['goalDigest']:
            raise OSError('generated goal bytes changed; preserving observed material')
    finally:
        os.close(fd)
    os.unlink(GOAL_NAME, dir_fd=owner['workspaceFd'])

def _bounded_digest(fd, size):
    if size > MAX_GOAL_BYTES:
        raise OSError('generated goal exceeds byte bound; preserving scratch')
    digest = hashlib.sha256()
    remaining = MAX_GOAL_BYTES + 1
    while remaining:
        chunk = os.read(fd, min(remaining, 64 * 1024))
        if not chunk:
            return digest.hexdigest()
        digest.update(chunk)
        remaining -= len(chunk)
    raise OSError('generated goal grew beyond byte bound; preserving scratch')

def _has_entries(fd):
    with os.scandir(fd) as entries:
        return next(entries, None) is not None

def finish(lease):
    """Remove an empty owned lease or atomically quarantine its exact contents."""
    if lease is None:
        return None
    if lease.get('borrowed'):
        return _finish_borrowed(lease)
    checked = None
    try:
        checked = _validate_chain(lease)
        _root_fd, _ladon_fd, state_fd, workspace_fd = checked
        if _has_entries(workspace_fd):
            return _quarantine(lease, state_fd, workspace_fd)
        _check_entry_identity(state_fd, lease['name'], lease['workspaceId'])
        os.rmdir(lease['name'], dir_fd=state_fd)
        return None
    finally:
        if checked is not None:
            for fd in checked:
                os.close(fd)
        for key in ('workspaceFd', 'stateFd', 'ladonFd', 'rootFd'):
            os.close(lease[key])

def _finish_borrowed(lease):
    checked = None
    try:
        checked = _validate_chain(lease)
        if _has_entries(checked[3]):
            raise OSError('borrowed goal workspace still contains owned or partial material')
        return
    finally:
        if checked is not None:
            for fd in checked:
                os.close(fd)
        for key in ('workspaceFd', 'stateFd', 'ladonFd', 'rootFd'):
            os.close(lease[key])

def _quarantine(lease, state_fd, workspace_fd):
    root = Path(lease['root'])
    parent_fd = os.open(root.parent, _FLAGS)
    quarantine_fd = None
    qname = '.ladon-goal-quarantine-' + secrets.token_hex(12)
    try:
        if _identity(parent_fd)[0] != _identity(workspace_fd)[0]:
            raise OSError('source and quarantine directories are on different filesystems')
        os.mkdir(qname, mode=0o700, dir_fd=parent_fd)
        quarantine_fd = _open_at(parent_fd, qname)
        if _identity(workspace_fd) != lease['workspaceId']:
            raise OSError('owned goal workspace identity changed')
        if _identity(quarantine_fd)[0] != _identity(workspace_fd)[0]:
            raise OSError('quarantine directory is on a different filesystem')
        _check_entry_identity(state_fd, lease['name'], lease['workspaceId'])
        dest = lease['name']
        os.rename(lease['name'], dest, src_dir_fd=state_fd, dst_dir_fd=quarantine_fd)
        moved_fd = _open_at(quarantine_fd, dest, lease['workspaceId'])
        os.close(moved_fd)
        return str(root.parent / qname / dest)
    finally:
        if quarantine_fd is not None:
            os.close(quarantine_fd)
        os.close(parent_fd)

def _check_entry_identity(parent_fd, name, expected):
    info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if _id_stat(info) != expected or not stat.S_ISDIR(info.st_mode):
        raise OSError('owned goal workspace entry was replaced')
