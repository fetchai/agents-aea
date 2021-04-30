# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains the strategy class."""

import random  # nosec
from typing import Any, List

from aea.exceptions import enforce
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    SIMPLE_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location
from aea.helpers.transaction.base import Terms
from aea.skills.base import Model

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract


DEFAULT_IS_LEDGER_TX = True
DEFAULT_NFT = 1
DEFAULT_FT = 2
DEFAULT_TOKEN_TYPE = DEFAULT_NFT
DEFAULT_NB_TOKENS = 10
DEFAULT_MINT_QUANTITIES = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
DEFAULT_FROM_SUPPLY = 10
DEFAULT_TO_SUPPLY = 0
DEFAULT_VALUE = 0
DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_SERVICE_DATA = {"key": "seller_service", "value": "erc1155_contract"}
DEFAULT_PERSONALITY_DATA = {"piece": "genus", "value": "data"}
DEFAULT_CLASSIFICATION = {"piece": "classification", "value": "seller"}
DEFAULT_GAS = 5000000


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the strategy of the agent."""
        ledger_id = kwargs.pop("ledger_id", None)
        self._token_type = kwargs.pop("token_type", DEFAULT_TOKEN_TYPE)
        enforce(self._token_type in [1, 2], "Token type must be 1 (NFT) or 2 (FT)")
        self._nb_tokens = kwargs.pop("nb_tokens", DEFAULT_NB_TOKENS)
        self._token_ids = kwargs.pop("token_ids", None)
        self._mint_quantities = kwargs.pop("mint_quantities", DEFAULT_MINT_QUANTITIES)
        enforce(
            len(self._mint_quantities) == self._nb_tokens,
            "Number of tokens must match mint quantities array size.",
        )
        if self._token_type == 1:
            enforce(
                all(quantity == 1 for quantity in self._mint_quantities),
                "NFTs must have a quantity of 1",
            )
        self._contract_address = kwargs.pop("contract_address", None)
        enforce(
            (self._token_ids is None and self._contract_address is None)
            or (self._token_ids is not None and self._contract_address is not None),
            "Either provide contract address and token ids or provide neither.",
        )

        self.from_supply = kwargs.pop("from_supply", DEFAULT_FROM_SUPPLY)
        self.to_supply = kwargs.pop("to_supply", DEFAULT_TO_SUPPLY)
        self.value = kwargs.pop("value", DEFAULT_VALUE)

        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(
                latitude=location["latitude"], longitude=location["longitude"]
            )
        }
        self._set_personality_data = kwargs.pop(
            "personality_data", DEFAULT_PERSONALITY_DATA
        )
        enforce(
            len(self._set_personality_data) == 2
            and "piece" in self._set_personality_data
            and "value" in self._set_personality_data,
            "personality_data must contain keys `key` and `value`",
        )
        self._set_classification = kwargs.pop("classification", DEFAULT_CLASSIFICATION)
        enforce(
            len(self._set_classification) == 2
            and "piece" in self._set_classification
            and "value" in self._set_classification,
            "classification must contain keys `key` and `value`",
        )
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        enforce(
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data,
            "service_data must contain keys `key` and `value`",
        )
        self._remove_service_data = {"key": self._set_service_data["key"]}
        self._simple_service_data = {
            self._set_service_data["key"]: self._set_service_data["value"]
        }
        self._gas = kwargs.pop("gas", DEFAULT_GAS)

        super().__init__(**kwargs)
        self._ledger_id = (
            ledger_id if ledger_id is not None else self.context.default_ledger_id
        )
        self._contract_id = str(ERC1155Contract.contract_id)
        self.is_behaviour_active = True
        self._is_contract_deployed = self._contract_address is not None
        self._is_tokens_created = self._token_ids is not None
        self._is_tokens_minted = self._token_ids is not None
        if self._token_ids is None:
            self._token_ids = ERC1155Contract.generate_token_ids(
                token_type=self._token_type, nb_tokens=self._nb_tokens
            )

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def contract_id(self) -> str:
        """Get the contract id."""
        return self._contract_id

    @property
    def mint_quantities(self) -> List[int]:
        """Get the list of mint quantities."""
        return self._mint_quantities

    @property
    def token_ids(self) -> List[int]:
        """Get the token ids."""
        if self._token_ids is None:
            raise ValueError("Token ids not set.")
        return self._token_ids

    @property
    def contract_address(self) -> str:
        """Get the contract address."""
        if self._contract_address is None:
            raise ValueError("Contract address not set!")
        return self._contract_address

    @contract_address.setter
    def contract_address(self, contract_address: str) -> None:
        """Set the contract address."""
        enforce(self._contract_address is None, "Contract address already set!")
        self._contract_address = contract_address

    @property
    def is_contract_deployed(self) -> bool:
        """Get contract deploy status."""
        return self._is_contract_deployed

    @is_contract_deployed.setter
    def is_contract_deployed(self, is_contract_deployed: bool) -> None:
        """Set contract deploy status."""
        enforce(
            not self._is_contract_deployed and is_contract_deployed,
            "Only allowed to switch to true.",
        )
        self._is_contract_deployed = is_contract_deployed

    @property
    def is_tokens_created(self) -> bool:
        """Get token created status."""
        return self._is_tokens_created

    @is_tokens_created.setter
    def is_tokens_created(self, is_tokens_created: bool) -> None:
        """Set token created status."""
        enforce(
            not self._is_tokens_created and is_tokens_created,
            "Only allowed to switch to true.",
        )
        self._is_tokens_created = is_tokens_created

    @property
    def is_tokens_minted(self) -> bool:
        """Get token minted status."""
        return self._is_tokens_minted

    @is_tokens_minted.setter
    def is_tokens_minted(self, is_tokens_minted: bool) -> None:
        """Set token minted status."""
        enforce(
            not self._is_tokens_minted and is_tokens_minted,
            "Only allowed to switch to true.",
        )
        self._is_tokens_minted = is_tokens_minted

    @property
    def gas(self) -> int:
        """Get gas."""
        return self._gas

    def get_location_description(self) -> Description:
        """
        Get the location description.

        :return: a description of the agent's location
        """
        description = Description(
            self._agent_location, data_model=AGENT_LOCATION_MODEL,
        )
        return description

    def get_register_service_description(self) -> Description:
        """
        Get the register service description.

        :return: a description of the offered services
        """
        description = Description(
            self._set_service_data, data_model=AGENT_SET_SERVICE_MODEL,
        )
        return description

    def get_register_personality_description(self) -> Description:
        """
        Get the register personality description.

        :return: a description of the personality
        """
        description = Description(
            self._set_personality_data, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_register_classification_description(self) -> Description:
        """
        Get the register classification description.

        :return: a description of the classification
        """
        description = Description(
            self._set_classification, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_service_description(self) -> Description:
        """
        Get the simple service description.

        :return: a description of the offered services
        """
        description = Description(
            self._simple_service_data, data_model=SIMPLE_SERVICE_MODEL,
        )
        return description

    def get_unregister_service_description(self) -> Description:
        """
        Get the unregister service description.

        :return: a description of the to be removed service
        """
        description = Description(
            self._remove_service_data, data_model=AGENT_REMOVE_SERVICE_MODEL,
        )
        return description

    def get_deploy_terms(self) -> Terms:
        """
        Get deploy terms of deployment.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms

    def get_create_token_terms(self) -> Terms:
        """
        Get create token terms of deployment.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms

    def get_mint_token_terms(self) -> Terms:
        """
        Get mint token terms of deployment.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms

    def get_proposal(self) -> Description:
        """Get the proposal."""
        trade_nonce = random.randrange(  # nosec
            0, 10000000
        )  # quickfix, to avoid contract call
        token_id = self.token_ids[0]
        proposal = Description(
            {
                "contract_address": self.contract_address,
                "token_id": str(token_id),
                "trade_nonce": str(trade_nonce),
                "from_supply": str(self.from_supply),
                "to_supply": str(self.to_supply),
                "value": str(self.value),
            }
        )
        return proposal

    def get_single_swap_terms(
        self, proposal: Description, counterparty_address: str
    ) -> Terms:
        """Get the proposal."""
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=counterparty_address,
            amount_by_currency_id={
                str(proposal.values["token_id"]): int(proposal.values["from_supply"])
                - int(proposal.values["to_supply"])
            },
            quantities_by_good_id={},
            is_sender_payable_tx_fee=True,
            nonce=str(proposal.values["trade_nonce"]),
            fee_by_currency_id={},
        )
        return terms
