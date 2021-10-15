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

"""This package contains a class representing the game parameters."""
from typing import Any

from aea_ledger_ethereum import EthereumApi
from aea_ledger_fetchai import FetchAIApi

from aea.helpers.transaction.base import Terms

from packages.fetchai.skills.tac_control.parameters import Parameters as BaseParameters


class Parameters(BaseParameters):
    """This class contains the parameters of the game."""

    def __init__(self, **kwargs: Any) -> None:
        """Instantiate the parameter class."""
        super().__init__(**kwargs)
        self.nb_completed_minting = 0

    def get_deploy_terms(self, is_init_transaction: bool = False) -> Terms:
        """
        Get deploy terms of deployment.

        :param is_init_transaction: whether this is for contract initialisation stage (for fetch ledger) or not.
        :return: terms
        """
        if self.ledger_id == EthereumApi.identifier:
            label = "deploy"
        elif self.ledger_id == FetchAIApi.identifier:
            label = "store"
            if is_init_transaction:
                label = "init"
        else:
            raise ValueError(
                f"Unidentified ledger id: {self.ledger_id}"
            )  # pragma: nocover

        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
            label=label,
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
