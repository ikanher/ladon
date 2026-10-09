"""Output failures retain actual stream sizes and configured capture budgets."""
from ladon.process_supervisor import ProcessResult
from ladon.source_goal_capture import _process_failure, _receipt


def test_capture_receipt_records_stream_bytes_and_size_failure():
    process = ProcessResult(('lean',), -9, 'é' * 10, 'diagnostic', 0.1, output_limited=True)
    receipt = _receipt(process, b'input')
    receipt['maxOutputBytes'] = 16
    assert receipt['stdoutBytes'] == 20
    assert receipt['stderrBytes'] == 10
    result = _process_failure(process, 0, [receipt])
    assert result['status'] == 'output-limit'
    assert result['diagnostic']['outputSize'] == {
        'stdoutBytes': 20, 'stderrBytes': 10, 'maxOutputBytes': 16,
    }
