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
"""This module contains the tests of the behaviour classes of the registration_aw1 skill."""

import logging
from pathlib import Path
from unittest.mock import patch

from aea.helpers.transaction.base import RawMessage, Terms

from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_registration_aw1.intermediate_class import (
    RegiatrationAW1TestCase,
)


class TestAW1Registration(RegiatrationAW1TestCase):
    """Test registration behaviour of registration_aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "registration_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

    def test_setup_i(self):
        """Test the setup method of the registration behaviour NOT developer_handle_mode and announce_termination_key is None."""
        # setup
        self.strategy.announce_termination_key = None
        self.strategy.developer_handle_mode = False

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_behaviour.setup()

        # after
        self.assert_quantity_in_decision_making_queue(1)
        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            raw_message=RawMessage(
                self.strategy.ledger_id, self.strategy.ethereum_address.encode("utf-8")
            ),
            terms=Terms(
                ledger_id=self.strategy.ledger_id,
                sender_address="",
                counterparty_address="",
                amount_by_currency_id={},
                quantities_by_good_id={},
                nonce="",
            ),
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, "sending signing_msg to decision maker..."
        )

    def test_setup_ii(self):
        """Test the setup method of the registration behaviour IN developer_handle_mode and announce_termination_key is NOT None."""
        # setup
        key = "some_key"
        self.strategy.announce_termination_key = key
        self.strategy.developer_handle_only = True

        # operation
        self.register_behaviour.setup()

        # after
        self.assert_quantity_in_decision_making_queue(0)

        assert self.skill.skill_context.shared_state[key] is False

    def test_act_i(self):
        """Test the act method of the registration behaviour where is_ready_to_register is False."""
        # setup
        self.strategy.is_ready_to_register = False

        # operation
        self.register_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_ii(self):
        """Test the act method of the registration behaviour where aw1_registration_aeas is None."""
        # setup
        self.strategy.is_ready_to_register = True

        # operation
        self.register_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_iii(self):
        """Test the act method of the registration behaviour where is_registered is True."""
        # setup
        self.strategy.is_ready_to_register = True
        self.skill.skill_context.shared_state[
            self.shared_storage_key
        ] = self.aw1_registration_aeas
        self.strategy.is_registered = True

        # operation
        self.register_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_iv(self):
        """Test the act method of the registration behaviour where is_registration_pending is True."""
        # setup
        self.strategy.is_ready_to_register = True
        self.skill.skill_context.shared_state[
            self.shared_storage_key
        ] = self.aw1_registration_aeas
        self.strategy.is_registered = False
        self.strategy.is_registration_pending = True

        # operation
        self.register_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_v(self):
        """Test the act method of the registration behaviour where _register_for_aw1 is called."""
        # setup
        self.strategy.is_ready_to_register = True
        self.skill.skill_context.shared_state[
            self.shared_storage_key
        ] = self.aw1_registration_aeas
        self.strategy.is_registered = False
        self.strategy.is_registration_pending = False

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_behaviour.act()

        # after
        self.assert_quantity_in_outbox(len(self.aw1_registration_aeas))

        assert self.strategy.is_registration_pending is True

        # _register_for_aw1
        info = self.strategy.registration_info
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=RegisterMessage,
            performative=RegisterMessage.Performative.REGISTER,
            to=self.aw1_registration_aea,
            sender=self.skill.skill_context.agent_address,
            info=info,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, f"sending registration info: {info}",
        )

    def test_act_vi(self):
        """Test the act method of the registration behaviour where aw1 agent is NOT in the whitelist."""
        # setup
        self.strategy.is_ready_to_register = True
        self.skill.skill_context.shared_state[
            self.shared_storage_key
        ] = self.aw1_registration_aeas
        self.strategy.is_registered = False
        self.strategy.is_registration_pending = False
        self.strategy._whitelist = []

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

        assert self.strategy.is_registration_pending is True

        mock_logger.assert_any_call(
            logging.INFO,
            f"agent={self.aw1_registration_aea} not in whitelist={self.strategy._whitelist}",
        )

    def test_teardown(self):
        """Test the teardown method of the registration behaviour."""
        assert self.register_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
