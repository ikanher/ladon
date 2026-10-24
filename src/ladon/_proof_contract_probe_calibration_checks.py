"""Fixed finite goals and immutable source binding for probe calibration."""
from __future__ import annotations

import hashlib
from importlib import resources
from pathlib import Path

from ._proof_contract_source_obligations_staging import (
    _check_stage_deadline,
    _safe_create_parent,
    _write_probe,
)
from .proof_slice import pinned_toolchain
from .source_association_io import _read_regular

MAX_BYTES = 8 * 1024**2


def separator_source():
    """Read the actual shipped, bounded Lean asset."""
    path = Path(str(resources.files('ladon').joinpath('lean', 'ladon_probe_separator.lean')))
    return _read_regular(path, MAX_BYTES)


def source_digest(source):
    return 'sha256:' + hashlib.sha256(source).hexdigest()


def prepare_calibration(owned, profile):
    root = Path(owned['repoRoot'])
    _check_stage_deadline(owned['deadlineMonotonic'])
    source = separator_source()
    if source_digest(source) != profile['sourceDigest']:
        raise ValueError('registered calibration source changed')
    environment = pinned_toolchain(root).context_identity
    relative = Path('.ladon/contract-obligations') / profile['sourceDigest'][7:] / 'calibration/Probe.lean'
    _check_stage_deadline(owned['deadlineMonotonic'])
    _safe_create_parent(root, (root / relative).parent)
    _write_probe(root / relative, source)
    adapter = {'repoRoot': str(root), 'sourcePath': relative.as_posix(),
               'sourceDigest': profile['sourceDigest']}
    verify_calibration(owned, adapter, environment)
    return adapter, environment


def verify_calibration(owned, adapter, environment):
    """Recheck the installed asset, staged bytes and installed toolchain identity."""
    root = Path(owned['repoRoot'])
    _check_stage_deadline(owned['deadlineMonotonic'])
    target = root / adapter['sourcePath']
    _safe_create_parent(root, target.parent)
    if target.is_symlink() or source_digest(_read_regular(target, MAX_BYTES)) != adapter['sourceDigest']:
        raise ValueError('staged calibration source changed')
    if source_digest(separator_source()) != adapter['sourceDigest']:
        raise ValueError('shipped calibration source changed')
    if pinned_toolchain(root).context_identity != environment:
        raise ValueError('calibration execution environment changed')
    _check_stage_deadline(owned['deadlineMonotonic'])


def calibration_goals(application):
    """Closed propositions: generic separator, actual counterexample, application."""
    family = '([0, 1, 2, 3, 4] : List (Fin 5))'
    small = '([0, 1, 2, 3] : List (Fin 5))'
    zero = '(fun (_ : Fin 5) => false)'
    last = '(fun (i : Fin 5) => if i.val = 4 then true else false)'
    return [
        {'id': 'separator', 'goal': f'∀ (f g : Fin 5 → Bool), (∀ i ∈ {family}, f i = g i) → f = g',
         'term': 'LadonProbeCalibration.full_separates'},
        {'id': 'incomplete-counterexample',
         'goal': f'(∀ i ∈ {small}, {zero} i = {last} i) ∧ {zero} ≠ {last}',
         'term': 'LadonProbeCalibration.incomplete_counterexample'},
        {'id': 'application', **application},
    ]
