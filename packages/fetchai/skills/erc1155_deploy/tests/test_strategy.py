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
"""This module contains the tests of the strategy class of the erc1155_deploy skill."""
# pylint: skip-file

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location
from aea.helpers.transaction.base import Terms

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.skills.erc1155_deploy.strategy import (
    SIMPLE_SERVICE_MODEL,
    Strategy,
)
from packages.fetchai.skills.erc1155_deploy.tests.intermediate_class import (
    ERC1155DeployTestCase,
)


class TestStrategy(ERC1155DeployTestCase):
    """Test Strategy of erc1155_deploy."""

    def test__init__(self):
        """Test the properties of Strategy class."""
        assert Strategy(
            location=self.location,
            mint_quantities=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            service_data=self.service_data,
            personality_data=self.personality_data,
            classification=self.classification,
            from_supply=self.from_supply,
            to_supply=self.to_supply,
            value=self.value,
            token_type=1,
            name="strategy",
            skill_context=self.skill.skill_context,
        )

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.ledger_id == self.skill.skill_context.default_ledger_id
        assert self.strategy.contract_id == str(ERC1155Contract.contract_id)
        assert self.strategy.mint_quantities == self.mint_quantities
        assert self.strategy.token_ids == self.strategy._token_ids

        self.strategy._token_ids = None
        with pytest.raises(ValueError, match="Token ids not set."):
            assert self.strategy.token_ids

        with pytest.raises(ValueError, match="Contract address not set!"):
            assert self.strategy.contract_address
        self.strategy.contract_address = self.contract_address
        with pytest.raises(AEAEnforceError, match="Contract address already set!"):
            self.strategy.contract_address = self.contract_address
        assert self.strategy.contract_address == self.contract_address

        assert self.strategy.is_contract_deployed is False
        self.strategy.is_contract_deployed = True
        assert self.strategy.is_contract_deployed is True
        with pytest.raises(AEAEnforceError, match="Only allowed to switch to true."):
            self.strategy.is_contract_deployed = False

        assert self.strategy.is_tokens_created is False
        self.strategy.is_tokens_created = True
        assert self.strategy.is_tokens_created is True
        with pytest.raises(AEAEnforceError, match="Only allowed to switch to true."):
            self.strategy.is_tokens_created = False

        assert self.strategy.is_tokens_minted is False
        self.strategy.is_tokens_minted = True
        assert self.strategy.is_tokens_minted is True
        with pytest.raises(AEAEnforceError, match="Only allowed to switch to true."):
            self.strategy.is_tokens_minted = False

        assert self.strategy.gas == self.strategy._gas

    def test_get_location_description(self):
        """Test the get_location_description method of the Strategy class."""
        description = self.strategy.get_location_description()

        assert type(description) == Description
        assert description.data_model is AGENT_LOCATION_MODEL
        assert description.values.get("location", "") == Location(
            latitude=self.location["latitude"], longitude=self.location["longitude"]
        )

    def test_get_register_service_description(self):
        """Test the get_register_service_description method of the Strategy class."""
        description = self.strategy.get_register_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_data["key"]
        assert description.values.get("value", "") == self.service_data["value"]

    def test_get_register_personality_description(self):
        """Test the get_register_personality_description method of the Strategy class."""
        description = self.strategy.get_register_personality_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == self.personality_data["piece"]
        assert description.values.get("value", "") == self.personality_data["value"]

    def test_get_register_classification_description(self):
        """Test the get_register_classification_description method of the Strategy class."""
        description = self.strategy.get_register_classification_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == self.classification["piece"]
        assert description.values.get("value", "") == self.classification["value"]

    def test_get_service_description(self):
        """Test the get_service_description method of the Strategy class."""
        description = self.strategy.get_service_description()

        assert type(description) == Description
        assert description.data_model is SIMPLE_SERVICE_MODEL
        assert (
            description.values.get("seller_service", "") == self.service_data["value"]
        )

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the Strategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_data["key"]

    def test_get_deploy_terms(self):
        """Test the get_deploy_terms of Strategy."""
        assert self.strategy.get_deploy_terms() == Terms(
            ledger_id=self.ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address=self.skill.skill_context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )

    def test_get_create_token_terms(self):
        """Test the get_create_token_terms of Parameters."""
        assert self.strategy.get_create_token_terms() == Terms(
            ledger_id=self.ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address=self.skill.skill_context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )

    def test_get_mint_token_terms(self):
        """Test the get_mint_token_terms of Strategy."""
        assert self.strategy.get_mint_token_terms() == Terms(
            ledger_id=self.ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address=self.skill.skill_context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )

    def test_get_proposal(self):
        """Test the get_proposal of Strategy."""
        # setup
        self.strategy._contract_address = self.contract_address
        first_id = 8768
        self.strategy._token_ids = [first_id, 234, 879643]

        # operation
        actual_proposal = self.strategy.get_proposal()

        # after
        assert all(
            keys in actual_proposal.values
            for keys in [
                "contract_address",
                "token_id",
                "trade_nonce",
                "from_supply",
                "to_supply",
            ]
        )
        assert (
            actual_proposal.values.get("contract_address", "") == self.contract_address
        )
        assert actual_proposal.values.get("token_id", "") == str(first_id)
        assert isinstance(actual_proposal.values.get("trade_nonce", ""), str)
        assert actual_proposal.values.get("from_supply", "") == str(self.from_supply)
        assert actual_proposal.values.get("to_supply", "") == str(self.to_supply)
        assert actual_proposal.values.get("value", "") == str(self.value)

    def test_get_single_swap_terms(self):
        """Test the get_single_swap_terms of Strategy."""
        assert self.strategy.get_single_swap_terms(
            self.mocked_proposal, "some_address"
        ) == Terms(
            ledger_id=self.ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address="some_address",
            amount_by_currency_id={
                str(self.mocked_proposal.values["token_id"]): int(
                    self.mocked_proposal.values["from_supply"]
                )
                - int(self.mocked_proposal.values["to_supply"])
            },
            quantities_by_good_id={},
            is_sender_payable_tx_fee=True,
            nonce=str(self.mocked_proposal.values["trade_nonce"]),
            fee_by_currency_id={},
        )
