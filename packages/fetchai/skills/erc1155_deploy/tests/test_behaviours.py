# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests of the behaviour classes of the erc1155_deploy skill."""
# pylint: skip-file

import logging
from typing import cast
from unittest.mock import patch

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_deploy.behaviours import LEDGER_API_ADDRESS
from packages.fetchai.skills.erc1155_deploy.dialogues import ContractApiDialogue
from packages.fetchai.skills.erc1155_deploy.tests.intermediate_class import (
    ERC1155DeployTestCase,
)


class TestServiceRegistrationBehaviour(ERC1155DeployTestCase):
    """Test registration behaviour of erc1155_deploy."""

    def test_init(self):
        """Test the __init__ method of the registration behaviour."""
        assert self.registration_behaviour.is_registered is False
        assert self.registration_behaviour.registration_in_progress is False
        assert self.registration_behaviour.failed_registration_msg is None
        assert self.registration_behaviour._nb_retries == 0

    def test_setup(self):
        """Test the setup method of the registration behaviour."""
        # setup
        self.strategy._is_contract_deployed = False

        # before
        assert self.strategy.is_behaviour_active is True

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.registration_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(2)

        # _request_balance
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.strategy.ledger_id,
            address=cast(
                str,
                self.skill.skill_context.agent_addresses.get(self.strategy.ledger_id),
            ),
        )
        assert has_attributes, error_str

        # _request_contract_deploy_transaction
        assert self.strategy.is_behaviour_active is False

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.strategy.ledger_id,
            contract_id=self.strategy.contract_id,
            callable="get_deploy_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.skill.skill_context.agent_address,
                    "gas": self.strategy.gas,
                }
            ),
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, "requesting contract deployment transaction..."
        )

    def test_act_i(self):
        """Test the act method of the registration behaviour where failed_registration_msg is NOT None."""
        # setup
        self.registration_behaviour.failed_registration_msg = self.registration_message

        with patch.object(self.logger, "log") as mock_logger:
            self.registration_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _retry_failed_registration
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
            f"Retrying registration on SOEF. Retry {self.registration_behaviour._nb_retries} out of {self.registration_behaviour._max_soef_registration_retries}.",
        )
        assert self.registration_behaviour.failed_registration_msg is None

    def test_act_ii(self):
        """Test the act method of the registration behaviour where failed_registration_msg is NOT None and max retries is reached."""
        # setup
        self.registration_behaviour.failed_registration_msg = self.registration_message
        self.registration_behaviour._max_soef_registration_retries = 2
        self.registration_behaviour._nb_retries = 2

        self.registration_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.skill.skill_context.is_active is False

    def test_act_iii(self):
        """Test the act method of the registration behaviour where is_behaviour_active IS False."""
        # setup
        self.strategy.is_behaviour_active = False

        # operation
        self.registration_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_iv(self):
        """Test the act method of the registration behaviour where is_contract_deployed IS True and is_tokens_created IS False."""
        # setup
        self.strategy.is_contract_deployed = True
        self.strategy._is_tokens_created = False
        self.strategy._contract_address = self.contract_address

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.registration_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        assert self.strategy.is_behaviour_active is False

        # _request_token_create_transaction
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.strategy.ledger_id,
            contract_id=self.strategy.contract_id,
            contract_address=self.strategy.contract_address,
            callable="get_create_batch_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.skill.skill_context.agent_address,
                    "token_ids": self.strategy.token_ids,
                    "gas": self.strategy.gas,
                }
            ),
        )
        assert has_attributes, error_str

        contract_api_dialogue = cast(
            ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
        )
        assert contract_api_dialogue.terms == self.strategy.get_create_token_terms()

        mock_logger.assert_any_call(
            logging.INFO, "requesting create batch transaction..."
        )

    def test_act_v(self):
        """Test the act method of the registration behaviour where is_contract_deployed IS True, is_tokens_created IS True and is_tokens_minted is False."""
        # setup
        self.strategy.is_contract_deployed = True
        self.strategy._is_tokens_created = True
        self.strategy._is_tokens_minted = False
        self.strategy._contract_address = self.contract_address

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.registration_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        assert self.strategy.is_behaviour_active is False

        # _request_token_mint_transaction
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.strategy.ledger_id,
            contract_id=self.strategy.contract_id,
            contract_address=self.strategy.contract_address,
            callable="get_mint_batch_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "deployer_address": self.skill.skill_context.agent_address,
                    "recipient_address": self.skill.skill_context.agent_address,
                    "token_ids": self.strategy.token_ids,
                    "mint_quantities": self.strategy.mint_quantities,
                    "gas": self.strategy.gas,
                }
            ),
        )
        assert has_attributes, error_str

        contract_api_dialogue = cast(
            ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
        )
        assert contract_api_dialogue.terms == self.strategy.get_mint_token_terms()

        mock_logger.assert_any_call(
            logging.INFO, "requesting mint batch transaction..."
        )

    def test_act_vi(self):
        """Test the act method of the registration behaviour where is_contract_deployed IS True, is_tokens_created IS True and is_tokens_minted is True and is_registered IS False."""
        # setup
        self.strategy.is_contract_deployed = True
        self.strategy._is_tokens_created = True
        self.strategy._is_tokens_minted = True
        self.strategy._contract_address = self.contract_address

        # before
        assert self.registration_behaviour.registration_in_progress is False

        # operation
        with patch.object(
            self.strategy,
            "get_location_description",
            return_value=self.mocked_registration_description,
        ) as mock_desc:
            with patch.object(self.logger, "log") as mock_logger:
                self.registration_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        assert self.registration_behaviour.registration_in_progress is True

        # _register_agent
        mock_desc.assert_called_once()

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering agent on SOEF.")

    def test_register_service(self):
        """Test the register_service method of the registration behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_service_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.registration_behaviour.register_service()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's service on the SOEF."
        )

    def test_register_genus(self):
        """Test the register_genus method of the registration behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_personality_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.registration_behaviour.register_genus()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality genus on the SOEF."
        )

    def test_register_classification(self):
        """Test the register_classification method of the registration behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_classification_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.registration_behaviour.register_classification()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality classification on the SOEF."
        )

    def test_teardown(self):
        """Test the teardown method of the service_registration behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_unregister_service_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(
                self.strategy,
                "get_location_description",
                return_value=self.mocked_registration_description,
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    self.registration_behaviour.teardown()

        # after
        self.assert_quantity_in_outbox(2)

        # _unregister_service
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering service from SOEF.")

        # _unregister_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering agent from SOEF.")
