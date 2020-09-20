# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This test module contains the tests for CLI core methods."""

from unittest import TestCase, mock

from click import ClickException

from aea.cli.core import _init_gui
from aea.cli.utils.constants import AUTHOR_KEY


@mock.patch("aea.cli.core.get_or_create_cli_config")
class InitGuiTestCase(TestCase):
    """Test case for _init_gui method."""

    def test__init_gui_positive(self, get_or_create_cli_config_mock):
        """Test _init_gui method for positive result."""
        config = {AUTHOR_KEY: "author"}
        get_or_create_cli_config_mock.return_value = config

        _init_gui()

    def test__init_gui_negative(self, get_or_create_cli_config_mock):
        """Test _init_gui method for negative result."""
        get_or_create_cli_config_mock.return_value = {}
        with self.assertRaises(ClickException):
            _init_gui()
