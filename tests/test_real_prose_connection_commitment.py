"""Source extensions cannot replace the independent owner-derived target."""

import json
import time

from test_real_prose_connection_witness import witness_root as _witness_root
from test_real_prose_connection_witness import witness_source
from test_real_prose_exact_goal import project as _project
from test_real_prose_exact_goal import request

from ladon.real_prose_connection_commitment import commit_target
from ladon.real_prose_connection_context import run_lean

project = _project
witness_root = _witness_root


def check(root,workspace,text,proof):
    workspace.mkdir()
    # The standalone fixture module is renamed without changing owner ranges.
    (root/'LadonConnection.lean').write_text(text)
    value = request()
    value['module'] = 'LadonConnection'
    job = {'workspace':str(workspace),'deadlineMonotonic':time.monotonic()+60,
           'maxRssBytes':12*1024**3,'maxOutputBytes':8*1024**2}
    return commit_target(job,root,text,value,proof,run_lean)


def source(proof,*,override=False):
    text = witness_source(proof).replace('"module\\":\\"Case', '"module\\":\\"LadonConnection')
    if override:
        # Install the rule after owner declarations, preserving their exact ranges.
        pos = text.index('#ladon_connection_witness')
        text = text[:pos]+('open Lean Elab Term\n'
            'elab_rules : term | `(ladon_prose_exact_goal% $_request:str) => pure (Lean.mkConst ``True)\n')+text[pos:]
    encoded = request()
    encoded['module'] = 'LadonConnection'
    quoted = json.dumps(json.dumps(encoded,sort_keys=True,separators=(',',':')))
    return text+f'example : ladon_prose_exact_goal% {quoted} := by\n  skip\n'


def test_owner_commitment_checks_requested_proof(witness_root,tmp_path):
    proof = 'by intro original first second; exact second'
    result = check(witness_root,tmp_path/'commit',source(proof),proof)
    assert result['certificate'] is not None,result['processReceipt']['stdout']+result['processReceipt']['stderr']
    assert result['certificate']['kernelCheck'] == 'synchronous'
    assert result['certificate']['expectedStructural'] == result['certificate']['actualStructural']


def test_goal_elaborator_override_cannot_commit_true(witness_root,tmp_path):
    proof = 'by exact True.intro'
    result = check(witness_root,tmp_path/'commit',source(proof,override=True),proof)
    assert result['certificate'] is None
    assert 'differs from independently constructed' in result['processReceipt']['stdout']+result['processReceipt']['stderr']


def test_witness_does_not_authorize_a_different_requested_term(witness_root,tmp_path):
    result = check(witness_root,tmp_path/'commit',source('by intro original first second; exact second'),
                   'by exact True.intro')
    assert result['certificate'] is None


def test_placeholder_proof_cannot_gain_commitment(witness_root,tmp_path):
    proof = 'by sorry'
    result = check(witness_root,tmp_path/'commit',source(proof),proof)
    assert result['certificate'] is None
    assert 'unsupported axioms' in result['processReceipt']['stdout']+result['processReceipt']['stderr']
