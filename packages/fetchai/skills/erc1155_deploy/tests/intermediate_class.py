# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This module sets up test environment for erc1155_deploy skill."""
# pylint: skip-file

from pathlib import Path
from typing import cast

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Location,
    Query,
)
from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedTransaction,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.contract_api.custom_types import Kwargs
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_deploy.behaviours import (
    ServiceRegistrationBehaviour,
)
from packages.fetchai.skills.erc1155_deploy.dialogues import (
    ContractApiDialogues,
    DefaultDialogues,
    FipaDialogues,
    LedgerApiDialogues,
    OefSearchDialogues,
    SigningDialogues,
)
from packages.fetchai.skills.erc1155_deploy.handlers import (
    ContractApiHandler,
    FipaHandler,
    LedgerApiHandler,
    OefSearchHandler,
    SigningHandler,
)
from packages.fetchai.skills.erc1155_deploy.strategy import Strategy
from packages.open_aea.protocols.signing.message import SigningMessage


PACKAGE_ROOT = Path(__file__).parent.parent


class ERC1155DeployTestCase(BaseSkillTestCase):
    """Sets the erc1155_deploy class up for testing."""

    path_to_skill = PACKAGE_ROOT

    def setup(self):
        """Setup the test class."""
        self.location = {"longitude": 0.1270, "latitude": 51.5194}
        self.mint_quantities = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        self.service_data = {"key": "seller_service", "value": "some_value"}
        self.personality_data = {"piece": "genus", "value": "some_personality"}
        self.classification = {
            "piece": "classification",
            "value": "some_classification",
        }
        self.from_supply = 756
        self.to_supply = 12
        self.value = 87
        self.token_type = 2
        config_overrides = {
            "models": {
                "strategy": {
                    "args": {
                        "location": self.location,
                        "mint_quantities": self.mint_quantities,
                        "service_data": self.service_data,
                        "personality_data": self.personality_data,
                        "classification": self.classification,
                        "from_supply": self.from_supply,
                        "to_supply": self.to_supply,
                        "value": self.value,
                        "token_type": self.token_type,
                    }
                }
            },
        }

        super().setup(config_overrides=config_overrides)

        # behaviours
        self.registration_behaviour = cast(
            ServiceRegistrationBehaviour,
            self._skill.skill_context.behaviours.service_registration,
        )

        # dialogues
        self.contract_api_dialogues = cast(
            ContractApiDialogues, self._skill.skill_context.contract_api_dialogues
        )
        self.default_dialogues = cast(
            DefaultDialogues, self._skill.skill_context.default_dialogues
        )
        self.fipa_dialogues = cast(
            FipaDialogues, self._skill.skill_context.fipa_dialogues
        )
        self.ledger_api_dialogues = cast(
            LedgerApiDialogues, self._skill.skill_context.ledger_api_dialogues
        )
        self.oef_search_dialogues = cast(
            OefSearchDialogues, self._skill.skill_context.oef_search_dialogues
        )
        self.signing_dialogues = cast(
            SigningDialogues, self._skill.skill_context.signing_dialogues
        )

        # handlers
        self.fipa_handler = cast(FipaHandler, self._skill.skill_context.handlers.fipa)
        self.oef_search_handler = cast(
            OefSearchHandler, self._skill.skill_context.handlers.oef_search
        )
        self.contract_api_handler = cast(
            ContractApiHandler, self._skill.skill_context.handlers.contract_api
        )
        self.signing_handler = cast(
            SigningHandler, self._skill.skill_context.handlers.signing
        )
        self.ledger_api_handler = cast(
            LedgerApiHandler, self._skill.skill_context.handlers.ledger_api
        )

        # models
        self.strategy = cast(Strategy, self._skill.skill_context.strategy)

        self.logger = self._skill.skill_context.logger

        # mocked objects
        self.ledger_id = "some_ledger_id"
        self.contract_id = "some_contract_id"
        self.contract_address = "some_contract_address"
        self.callable = "some_callable"
        self.body_dict = {"some_key": "some_value"}
        self.body_str = "some_body"
        self.body_bytes = b"some_body"
        self.kwargs = Kwargs(self.body_dict)
        self.address = "some_address"

        self.mocked_terms = Terms(
            self.ledger_id,
            self._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        self.mocked_query = Query(
            [Constraint("some_attribute_name", ConstraintType("==", "some_value"))],
            DataModel(
                "some_data_model_name",
                [
                    Attribute(
                        "some_attribute_name",
                        str,
                        False,
                        "Some attribute descriptions.",
                    )
                ],
            ),
        )
        self.mocked_proposal = Description(
            {
                "contract_address": "some_contract_address",
                "token_id": "123456",
                "trade_nonce": "876438756348568",
                "from_supply": "543",
                "to_supply": "432",
                "value": "67",
            }
        )
        self.mocked_registration_description = Description({"foo1": 1, "bar1": 2})

        self.mocked_raw_tx = RawTransaction(self.ledger_id, self.body_dict)
        self.mocked_raw_msg = RawMessage(self.ledger_id, self.body_bytes)
        self.mocked_tx_digest = TransactionDigest(self.ledger_id, self.body_str)
        self.mocked_signed_tx = SignedTransaction(self.ledger_id, self.body_dict)
        self.mocked_tx_receipt = TransactionReceipt(
            self.ledger_id,
            {"receipt_key": "receipt_value", "contractAddress": self.contract_address},
            {"transaction_key": "transaction_value"},
        )

        self.registration_message = OefSearchMessage(
            dialogue_reference=("", ""),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=self.mocked_registration_description,
        )
        self.registration_message.sender = str(self._skill.skill_context.skill_id)
        self.registration_message.to = self._skill.skill_context.search_service_address

        # list of messages
        self.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": self.mocked_query}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": self.mocked_proposal}
            ),
        )
        self.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                {
                    "ledger_id": self.ledger_id,
                    "contract_id": self.contract_id,
                    "contract_address": self.contract_address,
                    "callable": self.callable,
                    "kwargs": self.kwargs,
                },
            ),
        )
        self.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {"terms": self.mocked_terms, "raw_transaction": self.mocked_raw_tx},
            ),
        )
        self.list_of_ledger_api_balance_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_BALANCE,
                {"ledger_id": self.ledger_id, "address": "some_address"},
            ),
        )

        self.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                {"terms": self.mocked_terms},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.RAW_TRANSACTION,
                {"raw_transaction": self.mocked_raw_tx},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                {"signed_transaction": self.mocked_signed_tx},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                {"transaction_digest": self.mocked_tx_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {"transaction_digest": self.mocked_tx_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                {"transaction_receipt": self.mocked_tx_receipt},
            ),
        )
        self.register_location_description = Description(
            {"location": Location(51.5194, 0.1270)},
            data_model=DataModel(
                "location_agent", [Attribute("location", Location, True)]
            ),
        )
        self.list_of_messages_register_location = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": self.register_location_description},
                is_incoming=False,
            ),
        )

        self.register_service_description = Description(
            {"key": "some_key", "value": "some_value"},
            data_model=DataModel(
                "set_service_key",
                [Attribute("key", str, True), Attribute("value", str, True)],
            ),
        )
        self.list_of_messages_register_service = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": self.register_service_description},
                is_incoming=False,
            ),
        )

        self.register_genus_description = Description(
            {"piece": "genus", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        self.list_of_messages_register_genus = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": self.register_genus_description},
                is_incoming=False,
            ),
        )

        self.register_classification_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        self.list_of_messages_register_classification = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": self.register_classification_description},
                is_incoming=False,
            ),
        )

        self.register_invalid_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "some_different_name",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        self.list_of_messages_register_invalid = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": self.register_invalid_description},
                is_incoming=False,
            ),
        )
