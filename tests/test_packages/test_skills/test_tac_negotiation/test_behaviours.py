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
"""This module contains the tests of the behaviour classes of the tac negotiation skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import PropertyMock, patch

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.tac_negotiation.behaviours import (
    GoodsRegisterAndSearchBehaviour,
    TransactionCleanUpBehaviour,
)
from packages.fetchai.skills.tac_negotiation.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.tac_negotiation.strategy import Strategy
from packages.fetchai.skills.tac_negotiation.transactions import Transactions

from tests.conftest import ROOT_DIR


class TestSkillBehaviour(BaseSkillTestCase):
    """Test tac behaviour of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.tac_negotiation = cast(
            GoodsRegisterAndSearchBehaviour,
            cls._skill.skill_context.behaviours.tac_negotiation,
        )
        cls.oef_search_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.mocked_description = Description({"foo1": 1, "bar1": 2})
        cls.mocked_query = Query(
            [Constraint("tac_service", ConstraintType("==", "both"))]
        )
        cls.sender = (
            cls._skill.skill_context.agent_address
            + "_"
            + str(cls._skill.skill_context.skill_id)
        )

    def test_init(self):
        """Test the __init__ method of the negotiation behaviour."""
        assert self.tac_negotiation.is_registered is False

    def test_setup(self):
        """Test the setup method of the negotiation behaviour."""
        assert self.tac_negotiation.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act_i(self):
        """Test the act method of the negotiation behaviour where is_game_finished is True."""
        # setup
        self.skill.skill_context._agent_context._shared_state = {
            "is_game_finished": True
        }

        # operation
        self.tac_negotiation.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.skill.skill_context.is_active is False

    def test_register_agent(self):
        """Test the _register_agent method of the negotiation behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_location_description",
            return_value=self.mocked_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.tac_negotiation._register_agent()

        # after
        self.assert_quantity_in_outbox(1)

        # _register_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.sender,
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering agent on SOEF.")

    def test_register_service(self):
        """Test the _register_service method of the negotiation behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_service_description",
            return_value=self.mocked_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.tac_negotiation._register_service()

        # after
        self.assert_quantity_in_outbox(1)

        # _register_service
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"updating service directory as {self.strategy.registering_as}.",
        )
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.sender,
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str

    def test_search_services(self):
        """Test the _search_services method of the negotiation behaviour."""
        # setup
        searching_for_types = [(True, "sellers"), (False, "buyers")]
        no_searches = len(searching_for_types)

        # operation
        with patch.object(
            self.strategy,
            "get_location_and_service_query",
            return_value=self.mocked_query,
        ):
            with patch.object(
                type(self.strategy),
                "searching_for_types",
                new_callable=PropertyMock,
                return_value=searching_for_types,
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    self.tac_negotiation._search_services()

        # after
        self.assert_quantity_in_outbox(no_searches)

        # _search_services
        for search in searching_for_types:
            message = self.get_message_from_outbox()
            has_attributes, error_str = self.message_has_attributes(
                actual_message=message,
                message_type=OefSearchMessage,
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                to=self.skill.skill_context.search_service_address,
                sender=self.sender,
                query=self.mocked_query,
            )
            assert has_attributes, error_str

            assert (
                cast(
                    OefSearchDialogue, self.oef_search_dialogues.get_dialogue(message)
                ).is_seller_search
                == search[0]
            )

            mock_logger.assert_any_call(
                logging.INFO,
                f"searching for {search[1]}, search_id={message.dialogue_reference}.",
            )

    def test_teardown_i(self):
        """Test the teardown method of the negotiation behaviour."""
        # setup
        self.tac_negotiation.is_registered = True

        # operation
        with patch.object(
            self.strategy,
            "get_unregister_service_description",
            return_value=self.mocked_description,
        ):
            with patch.object(
                self.strategy,
                "get_location_description",
                return_value=self.mocked_description,
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    self.tac_negotiation.teardown()

        # after
        self.assert_quantity_in_outbox(2)

        # _unregister_service
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.sender,
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"unregistering from service directory as {self.strategy.registering_as}.",
        )

        # _unregister_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=self.sender,
            service_description=self.mocked_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering agent from SOEF.")

        # teardown
        assert self.tac_negotiation.is_registered is False

    def test_teardown_ii(self):
        """Test the teardown method of the negotiation behaviour where is_registered is False."""
        # setup
        self.tac_negotiation.is_registered = False

        # operation
        assert self.tac_negotiation.teardown() is None

        # after
        self.assert_quantity_in_outbox(0)


class TestTransactionCleanUpBehaviour(BaseSkillTestCase):
    """Test clean_up behaviour of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.clean_up_behaviour = cast(
            TransactionCleanUpBehaviour, cls._skill.skill_context.behaviours.clean_up
        )
        cls.transactions = cast(Transactions, cls._skill.skill_context.transactions)

    def test_setup(self):
        """Test the setup method of the clean_up behaviour."""
        assert self.clean_up_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act(self):
        """Test the act method of the clean_up behaviour."""
        # operation
        with patch.object(
            self.transactions, "update_confirmed_transactions"
        ) as mocked_update:
            with patch.object(
                self.transactions, "cleanup_pending_transactions"
            ) as mocked_cleanup:
                self.clean_up_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        mocked_update.assert_called_once()
        mocked_cleanup.assert_called_once()

    def test_teardown(self):
        """Test the teardown method of the clean_up behaviour."""
        assert self.clean_up_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
