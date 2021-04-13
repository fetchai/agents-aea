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
"""This module contains the tests of the strategy class of the registration_aw1 skill."""

from pathlib import Path

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_registration_aw1.intermediate_class import (
    RegiatrationAW1TestCase,
)


class TestStrategy(RegiatrationAW1TestCase):
    """Test Strategy of registration_aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "registration_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.shared_storage_key == self.shared_storage_key
        assert self.strategy.whitelist == self.whitelist
        assert self.strategy.ethereum_address == self.ethereum_address
        assert self.strategy.ledger_id == self.skill.skill_context.default_ledger_id

        assert self.strategy.is_registration_pending is False
        assert self.strategy.signature_of_ethereum_address is None

        assert self.strategy.is_ready_to_register is False
        self.strategy.is_ready_to_register = True
        assert self.strategy.is_ready_to_register is True

        assert self.strategy.is_registered is False
        self.strategy.is_registered = True
        assert self.strategy.is_registered is True

        info_i = {
            "ethereum_address": self.ethereum_address,
            "fetchai_address": self.skill.skill_context.agent_address,
            "signature_of_ethereum_address": self.strategy.signature_of_ethereum_address,
            "signature_of_fetchai_address": self.signature_of_fetchai_address,
            "developer_handle": self.developer_handle,
            "tweet": self.tweet,
        }

        assert self.strategy.registration_info == info_i

        self.strategy._tweet = "PUT_THE_LINK_TO_YOUR_TWEET_HERE"
        info_ii = {
            "ethereum_address": self.ethereum_address,
            "fetchai_address": self.skill.skill_context.agent_address,
            "signature_of_ethereum_address": self.strategy.signature_of_ethereum_address,
            "signature_of_fetchai_address": self.signature_of_fetchai_address,
            "developer_handle": self.developer_handle,
        }

        assert self.strategy.registration_info == info_ii
