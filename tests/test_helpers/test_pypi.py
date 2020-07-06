# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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
from packaging.specifiers import SpecifierSet

from aea.helpers.pypi import (
    is_satisfiable,
    is_simple_dep,
    merge_dependencies,
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


def test_is_satisfiable_with_legacy_version():
    """Test the 'is_satisfiable' function with legacy versions."""
    assert is_satisfiable(SpecifierSet("==1.0,==1.*")) is True


def test_merge_dependencies():
    """Test the 'merge_dependencies' function."""
    dependencies_a = {
        "package_1": {"version": "==0.1.0"},
        "package_2": {"version": "==0.3.0"},
        "package_3": {"version": "0.2.0", "index": "pypi"},
    }
    dependencies_b = {
        "package_1": {"version": "==0.1.0"},
        "package_2": {"version": "==0.2.0"},
        "package_4": {"version": "0.1.0", "index": "pypi"},
    }
    merged_dependencies = {
        "package_1": {"version": "==0.1.0"},
        "package_2": {"version": "==0.2.0,==0.3.0"},
    }
    assert merged_dependencies == merge_dependencies(dependencies_a, dependencies_b)


def test_is_simple_dep():
    """Test the `is_simple_dep` function."""
    dependency_a = {"version": "==0.1.0"}
    assert is_simple_dep(dependency_a), "Should be a simple dependency."
    dependency_b = {}
    assert is_simple_dep(dependency_b), "Should be a simple dependency."
    dependency_c = {"version": "==0.1.0", "index": "pypi"}
    assert not is_simple_dep(dependency_c), "Should not be a simple dependency."


def test_to_set_specifier():
    """Test the 'to_set_specifier' function."""
    dependency_a = {"version": "==0.1.0"}
    assert to_set_specifier(dependency_a) == "==0.1.0"
