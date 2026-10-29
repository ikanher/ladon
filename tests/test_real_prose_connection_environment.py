"""The commitment must use the original capture's scope and compiled imports."""

import copy
import time

import pytest
from test_real_prose_connection_commitment import source
from test_real_prose_connection_witness import witness_root as _witness_root
from test_real_prose_exact_goal import project as _project
from test_real_prose_exact_goal import request

from ladon.proof_slice import pinned_toolchain
from ladon.real_prose_connection_commitment import commit_target, validate_commitment
from ladon.real_prose_connection_context import run_lean
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal

project = _project
witness_root = _witness_root


@pytest.fixture(scope='module')
def checked_environment(witness_root,tmp_path_factory):
    proof = 'by intro original first second; exact second'
    text = source(proof)
    (witness_root/'LadonConnection.lean').write_text(text)
    workspace = tmp_path_factory.mktemp('committed-environment')
    context = pinned_toolchain(witness_root)
    captured = capture_source_goal(SourceGoalCaptureRequest(witness_root,'LadonConnection.lean',
        'LadonConnection',len(text.splitlines()),4,context),workspace_parent=workspace)
    assert captured['status'] == 'captured',captured
    owner = request()
    owner['module'] = 'LadonConnection'
    job = {'workspace':str(workspace),'deadlineMonotonic':time.monotonic()+60,
           'maxRssBytes':12*1024**3,'maxOutputBytes':8*1024**2}
    commitment = commit_target(job,witness_root,text,owner,proof,run_lean,capture=captured['capture'])
    assert commitment['certificate'] is not None,commitment['processReceipt']
    return commitment,owner,proof,text,captured['capture']


def test_actual_commitment_binds_original_capture_environment(checked_environment):
    commitment,owner,proof,text,capture = checked_environment
    validate_commitment(commitment,owner,proof,text,capture['goal']['typeStructural'],
                        environment=capture['environment'])
    assert commitment['environment'] == capture['environment']


@pytest.mark.parametrize('field', ['leanVersion','leanCommit','leanExecutablePath','namespace',
                                  'openDeclarationsStructural','optionsStructural'])
def test_different_observed_scope_rejects(checked_environment,field):
    commitment,owner,proof,text,capture = checked_environment
    altered = copy.deepcopy(commitment)
    altered['certificate']['environment'][field] += '-changed'
    with pytest.raises(ValueError,match='scope or executable'):
        validate_commitment(altered,owner,proof,text,capture['goal']['typeStructural'],
                            environment=capture['environment'])


@pytest.mark.parametrize('field', ['executionContextRef','executableDigest','compiledInventory'])
def test_substituted_recorded_environment_rejects(checked_environment,field):
    commitment,owner,proof,text,capture = checked_environment
    altered = copy.deepcopy(commitment)
    if field == 'compiledInventory':
        altered['environment'][field]['primaryDigest'] = 'sha256:'+'0'*64
    else:
        altered['environment'][field] = 'sha256:'+'0'*64
    with pytest.raises(ValueError,match='environment differs'):
        validate_commitment(altered,owner,proof,text,capture['goal']['typeStructural'],
                            environment=capture['environment'])


def test_changed_loaded_module_path_rejects(checked_environment):
    commitment,owner,proof,text,capture = checked_environment
    altered = copy.deepcopy(commitment)
    altered['certificate']['environment']['compiledModulePaths'][0]['path'] += '.different'
    with pytest.raises(ValueError,match='different compiled import'):
        validate_commitment(altered,owner,proof,text,capture['goal']['typeStructural'],
                            environment=capture['environment'])
