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
"""This module contains the tests of the behaviour classes of the generic seller skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.behaviours import (
    GenericServiceRegistrationBehaviour,
    LEDGER_API_ADDRESS,
)
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of generic seller."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_seller")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.service_registration = cast(
            GenericServiceRegistrationBehaviour,
            cls._skill.skill_context.behaviours.service_registration,
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)

    def _assert_oef_message_and_logging_output(
        self, service_description, mocked_logger, logger_message
    ):
        """
        Check there is a specific OEFMessage in the outbox and the mocked logger is called with a specific message.

        This method is reused a few times in the following tests and its purpose is to avoid code duplication.

        :param service_description: the service description
        :param mocked_logger: the mocked logger
        :param logger_message: the logger message

        :return: None
        """
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=service_description,
        )
        assert has_attributes, error_str
        mocked_logger.assert_any_call(logging.INFO, logger_message)

    def test_setup_is_ledger_tx(self):
        """Test the setup method of the service_registration behaviour where is_ledger_tx is True."""
        # setup
        self.strategy._is_ledger_tx = True
        mocked_description_1 = "some_description_1"
        mocked_description_2 = "some_description_2"

        # operation
        with patch.object(
            self.strategy,
            "get_location_description",
            return_value=mocked_description_1,
        ):
            with patch.object(
                self.strategy,
                "get_register_service_description",
                return_value=mocked_description_2,
            ):
                with patch.object(
                    self.service_registration.context.logger, "log"
                ) as mock_logger:
                    self.service_registration.setup()

        # after
        self.assert_quantity_in_outbox(5)

        # message 1
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            to=LEDGER_API_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            ledger_id=self.strategy.ledger_id,
            address=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

        # message 2
        self._assert_oef_message_and_logging_output(
            mocked_description_1, mock_logger, "registering agent on SOEF.",
        )

        # message 3
        self._assert_oef_message_and_logging_output(
            mocked_description_2, mock_logger, "registering service on SOEF.",
        )

    def test_setup_not_is_ledger_tx(self):
        """Test the setup method of the service_registration behaviour: where is_ledger_tx is False."""
        # setup
        self.strategy._is_ledger_tx = False
        mocked_description_1 = "some_description_1"
        mocked_description_2 = "some_description_2"

        # operation
        with patch.object(
            self.strategy,
            "get_location_description",
            return_value=mocked_description_1,
        ):
            with patch.object(
                self.strategy,
                "get_register_service_description",
                return_value=mocked_description_2,
            ):
                with patch.object(
                    self.service_registration.context.logger, "log"
                ) as mock_logger:
                    self.service_registration.setup()

        # after
        self.assert_quantity_in_outbox(4)

        # message 1
        self._assert_oef_message_and_logging_output(
            mocked_description_1, mock_logger, "registering agent on SOEF.",
        )

        # message 2
        self._assert_oef_message_and_logging_output(
            mocked_description_2, mock_logger, "registering service on SOEF.",
        )

    def test_act(self):
        """Test the act method of the service_registration behaviour."""
        assert self.service_registration.act() is None
        self.assert_quantity_in_outbox(0)

    def test_teardown(self):
        """Test the teardown method of the service_registration behaviour."""
        # setup
        mocked_description_1 = "some_description_1"
        mocked_description_2 = "some_description_2"

        # operation
        with patch.object(
            self.strategy,
            "get_unregister_service_description",
            return_value=mocked_description_1,
        ):
            with patch.object(
                self.strategy,
                "get_location_description",
                return_value=mocked_description_2,
            ):
                with patch.object(
                    self.service_registration.context.logger, "log"
                ) as mock_logger:
                    self.service_registration.teardown()

        # after
        self.assert_quantity_in_outbox(2)

        # message 1
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_description_1,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering service from SOEF.")

        # message 2
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            service_description=mocked_description_2,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering agent from SOEF.")
