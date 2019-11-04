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

"""This test module contains the tests for the `aea create` sub-command."""
from .test_base import TestBase


class TestCreateConnectionAndList(TestBase):
    """Test that the gui home page exits and has the correct title."""

    def test_create_and_list_connections(self):
        self._test_create_and_list("connection", "local")

class TestCreateProtocolAndList(TestBase):
    """Test that the gui home page exits and has the correct title."""

    def test_create_and_list_protocols(self):
        self._test_create_and_list("protocol", "fipa")


class TestCreateSkillAndList(TestBase):
    """Test that the gui home page exits and has the correct title."""

    def test_create_and_list_skills(self):
        self._test_create_and_list("skill", "scaffold")

