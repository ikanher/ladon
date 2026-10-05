"""Qualification requires observed namespace and probe results, not a label."""
from __future__ import annotations

import copy
import errno
import json
import os
import shutil
import subprocess
import sys

import pytest

from ladon.acceptance_network import observe_network_isolation, validate_network_isolation

HOST = 'net:[12345]'
OBSERVED = {'namespace': 'net:[23456]', 'interfaces': ['lo'], 'status': 'passed',
            'scope': 'network-only', 'connectErrors': {'ipv4': errno.ENETUNREACH,
                                                     'ipv6': errno.ENETUNREACH}}


@pytest.mark.parametrize(('key', 'bad'), [
    ('namespace', HOST), ('namespace', 'unknown'), ('interfaces', ['lo', 'eth0']),
    ('status', 'not-run'), ('scope', 'filesystem-isolation'),
    ('connectErrors', {}), ('connectErrors', {'ipv4': 0, 'ipv6': errno.ENETUNREACH}),
])
def test_metadata_cannot_replace_unreachable_network_observations(key, bad):
    record = copy.deepcopy(OBSERVED)
    record[key] = bad
    with pytest.raises(ValueError, match='network'):
        validate_network_isolation(record, HOST)


def test_host_namespace_is_rejected_before_socket_probes(monkeypatch):
    namespace = os.readlink('/proc/self/ns/net')
    def forbidden(*args):
        raise AssertionError('host network must not be probed')
    monkeypatch.setattr('socket.socket', forbidden)
    with pytest.raises(ValueError, match='distinct'):
        observe_network_isolation(namespace)


@pytest.mark.skipif(shutil.which('bwrap') is None, reason='network qualification requires bwrap')
def test_real_loopback_only_namespace_has_unreachable_network():
    parent_namespace = os.environ.get('LADON_ACCEPTANCE_HOST_NETWORK_NAMESPACE')
    if parent_namespace:
        # The outer installed harness already entered the namespace. Nested
        # namespace creation is unavailable after bwrap drops its privileges.
        validate_network_isolation(observe_network_isolation(parent_namespace), parent_namespace)
        return
    namespace = os.readlink('/proc/self/ns/net')
    code = ('import json; from ladon.acceptance_network import observe_network_isolation; '
            'print(json.dumps(observe_network_isolation(' + repr(namespace) + ')))')
    argv = ['bwrap', '--unshare-net', '--bind', '/', '/', '--proc', '/proc', '--dev', '/dev',
            sys.executable, '-I', '-c', code]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 0, result.stderr
    validate_network_isolation(json.loads(result.stdout), namespace)
