"""Native plans for local source-bound implication and counterexample probes."""
from ._proof_contract_probe_pair import derive_probe_result, probe_context, probe_side
from .proof_contract_rules import PROFILE_DIGEST
from .proofir_v3 import make_envelope, validate_envelope_batch


def application_probe_artifact(context, left, right, template, *, analysis_id):
    """Generate open goals; this artifact conveys no checked support."""
    from ._proof_contract_probe_templates import validate_template

    probe_context(context)
    probe_side(left)
    probe_side(right)
    validate_template(template)
    artifacts = context['artifacts']
    validate_envelope_batch(artifacts)
    result = derive_probe_result(artifacts, left, right, template)
    index = {a['artifactId']: a for a in artifacts}
    payload = {'analysisId': analysis_id, 'profileDigest': PROFILE_DIGEST, 'stage': 'probes',
        'contractRefs': [left['contractRef'], right['contractRef']],
        'correspondenceRefs': [left['correspondenceRef'], right['correspondenceRef']],
        'template': template, 'result': result, 'checkRunRefs': [], 'residuals': result['residuals']}
    artifact = make_envelope(artifact_kind='proofir.contract-analysis',
        producer={'name': 'ladon-application-probes', 'version': '1'},
        environment_ref=index[left['contractRef']['artifactRef']]['environmentRef'],
        subject_refs=[{'kind': 'contract-analysis', 'localId': analysis_id}],
        coverage={'status': 'complete', 'observed': 1}, payload=payload,
        limitations=[{'id': 'source-contract-binding-unchecked',
            'message': 'Source attribution does not establish faithful interpretation.'},
            {'id': 'planned-probes-only', 'message': 'Open goals confer no checked authority.'}]).to_dict()
    validate_envelope_batch([*artifacts, artifact])
    return artifact
