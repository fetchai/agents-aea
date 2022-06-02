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
"""Test helper to install python dependecies."""
from unittest import mock
from unittest.case import TestCase

import pytest

from aea.configurations.base import Dependency
from aea.exceptions import AEAException
from aea.helpers.install_dependency import install_dependencies, install_dependency


class InstallDependencyTestCase(TestCase):
    """Test case for _install_dependency method."""

    def test__install_dependency_fails(self, *mocks):
        """Test for install_dependency method fails."""
        result = mock.Mock()
        result.returncode = 1
        with mock.patch("subprocess.run", return_value=result):
            with self.assertRaises(AEAException):
                install_dependency("test", Dependency("test", "==10.0.0"), mock.Mock())

    def test__install_dependency_ok(self, *mocks):
        """Test for install_dependency method ok."""
        result = mock.Mock()
        result.returncode = 0
        with mock.patch("subprocess.run", return_value=result):
            install_dependency("test", Dependency("test", "==10.0.0"), mock.Mock())

    def test__install_dependency_fails_real_pip_call(self):
        """Test for install_dependency method fails."""
        with pytest.raises(AEAException, match=r"No matching distribution found"):
            install_dependency(
                "testnotexists", Dependency("testnotexists", "==10.0.0"), mock.Mock()
            )


class InstallDependenciesTestCase(TestCase):
    """Test case for _install_dependencies method."""

    def test_fails(self, *mocks):
        """Test for install_dependency method fails."""
        result = mock.Mock()
        result.returncode = 1
        with mock.patch("subprocess.run", return_value=result):
            with self.assertRaises(AEAException):
                install_dependencies([Dependency("test", "==10.0.0")], mock.Mock())

    def test_ok(self, *mocks):
        """Test for install_dependency method ok."""
        result = mock.Mock()
        result.returncode = 0
        with mock.patch("subprocess.run", return_value=result):
            install_dependencies([Dependency("test", "==10.0.0")], mock.Mock())

    def test_fails_real_pip_call(self):
        """Test for install_dependency method fails."""
        with pytest.raises(AEAException, match=r"No matching distribution found"):
            install_dependencies([Dependency("testnotexists", "==10.0.0")], mock.Mock())

        """Test for install_dependency method fails."""
        with pytest.raises(AEAException, match=r"No matching distribution found"):
            install_dependency(
                "testnotexists", Dependency("testnotexists", "==10.0.0"), mock.Mock()
            )
