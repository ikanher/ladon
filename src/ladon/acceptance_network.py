"""Observe and validate network-disabled qualification in a separate namespace.

The harness creates the namespace explicitly. This observer checks it before
probing reserved destinations; it supplies no filesystem or initializer
isolation and does not authenticate a recorded producer.
"""
from __future__ import annotations

import errno
import os
import re
import socket


def observe_network_isolation(host_namespace: str) -> dict:
    """Fail before socket probes unless only loopback exists in a new namespace."""
    namespace = os.readlink('/proc/self/ns/net')
    interfaces = sorted(name for _, name in socket.if_nameindex())
    _validate_namespace(host_namespace, namespace, interfaces)
    outcomes = {}
    for label, family, address in (
        ('ipv4', socket.AF_INET, '198.18.0.1'),
        ('ipv6', socket.AF_INET6, '2001:db8::1'),
    ):
        with socket.socket(family, socket.SOCK_STREAM) as connection:
            connection.settimeout(1)
            outcomes[label] = connection.connect_ex((address, 9))
    observed = {'status': 'passed', 'namespace': namespace, 'interfaces': interfaces,
                'connectErrors': outcomes, 'scope': 'network-only'}
    validate_network_isolation(observed, host_namespace)
    return observed


def validate_network_isolation(observed: dict, host_namespace: str) -> None:
    """Require namespace, interface and actual unreachable-probe observations."""
    if observed is None:
        raise ValueError('network isolation observations are missing')
    if not isinstance(observed, dict):
        raise TypeError('network isolation observations must be an object')
    _validate_namespace(host_namespace, observed.get('namespace'), observed.get('interfaces'))
    if observed.get('status') != 'passed' or observed.get('scope') != 'network-only':
        raise ValueError('network isolation observation is incomplete')
    expected = {'ipv4': errno.ENETUNREACH, 'ipv6': errno.ENETUNREACH}
    errors = observed.get('connectErrors')
    if errors != expected or any(type(value) is not int for value in errors.values()):
        raise ValueError('network probes did not establish unreachable destinations')


def _validate_namespace(host, namespace, interfaces) -> None:
    for value in (host, namespace):
        if not isinstance(value, str) or re.fullmatch(r'net:\[[0-9]+\]', value) is None:
            raise ValueError('network namespace identity is unavailable')
    if namespace == host or interfaces != ['lo']:
        raise ValueError('network qualification requires a distinct loopback-only namespace')
