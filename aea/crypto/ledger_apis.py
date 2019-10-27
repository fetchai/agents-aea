# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Module wrapping all the public and private keys cryptography."""

import logging
from typing import Any, Dict, Optional, Tuple

from fetchai.ledger.api import LedgerApi as FetchLedgerApi  # type: ignore
from fetchai.ledger.crypto import Entity, Identity, Address  # type: ignore

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI

DEFAULT_FETCHAI_CONFIG = ('alpha.fetch-ai.com', 80)

logger = logging.getLogger(__name__)


class LedgerApis(object):
    """Store all the ledger apis we initialise."""

    def __init__(self, ledger_api_configs: Dict[str, Tuple[str, int]]):
        """
        Instantiate a wallet object.

        :param private_key_paths: the private key paths
        :param ledger_api_configs: the ledger api configs
        """
        apis = {}  # type: Dict[str, Any]
        for identifier, config in ledger_api_configs.items():
            if identifier == FETCHAI:
                api = FetchLedgerApi(config[0], config[1])
                apis[identifier] = api
            elif identifier == ETHEREUM:
                raise NotImplementedError
            else:
                raise ValueError("Unsupported identifier in private key paths.")
        self._apis = apis

    @property
    def apis(self) -> Dict[str, Any]:
        """Get the apis."""
        return self._apis

    def token_balance(self, identifier: str, address: str) -> float:
        """
        Get the token balance.

        :param identifier: the identifier of the ledger
        :param address: the address to check for
        :return: the token balance
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        try:
            api = self.apis[identifier]
            balance = api.tokens.balance(address)
        except Exception:
            logger.warning("An error occurred while attempting to get the current balance.")
            balance = 0.0
        return balance

    def transfer(self, identifier: str, entity: Entity, destination_address: str, amount: float, tx_fee: float) -> Optional[str]:
        """
        Transfer from self to destination.

        :param destination_address: the address of the receive
        :param amount: the amount
        :param tx_fee: the tx fee

        :return: tx digest if successful, otherwise None
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        try:
            api = self.apis[identifier]
            logger.info("Waiting for the validation of the transaction ...")
            tx_digest = api.tokens.transfer(entity, destination_address, amount, tx_fee)
            api.sync(tx_digest)
            logger.info("Transaction validated ...")
        except Exception:
            logger.warning("An error occurred while attempting the transfer.")
            tx_digest = None
        return tx_digest

    @staticmethod
    def get_address_from_public_key(self, identifier: str, public_key: str) -> Address:
        """
        Get the address from the public key.

        :param identifier: the identifier
        :param public_key: the public key
        :return: the address
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        identity = Identity.from_hex(public_key)
        return Address(identity)
