"""Bounded application-probe response and stop reporting."""
from ._proof_contract_probe_pair import MAX_BYTES
from ._proof_contract_source_obligations_inputs import bounded_json_size


class ApplicationProbeOutputLimit(ValueError):
    """No result envelope fits: publish neither JSON nor an output file."""

    def __init__(self, diagnostic):
        self.code = diagnostic['code']
        self.memory_report_back_required = self.code == 'memory-limit'
        super().__init__('Insufficient output capacity; no result published. ' + diagnostic['message'])


def base_result():
    return {'schema': 'ladon-application-probe-v1', 'status': 'incomplete',
        'planId': None, 'goals': [], 'residuals': [], 'diagnostic': None,
        'sourceFidelity': 'attributed-unreviewed', 'checkerAuthority': 'none',
        'wholeMethodAuthority': 'none', 'mathematicalFalsity': 'not-established',
        'memoryReportBackRequired': False}


def fail(result, status, code, message):
    result.update(status=status, checkerAuthority='none',
        diagnostic={'code': code, 'message': str(message)[:1000]},
        memoryReportBackRequired=code == 'memory-limit')


def require_capacity(result, cap):
    from ._proof_contract_context_goals import ContextOutputLimit

    if bounded_json_size(result, min(cap, MAX_BYTES)) + 1 > min(cap, MAX_BYTES):
        raise ContextOutputLimit('Application probe response capacity exhausted; later work stopped.')


def bounded_result(result, cap):
    limit = min(cap, MAX_BYTES)
    if bounded_json_size(result, limit) + 1 <= limit:
        return result
    small = base_result()
    if result['memoryReportBackRequired']:
        fail(small, 'incomplete', 'memory-limit', result['diagnostic']['message'])
    else:
        fail(small, 'incomplete', 'output-limit', 'Application probe response exceeds output capacity.')
    if bounded_json_size(small, limit) + 1 > limit:
        raise ApplicationProbeOutputLimit(small['diagnostic'])
    return small
