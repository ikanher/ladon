"""Count real bounded calls, including setup, without promoting timing to authority."""
import sys

from ladon.process_supervisor import run_bounded_target_process


def test_all_supervised_calls_count_inside_exclusive_request_stages(tmp_path):
    from ladon.correspondence_execution_accounting import execution_accounting, stage
    with execution_accounting() as accounting:
        with stage('setup'):
            first = run_bounded_target_process([sys.executable, '-c', 'print("setup")'],
                cwd=tmp_path, timeout_seconds=5, max_output_bytes=4096)
        with stage('typing'):
            second = run_bounded_target_process([sys.executable, '-c', 'print("typing")'],
                cwd=tmp_path, timeout_seconds=5, max_output_bytes=4096)
    result = accounting.result()
    assert first.succeeded and second.succeeded
    assert result['processCount'] == 2
    assert [p['stage'] for p in result['processes']] == ['setup', 'typing']
    assert result['observedOutputBytes'] == len((first.stdout + second.stdout).encode())
    assert result['stages']['setup']['processCount'] == 1
    assert result['stages']['typing']['processCount'] == 1
    assert result['memoryMeasurementScope'] == 'supervised process groups; max observed RSS, not cumulative RSS'
    assert result['wallSeconds'] >= sum(p['elapsedSeconds'] for p in result['processes'])


def test_accounting_does_not_survive_request_boundary(tmp_path):
    from ladon.correspondence_execution_accounting import execution_accounting
    with execution_accounting() as first:
        run_bounded_target_process([sys.executable, '-c', 'pass'], cwd=tmp_path,
                                  timeout_seconds=5, max_output_bytes=4096)
    with execution_accounting() as second:
        pass
    assert first.result()['processCount'] == 1
    assert second.result()['processCount'] == 0
