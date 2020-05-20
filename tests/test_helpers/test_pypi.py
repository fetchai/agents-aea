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

from aea.helpers.pypi import is_satisfiable


def test_is_satisfiable():
    """Test the 'is_satisfiable' function."""

    assert is_satisfiable(SpecifierSet("<=1.0,>1.1, >0.9")) is False
    assert is_satisfiable(SpecifierSet("==1.0,!=1.0")) is False
    assert is_satisfiable(SpecifierSet("!=0.9,!=1.0")) is True
    assert is_satisfiable(SpecifierSet("<=1.0,>=1.0")) is True
    assert is_satisfiable(SpecifierSet("<=1.0,>1.0")) is False
    assert is_satisfiable(SpecifierSet("<1.0,<=1.0,>1.0")) is False
    assert is_satisfiable(SpecifierSet(">1.0,>=1.0,<1.0")) is False
    assert is_satisfiable(SpecifierSet("~=1.1,==2.0")) is False
    assert is_satisfiable(SpecifierSet("~=1.1,==1.0")) is False
    assert is_satisfiable(SpecifierSet("~=1.1,<=1.1")) is True
    assert is_satisfiable(SpecifierSet("~=1.1,<1.1")) is False
    assert is_satisfiable(SpecifierSet("~=1.0,<1.0")) is False
    assert is_satisfiable(SpecifierSet("~=1.1,==1.2")) is True
    assert is_satisfiable(SpecifierSet("~=1.1,>1.2")) is True

    # We ignore legacy versions:
    assert is_satisfiable(SpecifierSet("==1.0,==1.*")) is True
