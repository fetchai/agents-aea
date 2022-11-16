# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Tests for config data types."""
import copy
import operator

import pytest
from hypothesis import given
from hypothesis import strategies as st

from aea.configurations.data_types import (
    Dependency,
    PackageId,
    PackageVersion,
    PublicId,
)

from tests.strategies.data_types import (
    package_id_strategy,
    public_id_strategy,
    version_info_strategy,
)


NUMERIC_TYPES = int, float, complex
SEQUENCE_TYPES = list, str, tuple
ITERATOR_TYPES = *SEQUENCE_TYPES, list, zip, map
NAME_SPACE = [PublicId, PackageId, Dependency]
COMPARISON_OPERATORS = [
    operator.lt,
    operator.le,
    operator.eq,
    operator.ne,
    operator.ge,
    operator.gt,
]


def all_comparisons_operations_equal(pair_a, pair_b) -> bool:
    """Check whether all operator comparisons return the same result."""

    version_comparison = tuple(f(*pair_a) for f in COMPARISON_OPERATORS)
    package_comparison = tuple(f(*pair_b) for f in COMPARISON_OPERATORS)
    return version_comparison == package_comparison


@pytest.mark.parametrize("self_type", [PublicId, PackageId, Dependency])
def test_self_type_comparison(self_type):
    """Test comparison to self"""

    self = st.from_type(self_type).example()
    copy_self = copy.deepcopy(self)
    other = st.from_type(self_type).example()
    assert self == copy_self
    for f in COMPARISON_OPERATORS:
        assert isinstance(f(self, other), bool)
        assert isinstance(f(other, self), bool)


@pytest.mark.parametrize("self_type", [PublicId, PackageId, Dependency])
@pytest.mark.parametrize(
    "other_type", [*NUMERIC_TYPES, *ITERATOR_TYPES, PublicId, PackageId, Dependency]
)
def test_type_comparison(self_type, other_type):
    """Test type comparison"""

    if self_type is other_type:
        return

    funcs = (operator.le, operator.lt, operator.ge, operator.gt)
    self = st.from_type(self_type).example()
    other = st.from_type(other_type).example()

    assert not isinstance(self, other_type)
    assert not isinstance(other, self_type)
    assert self.__eq__(self)
    assert other.__eq__(other)
    assert self.__ne__(other)
    assert other.__ne__(self)

    for f in funcs:
        with pytest.raises((TypeError, ValueError)):
            assert f(self, other)


@given(st.tuples(version_info_strategy, version_info_strategy))
def test_package_version_comparison(version_pair):
    """Test package version comparison"""

    package_pair = tuple(map(PackageVersion, version_pair))
    assert all_comparisons_operations_equal(version_pair, package_pair)


@given(st.tuples(public_id_strategy, public_id_strategy))
def test_public_id_comparison(public_id_pair):
    """Test public id comparison"""

    public_id_pair[0]._name = public_id_pair[1]._name
    public_id_pair[0]._author = public_id_pair[1]._author
    version_pair = tuple(p.package_version._version for p in public_id_pair)
    assert all_comparisons_operations_equal(version_pair, public_id_pair)


@given(st.tuples(package_id_strategy, package_id_strategy))
def test_package_id_comparison(package_id_pair):
    """Test package id comparison"""

    package_id_pair[0]._public_id = package_id_pair[1]._public_id
    package_id_pair[0]._package_type = package_id_pair[1]._package_type
    version_pair = tuple(p.public_id.package_version._version for p in package_id_pair)
    assert all_comparisons_operations_equal(version_pair, package_id_pair)
