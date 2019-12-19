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

"""This module contains the tests for the helper module."""
import os
import sys

from aea.helpers.base import locate
from packages.connections.oef.connection import OEFConnection
from ..conftest import CUR_PATH


class TestHelpersBase:
    """Test the helper functions."""

    def test_locate(self):
        """Test the locate function to locate modules."""
        cwd = os.getcwd()
        os.chdir(os.path.join(CUR_PATH, ".."))
        sys.modules["gym_connection"] = locate("packages.connections.gym")
        assert sys.modules['gym_connection'] is not None
        sys.modules["gym_connection"] = locate("packages.connections.weather")
        assert sys.modules['gym_connection'] is None
        os.chdir(cwd)

    def test_locate_class(self):
        """Test the locate function to locate classes."""
        cwd = os.getcwd()
        os.chdir(os.path.join(CUR_PATH, ".."))
        expected_class = OEFConnection
        actual_class = locate("packages.connections.oef.connection.OEFConnection")
        # although they are the same class, they are different instances in memory
        # and the build-in default "__eq__" method does not compare the attributes.
        # so compare the names
        assert actual_class is not None
        assert expected_class.__name__ == actual_class.__name__
        os.chdir(cwd)

    def test_locate_with_builtins(self):
        """Test that locate function returns the built-in."""
        result = locate("int.bit_length")
        assert int.bit_length == result

    def test_locate_when_path_does_not_exist(self):
        """Test that locate function returns None when the dotted path does not exist."""
        result = locate("aea.not.existing.path")
        assert result is None

        result = locate("ThisClassDoesNotExist")
        assert result is None
