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

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.location = {"longitude": 0.1270, "latitude": 51.5194}
        cls.mint_quantities = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        cls.service_data = {"key": "seller_service", "value": "some_value"}
        cls.personality_data = {"piece": "genus", "value": "some_personality"}
        cls.classification = {"piece": "classification", "value": "some_classification"}
        cls.from_supply = 756
        cls.to_supply = 12
        cls.value = 87
        cls.token_type = 2
        config_overrides = {
            "models": {
                "strategy": {
                    "args": {
                        "location": cls.location,
                        "mint_quantities": cls.mint_quantities,
                        "service_data": cls.service_data,
                        "personality_data": cls.personality_data,
                        "classification": cls.classification,
                        "from_supply": cls.from_supply,
                        "to_supply": cls.to_supply,
                        "value": cls.value,
                        "token_type": cls.token_type,
                    }
                }
            },
        }

        super().setup(config_overrides=config_overrides)

        # behaviours
        cls.registration_behaviour = cast(
            ServiceRegistrationBehaviour,
            cls._skill.skill_context.behaviours.service_registration,
        )

        # dialogues
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.oef_search_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )

        # handlers
        cls.fipa_handler = cast(FipaHandler, cls._skill.skill_context.handlers.fipa)
        cls.oef_search_handler = cast(
            OefSearchHandler, cls._skill.skill_context.handlers.oef_search
        )
        cls.contract_api_handler = cast(
            ContractApiHandler, cls._skill.skill_context.handlers.contract_api
        )
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )

        # models
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)

        cls.logger = cls._skill.skill_context.logger

        # mocked objects
        cls.ledger_id = "some_ledger_id"
        cls.contract_id = "some_contract_id"
        cls.contract_address = "some_contract_address"
        cls.callable = "some_callable"
        cls.body_dict = {"some_key": "some_value"}
        cls.body_str = "some_body"
        cls.body_bytes = b"some_body"
        cls.kwargs = Kwargs(cls.body_dict)
        cls.address = "some_address"

        cls.mocked_terms = Terms(
            cls.ledger_id,
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.mocked_query = Query(
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
        cls.mocked_proposal = Description(
            {
                "contract_address": "some_contract_address",
                "token_id": "123456",
                "trade_nonce": "876438756348568",
                "from_supply": "543",
                "to_supply": "432",
                "value": "67",
            }
        )
        cls.mocked_registration_description = Description({"foo1": 1, "bar1": 2})

        cls.mocked_raw_tx = RawTransaction(cls.ledger_id, cls.body_dict)
        cls.mocked_raw_msg = RawMessage(cls.ledger_id, cls.body_bytes)
        cls.mocked_tx_digest = TransactionDigest(cls.ledger_id, cls.body_str)
        cls.mocked_signed_tx = SignedTransaction(cls.ledger_id, cls.body_dict)
        cls.mocked_tx_receipt = TransactionReceipt(
            cls.ledger_id,
            {"receipt_key": "receipt_value", "contractAddress": cls.contract_address},
            {"transaction_key": "transaction_value"},
        )

        cls.registration_message = OefSearchMessage(
            dialogue_reference=("", ""),
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=cls.mocked_registration_description,
        )
        cls.registration_message.sender = str(cls._skill.skill_context.skill_id)
        cls.registration_message.to = cls._skill.skill_context.search_service_address

        # list of messages
        cls.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": cls.mocked_query}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": cls.mocked_proposal}
            ),
        )
        cls.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                {
                    "ledger_id": cls.ledger_id,
                    "contract_id": cls.contract_id,
                    "contract_address": cls.contract_address,
                    "callable": cls.callable,
                    "kwargs": cls.kwargs,
                },
            ),
        )
        cls.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {"terms": cls.mocked_terms, "raw_transaction": cls.mocked_raw_tx},
            ),
        )
        cls.list_of_ledger_api_balance_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_BALANCE,
                {"ledger_id": cls.ledger_id, "address": "some_address"},
            ),
        )

        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                {"terms": cls.mocked_terms},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.RAW_TRANSACTION,
                {"raw_transaction": cls.mocked_raw_tx},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                {"signed_transaction": cls.mocked_signed_tx},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                {"transaction_digest": cls.mocked_tx_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {"transaction_digest": cls.mocked_tx_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                {"transaction_receipt": cls.mocked_tx_receipt},
            ),
        )
        cls.register_location_description = Description(
            {"location": Location(51.5194, 0.1270)},
            data_model=DataModel(
                "location_agent", [Attribute("location", Location, True)]
            ),
        )
        cls.list_of_messages_register_location = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_location_description},
                is_incoming=False,
            ),
        )

        cls.register_service_description = Description(
            {"key": "some_key", "value": "some_value"},
            data_model=DataModel(
                "set_service_key",
                [Attribute("key", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_service = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_service_description},
                is_incoming=False,
            ),
        )

        cls.register_genus_description = Description(
            {"piece": "genus", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_genus = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_genus_description},
                is_incoming=False,
            ),
        )

        cls.register_classification_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_classification = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_classification_description},
                is_incoming=False,
            ),
        )

        cls.register_invalid_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "some_different_name",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_invalid = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_invalid_description},
                is_incoming=False,
            ),
        )
