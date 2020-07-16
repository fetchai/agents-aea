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
from typing import Any, Dict, List, Optional

from aea.configurations.constants import DEFAULT_LEDGER
from aea.helpers.search.generic import GenericDataModel
from aea.helpers.search.models import Description
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
DEFAULT_DATA_MODEL_NAME = "erc1155_deploy"
DEFAULT_DATA_MODEL = {
    "attribute_one": {
        "name": "has_erc1155_contract",
        "type": "bool",
        "is_required": "True",
    },
}  # type: Optional[Dict[str, Any]]
DEFAULT_SERVICE_DATA = {"has_erc1155_contract": True}
DEFAULT_LEDGER_ID = DEFAULT_LEDGER


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """Initialize the strategy of the agent."""
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._token_type = kwargs.pop("token_type", DEFAULT_TOKEN_TYPE)
        assert self._token_type in [1, 2], "Token type must be 1 (NFT) or 2 (FT)"
        self._nb_tokens = kwargs.pop("nb_tokens", DEFAULT_NB_TOKENS)
        self._token_ids = kwargs.pop("token_ids", None)
        self._mint_quantities = kwargs.pop("mint_quantities", DEFAULT_MINT_QUANTITIES)
        assert (
            len(self._mint_quantities) == self._nb_tokens
        ), "Number of tokens must match mint quantities array size."
        if self._token_type == 1:
            assert all(
                quantity == 1 for quantity in self._mint_quantities
            ), "NFTs must have a quantity of 1"
        self._contract_address = kwargs.pop("contract_address", None)
        assert (self._token_ids is None and self._contract_address is None) or (
            self._token_ids is not None and self._contract_address is not None
        ), "Either provide contract address and token ids or provide neither."

        self.from_supply = kwargs.pop("from_supply", DEFAULT_FROM_SUPPLY)
        self.to_supply = kwargs.pop("to_supply", DEFAULT_TO_SUPPLY)
        self.value = kwargs.pop("value", DEFAULT_VALUE)

        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)

        super().__init__(**kwargs)

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
    def mint_quantities(self) -> List[int]:
        """Get the list of mint quantities."""
        return self._mint_quantities

    @property
    def token_ids(self) -> List[int]:
        """Get the token ids."""
        assert self._token_ids is not None, "Token ids not set."
        return self._token_ids

    @property
    def contract_address(self) -> str:
        """Get the contract address."""
        assert self._contract_address is not None, "Contract address not set!"
        return self._contract_address

    @contract_address.setter
    def contract_address(self, contract_address: str) -> None:
        """Set the contract address."""
        assert self._contract_address is None, "Contract address already set!"
        self._contract_address = contract_address

    @property
    def is_contract_deployed(self) -> bool:
        """Get contract deploy status."""
        return self._is_contract_deployed

    @is_contract_deployed.setter
    def is_contract_deployed(self, is_contract_deployed: bool) -> None:
        """Set contract deploy status."""
        assert (
            not self._is_contract_deployed and is_contract_deployed
        ), "Only allowed to switch to true."
        self._is_contract_deployed = is_contract_deployed

    @property
    def is_tokens_created(self) -> bool:
        """Get token created status."""
        return self._is_tokens_created

    @is_tokens_created.setter
    def is_tokens_created(self, is_tokens_created: bool) -> None:
        """Set token created status."""
        assert (
            not self._is_tokens_created and is_tokens_created
        ), "Only allowed to switch to true."
        self._is_tokens_created = is_tokens_created

    @property
    def is_tokens_minted(self) -> bool:
        """Get token minted status."""
        return self._is_tokens_minted

    @is_tokens_minted.setter
    def is_tokens_minted(self, is_tokens_minted: bool) -> None:
        """Set token minted status."""
        assert (
            not self._is_tokens_minted and is_tokens_minted
        ), "Only allowed to switch to true."
        self._is_tokens_minted = is_tokens_minted

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        description = Description(
            self._service_data,
            data_model=GenericDataModel(self._data_model_name, self._data_model),
        )
        return description

    def get_deploy_terms(self) -> Terms:
        """
        Get deploy terms of deployment.

        :return: terms
        """
        terms = Terms(
            self.ledger_id,
            self.context.agent_address,
            self.context.agent_address,
            {},
            {},
            True,
            "",
            {},
        )
        return terms

    def get_create_token_terms(self) -> Terms:
        """
        Get create token terms of deployment.

        :return: terms
        """
        terms = Terms(
            self.ledger_id,
            self.context.agent_address,
            self.context.agent_address,
            {},
            {},
            True,
            "",
            {},
        )
        return terms

    def get_mint_token_terms(self) -> Terms:
        """
        Get mint token terms of deployment.

        :return: terms
        """
        terms = Terms(
            self.ledger_id,
            self.context.agent_address,
            self.context.agent_address,
            {},
            {},
            True,
            "",
            {},
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
        self, proposal: Description, counterparty_address
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
