# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This module contains tests for aea/components/utils.py"""
from itertools import chain
from unittest.mock import patch

from aea.components.utils import _enlist_component_packages, _populate_packages

from tests.test_aea import test_act


def test_modules_enlisted_and_loaded():
    """Test modules enlisted and loaded back."""
    # ensure some packages loaded
    test_act()

    packages = _enlist_component_packages()
    num_of_packages = len(list(chain(*packages.values())))
    assert num_of_packages > 0, "No packages present"

    with patch("aea.components.utils.perform_load_aea_package") as mock_package_load:
        _populate_packages(packages)
        assert mock_package_load.call_count == num_of_packages, packages
