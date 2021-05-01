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

from aea.helpers.search.models import Description
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
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.service_registration = cast(
            GenericServiceRegistrationBehaviour,
            cls._skill.skill_context.behaviours.service_registration,
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.registration_message = OefSearchMessage(
            dialogue_reference=("", ""),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description="some_service_description",
        )
        cls.registration_message.sender = str(cls._skill.skill_context.skill_id)
        cls.registration_message.to = cls._skill.skill_context.search_service_address

        cls.mocked_description = Description({"foo1": 1, "bar1": 2})

    def test_setup_is_ledger_tx(self):
        """Test the setup method of the service_registration behaviour where is_ledger_tx is True."""
        # setup
        self.strategy._is_ledger_tx = True
        mocked_description_1 = "some_description_1"

        # operation
        with patch.object(
            self.strategy,
            "get_location_description",
            return_value=mocked_description_1,
        ):
            with patch.object(
                self.service_registration.context.logger, "log"
            ) as mock_logger:
                self.service_registration.setup()

        # after
        self.assert_quantity_in_outbox(2)

        # message 1
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.strategy.ledger_id,
            address=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

        # _register_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=mocked_description_1,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering agent on SOEF.")

    def test_setup_not_is_ledger_tx(self):
        """Test the setup method of the service_registration behaviour: where is_ledger_tx is False."""
        # setup
        self.strategy._is_ledger_tx = False
        mocked_description_1 = "some_description_1"

        # operation
        with patch.object(
            self.strategy,
            "get_location_description",
            return_value=mocked_description_1,
        ):
            with patch.object(
                self.service_registration.context.logger, "log"
            ) as mock_logger:
                self.service_registration.setup()

        # after
        self.assert_quantity_in_outbox(1)

        # _register_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=mocked_description_1,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering agent on SOEF.")

    def test_act_i(self):
        """Test the act method of the service_registration behaviour where failed_registration_msg IS None."""
        # setup
        self.service_registration.failed_registration_msg = None

        # operation
        assert self.service_registration.act() is None

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_ii(self):
        """Test the act method of the service_registration behaviour where failed_registration_msg is NOT None."""
        # setup
        self.service_registration.failed_registration_msg = self.registration_message

        # operation
        with patch.object(
            self.service_registration.context.logger, "log"
        ) as mock_logger:
            self.service_registration.act()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=type(self.registration_message),
            performative=self.registration_message.performative,
            to=self.registration_message.to,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.registration_message.service_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"Retrying registration on SOEF. Retry {self.service_registration._nb_retries} out of {self.service_registration._max_soef_registration_retries}.",
        )
        assert self.service_registration.failed_registration_msg is None

    def test_act_iii(self):
        """Test the act method of the service_registration behaviour where failed_registration_msg is NOT None and max retries is reached."""
        # setup
        self.service_registration.failed_registration_msg = self.registration_message
        self.service_registration._max_soef_registration_retries = 2
        self.service_registration._nb_retries = 2

        # operation
        self.service_registration.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.skill.skill_context.is_active is False

    def test_register_service(self):
        """Test the register_service method of the service_registration behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_service_description",
            return_value=self.mocked_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.service_registration.register_service()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's service on the SOEF."
        )

    def test_register_genus(self):
        """Test the register_genus method of the service_registration behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_personality_description",
            return_value=self.mocked_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.service_registration.register_genus()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality genus on the SOEF."
        )

    def test_register_classification(self):
        """Test the register_classification method of the service_registration behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_classification_description",
            return_value=self.mocked_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.service_registration.register_classification()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality classification on the SOEF."
        )

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
            sender=str(self.skill.skill_context.skill_id),
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
            sender=str(self.skill.skill_context.skill_id),
            service_description=mocked_description_2,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering agent from SOEF.")
