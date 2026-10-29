"""A v2 connection cannot shed or substitute its independent commitment."""

import copy

import pytest
from test_real_prose_connection_history import qualified as _qualified
from test_real_prose_connection_history import rehash

from ladon.real_prose_connection import inspect_real_prose_connection

qualified = _qualified


@pytest.mark.parametrize('path,bad', [
    (['certificate','schema'],'unknown'),
    (['certificate','expectedStructural'],'True'),
    (['certificate','actualStructural'],'True'),
    (['certificate','ownerRequest'],'{}'),
    (['certificate','requestedTerm'],'by trivial'),
    (['certificate','kernelCheck'],'asynchronous'),
    (['certificate','axioms'],['sorryAx']),
    (['helperDigest'],'invalid'),
    (['sourceDigest'],'sha256:'+'0'*64),
    (['processReceipt','returncode'],1),
    (['processReceipt','command'],['lean','different-helper']),
])
def test_commitment_substitutions_reject(qualified,path,bad):
    snapshot,*_ = qualified
    assert snapshot['schema'] == 'ladon-real-prose-connection-v2'
    value = copy.deepcopy(snapshot)
    row = value['check']['result']['goal']['commitment']
    for field in path[:-1]:
        row = row[field]
    row[path[-1]] = bad
    with pytest.raises((ValueError,TypeError,KeyError)):
        inspect_real_prose_connection(rehash(value))


def test_v2_requires_commitment(qualified):
    snapshot,*_ = qualified
    value = copy.deepcopy(snapshot)
    del value['check']['result']['goal']['commitment']
    with pytest.raises(ValueError):
        inspect_real_prose_connection(rehash(value))


def test_v2_records_commitment_without_fresh_inspection_authority(qualified):
    snapshot,*_ = qualified
    report = inspect_real_prose_connection(snapshot)
    assert report['targetOwnerBinding'] == 'recorded-independent-commitment'
    assert report['authority'] == 'none'
    assert report['freshCheck'] is False
