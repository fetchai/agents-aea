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
"""This module sets up test environment for erc1155_client skill."""
# pylint: skip-file

from pathlib import Path
from typing import cast

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Query,
)
from aea.helpers.transaction.base import RawMessage, RawTransaction, Terms
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.contract_api.custom_types import Kwargs
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_client.behaviours import SearchBehaviour
from packages.fetchai.skills.erc1155_client.dialogues import (
    ContractApiDialogues,
    DefaultDialogues,
    FipaDialogues,
    LedgerApiDialogues,
    OefSearchDialogues,
    SigningDialogues,
)
from packages.fetchai.skills.erc1155_client.handlers import (
    ContractApiHandler,
    FipaHandler,
    LedgerApiHandler,
    OefSearchHandler,
    SigningHandler,
)
from packages.fetchai.skills.erc1155_client.strategy import Strategy
from packages.open_aea.protocols.signing.message import SigningMessage


PACKAGE_DIR = Path(__file__).parent.parent


class ERC1155ClientTestCase(BaseSkillTestCase):
    """Sets the erc1155_client class up for testing."""

    path_to_skill = PACKAGE_DIR

    def setup(self):
        """Setup the test class."""
        self.location = {"longitude": 0.1270, "latitude": 51.5194}
        self.search_query = {
            "search_key": "seller_service",
            "search_value": "erc1155_contract",
            "constraint_type": "==",
        }
        self.search_radius = 5.0
        config_overrides = {
            "models": {
                "strategy": {
                    "args": {
                        "location": self.location,
                        "search_query": self.search_query,
                        "search_radius": self.search_radius,
                    }
                }
            },
        }

        super().setup(config_overrides=config_overrides)

        # behaviours
        self.search_behaviour = cast(
            SearchBehaviour, self._skill.skill_context.behaviours.search
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
        self.body = {"some_key": "some_value"}
        self.kwargs = Kwargs(self.body)
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
        self.mocked_raw_tx = (
            RawTransaction(self.ledger_id, {"some_key": "some_value"}),
        )
        self.mocked_raw_msg = RawMessage(self.ledger_id, b"some_body")

        # list of messages
        self.list_of_fipa_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": self.mocked_query}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": self.mocked_proposal}
            ),
        )
        self.list_of_oef_search_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES,
                {"query": self.mocked_query},
            ),
        )
        self.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_RAW_MESSAGE,
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
                SigningMessage.Performative.SIGN_MESSAGE,
                {"terms": self.mocked_terms, "raw_message": self.mocked_raw_msg},
            ),
        )
        self.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_BALANCE,
                {"ledger_id": self.ledger_id, "address": "some_address"},
            ),
        )
