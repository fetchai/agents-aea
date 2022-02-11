# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains tests for the scaffold skill."""
from unittest.mock import MagicMock

import pytest

from aea.skills.base import SkillContext
from aea.skills.scaffold.behaviours import MyScaffoldBehaviour
from aea.skills.scaffold.handlers import MyScaffoldHandler
from aea.skills.scaffold.my_model import MyModel


class TestScaffoldHandler:
    """Tests for the scaffold handler."""

    @classmethod
    def setup_class(cls):
        """Set up the tests."""
        cls.handler = MyScaffoldHandler("handler", SkillContext())

    def test_supported_protocol(self):
        """Test that the supported protocol is None."""
        assert self.handler.SUPPORTED_PROTOCOL is None

    def test_setup(self):
        """Test that the setup method raises 'NotImplementedError'."""
        with pytest.raises(NotImplementedError):
            self.handler.setup()

    def test_handle(self):
        """Test that the handle method raises 'NotImplementedError'."""
        with pytest.raises(NotImplementedError):
            self.handler.handle(MagicMock())

    def test_teardown(self):
        """Test that the teardown method raises 'NotImplementedError'."""
        with pytest.raises(NotImplementedError):
            self.handler.teardown()


class TestScaffoldBehaviour:
    """Tests for the scaffold behaviour."""

    @classmethod
    def setup_class(cls):
        """Set up the tests."""
        cls.behaviour = MyScaffoldBehaviour("behaviour", SkillContext())

    def test_setup(self):
        """Test that the setup method raises 'NotImplementedError'."""
        with pytest.raises(NotImplementedError):
            self.behaviour.setup()

    def test_handle(self):
        """Test that the handle method raises 'NotImplementedError'."""
        with pytest.raises(NotImplementedError):
            self.behaviour.act()

    def test_teardown(self):
        """Test that the teardown method raises 'NotImplementedError'."""
        with pytest.raises(NotImplementedError):
            self.behaviour.teardown()


def test_model_initialization():
    """Test scaffold model initialization."""
    MyModel("model", SkillContext())
