# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains tests for the aea.helpers.pypi module."""
import pytest
from packaging.specifiers import SpecifierSet

from aea.configurations.base import Dependency
from aea.configurations.pypi import (
    is_satisfiable,
    is_simple_dep,
    merge_dependencies,
    merge_dependencies_list,
    to_set_specifier,
)


def test_is_satisfiable_common_cases():
    """Test the 'is_satisfiable' function with common cases."""
    assert is_satisfiable(SpecifierSet("<=1.0,>1.1, >0.9")) is False
    assert is_satisfiable(SpecifierSet("==1.0,!=1.0")) is False
    assert is_satisfiable(SpecifierSet("!=0.9,!=1.0")) is True
    assert is_satisfiable(SpecifierSet("<=1.0,>=1.0")) is True
    assert is_satisfiable(SpecifierSet("<=1.0,>1.0")) is False
    assert is_satisfiable(SpecifierSet("<1.0,<=1.0,>1.0")) is False
    assert is_satisfiable(SpecifierSet(">1.0,>=1.0,<1.0")) is False


def test_is_satisfiable_with_compatibility_constraints():
    """Test the 'is_satisfiable' function with ~= constraints."""
    assert is_satisfiable(SpecifierSet("~=1.1,==2.0")) is False
    assert is_satisfiable(SpecifierSet("~=1.1,==1.0")) is False
    assert is_satisfiable(SpecifierSet("~=1.1,<=1.1")) is True
    assert is_satisfiable(SpecifierSet("~=1.1,<1.1")) is False
    assert is_satisfiable(SpecifierSet("~=1.0,<1.0")) is False
    assert is_satisfiable(SpecifierSet("~=1.1,==1.2")) is True
    assert is_satisfiable(SpecifierSet("~=1.1,>1.2")) is True
    assert is_satisfiable(SpecifierSet("==1.1,==1.2")) is False
    assert is_satisfiable(SpecifierSet("~= 1.4.5.0")) is True
    assert is_satisfiable(SpecifierSet("~= 1.4.5.0,>1.4.6")) is False
    assert is_satisfiable(SpecifierSet("~=2.2.post3,==2.*")) is True
    assert is_satisfiable(SpecifierSet("~=2.2.post3,>2.3")) is True
    assert is_satisfiable(SpecifierSet("~=2.2.post3,>3")) is False
    assert is_satisfiable(SpecifierSet("~=1.4.5a4,>1.4.6")) is True
    assert is_satisfiable(SpecifierSet("~=1.4.5a4,>1.5")) is False


def test_is_satisfiable_with_legacy_version():
    """Test the 'is_satisfiable' function with legacy versions."""
    assert is_satisfiable(SpecifierSet("==1.0,==1.*")) is True


def test_merge_dependencies():
    """Test the 'merge_dependencies' function."""
    dependencies_a = {
        "package_1": Dependency("package_1", "==0.1.0"),
        "package_2": Dependency("package_2", "==0.3.0"),
        "package_3": Dependency("package_3", "==0.2.0", "https://pypi.org"),
    }
    dependencies_b = {
        "package_1": Dependency("package_1", "==0.1.0"),
        "package_2": Dependency("package_2", "==0.2.0"),
        "package_4": Dependency("package_4", "==0.1.0", "https://pypi.org"),
    }
    expected_merged_dependencies = {
        "package_1": Dependency("package_1", "==0.1.0"),
        "package_2": Dependency("package_2", "==0.2.0,==0.3.0"),
        "package_3": Dependency("package_3", "==0.2.0", "https://pypi.org"),
        "package_4": Dependency("package_4", "==0.1.0", "https://pypi.org"),
    }
    assert expected_merged_dependencies == merge_dependencies(
        dependencies_a, dependencies_b
    )
    assert expected_merged_dependencies == merge_dependencies_list(
        dependencies_a, dependencies_b
    )


def test_merge_dependencies_fails_not_simple():
    """Test we can't merge dependencies if at least one of the overlapping dependency is not 'simple'."""
    dependencies_a = {
        "package_1": Dependency("package_1", "==0.1.0", index="https://pypi.org"),
    }
    dependencies_b = {
        "package_1": Dependency("package_1", "==0.1.0", index="https://test.pypi.org"),
    }

    with pytest.raises(
        ValueError, match="cannot trivially merge these two PyPI dependencies:.*"
    ):
        merge_dependencies(dependencies_a, dependencies_b)


def test_merge_dependencies_succeeds_not_simple_but_the_same():
    """Test we can't merge dependencies if conflicting deps are not 'simple' but equal."""
    dependencies_a = {
        "package_1": Dependency("package_1", "==0.1.0", index="https://pypi.org"),
    }
    dependencies_b = {
        "package_1": Dependency("package_1", "==0.1.0", index="https://pypi.org"),
    }

    expected_merged_dependencies = merge_dependencies(dependencies_a, dependencies_b)
    assert dependencies_a == dependencies_b == expected_merged_dependencies


def test_is_simple_dep():
    """Test the `is_simple_dep` function."""
    dependency_a = Dependency("name", "==0.1.0")
    assert is_simple_dep(dependency_a), "Should be a simple dependency."
    dependency_b = Dependency("name")
    assert is_simple_dep(dependency_b), "Should be a simple dependency."
    dependency_c = Dependency("name", "==0.1.0", "pypi")
    assert not is_simple_dep(dependency_c), "Should not be a simple dependency."


def test_to_set_specifier():
    """Test the 'to_set_specifier' function."""
    dependency_a = Dependency("name", "==0.1.0")
    assert to_set_specifier(dependency_a) == SpecifierSet("==0.1.0")
