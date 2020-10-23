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
"""This module contains the tests of the helpers module of the tac control skill."""

from pathlib import Path

import pytest

from aea.exceptions import AEAEnforceError
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_control.helpers import (
    generate_currency_id_to_name,
    generate_good_id_to_name,
)

from tests.conftest import ROOT_DIR


class TestHelpers(BaseSkillTestCase):
    """Test Helper module methods of tac control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_control")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

    def test_generate_currency_id_to_name(self):
        """Test the generate_currency_id_to_name of Helpers module."""
        # phase
        with pytest.raises(
            AEAEnforceError,
            match="Length of currency_ids does not match nb_currencies.",
        ):
            assert generate_currency_id_to_name(nb_currencies=1, currency_ids=[1, 2])

    def test_generate_good_id_to_name(self):
        """Test the generate_good_id_to_name of Helpers module."""
        # phase
        with pytest.raises(
            AEAEnforceError, match="Length of good_ids does not match nb_goods."
        ):
            assert generate_good_id_to_name(nb_goods=1, good_ids=[1, 2])
