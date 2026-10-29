"""V2 syntax keeps global/set scope and never treats aliases as admitted meaning."""

import importlib
from copy import deepcopy

import pytest
from support.real_bound_shape import app, const, forall_, var


def reader():
    return importlib.import_module('ladon.real_prose_shape')


def binder(name, type_, body):
    return {'forallE': {'name': name, 'type': type_, 'body': body, 'binderInfo': 'explicit'}}


def test_old_and_new_profiles_are_distinct():
    assert reader().PROFILE_ID == 'real-bound-prose-shape-v2'


def test_wrong_or_unrelated_proposition_stays_unresolved():
    result = reader().recognize_shape({'const': 'True', 'levels': []})
    assert result['candidate'] is None
    assert result['admission'] == 'unresolved'
    assert result['residuals']
