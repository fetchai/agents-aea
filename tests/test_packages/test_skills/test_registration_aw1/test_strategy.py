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
from unittest.mock import patch

from aea.crypto.ledger_apis import LedgerApis

from packages.fetchai.skills.registration_aw1.strategy import Strategy

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

    def test__init__i(self):
        """Test __init__ where developer_handle_only is False."""
        announce_termination_key = True
        developer_handle_only = False

        with patch.object(LedgerApis, "is_valid_address", return_value=True):
            strategy = Strategy(
                developer_handle=self.developer_handle,
                ethereum_address=self.ethereum_address,
                signature_of_fetchai_address=self.signature_of_fetchai_address,
                shared_storage_key=self.shared_storage_key,
                whitelist=self.whitelist,
                tweet=self.tweet,
                announce_termination_key=announce_termination_key,
                developer_handle_only=developer_handle_only,
                name=Strategy,
                skill_context=self.skill.skill_context,
            )
        assert strategy._developer_handle == self.developer_handle
        assert strategy._whitelist == self.whitelist
        assert strategy._shared_storage_key == self.shared_storage_key
        assert strategy.announce_termination_key == announce_termination_key
        assert strategy.developer_handle_only == developer_handle_only

        assert strategy._ethereum_address == self.ethereum_address
        assert (
            strategy._signature_of_fetchai_address == self.signature_of_fetchai_address
        )
        assert strategy._tweet == self.tweet
        assert strategy._is_ready_to_register is False

        assert strategy._is_registered is False
        assert strategy.is_registration_pending is False
        assert strategy.signature_of_ethereum_address is None
        assert strategy._ledger_id == self.skill.skill_context.default_ledger_id

    def test__init__ii(self):
        """Test __init__ where developer_handle_only is True."""
        announce_termination_key = False
        developer_handle_only = True

        strategy = Strategy(
            developer_handle=self.developer_handle,
            ethereum_address=self.ethereum_address,
            signature_of_fetchai_address=self.signature_of_fetchai_address,
            shared_storage_key=self.shared_storage_key,
            whitelist=self.whitelist,
            tweet=self.tweet,
            announce_termination_key=announce_termination_key,
            developer_handle_only=developer_handle_only,
            name=Strategy,
            skill_context=self.skill.skill_context,
        )
        assert strategy._developer_handle == self.developer_handle
        assert strategy._whitelist == self.whitelist
        assert strategy._shared_storage_key == self.shared_storage_key
        assert strategy.announce_termination_key == announce_termination_key
        assert strategy.developer_handle_only == developer_handle_only

        assert strategy._is_ready_to_register is True
        assert strategy._ethereum_address == "some_dummy_address"
        assert strategy._signature_of_fetchai_address is None
        assert strategy._tweet is None

        assert strategy._is_registered is False
        assert strategy.is_registration_pending is False
        assert strategy.signature_of_ethereum_address is None
        assert strategy._ledger_id == self.skill.skill_context.default_ledger_id

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

        info_iii = {
            "fetchai_address": self.skill.skill_context.agent_address,
            "developer_handle": self.developer_handle,
        }
        self.strategy.developer_handle_only = True
        assert self.strategy.registration_info == info_iii
