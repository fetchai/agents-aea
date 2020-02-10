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

"""Module wrapping all the public and private keys cryptography."""

import logging
import sys
from typing import Dict, Optional, Union, cast

from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.ethereum import ETHEREUM, EthereumApi
from aea.crypto.fetchai import FETCHAI, FetchAIApi
from aea.mail.base import Address

SUCCESSFUL_TERMINAL_STATES = ("Executed", "Submitted")
SUPPORTED_LEDGER_APIS = [ETHEREUM, FETCHAI]
SUPPORTED_CURRENCIES = {ETHEREUM: "ETH", FETCHAI: "FET"}

logger = logging.getLogger(__name__)

GAS_PRICE = "50"
GAS_ID = "gwei"
UNKNOWN = "UNKNOWN"
OK = "OK"
ERROR = "ERROR"


class LedgerApis(object):
    """Store all the ledger apis we initialise."""

    def __init__(
        self,
        ledger_api_configs: Dict[str, Dict[str, Union[str, int]]],
        default_ledger_id: str,
    ):
        """
        Instantiate a wallet object.

        :param ledger_api_configs: the ledger api configs.
        :param default_ledger_id: the default ledger id.
        """
        apis = {}  # type: Dict[str, LedgerApi]
        configs = {}  # type: Dict[str, Dict[str, Union[str, int]]]
        self._last_tx_statuses = {}  # type: Dict[str, str]
        for identifier, config in ledger_api_configs.items():
            self._last_tx_statuses[identifier] = UNKNOWN
            if identifier == FETCHAI:
                api = FetchAIApi(**config)  # type: LedgerApi
                apis[identifier] = api
                configs[identifier] = config
            elif identifier == ETHEREUM:
                api = EthereumApi(
                    cast(str, config["address"]), cast(str, config["gas_price"])
                )
                apis[identifier] = api
                configs[identifier] = config
            else:
                raise ValueError("Unsupported identifier in ledger apis.")

        self._apis = apis
        self._configs = configs
        self._default_ledger_id = default_ledger_id

    @property
    def configs(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Get the configs."""
        return self._configs

    @property
    def apis(self) -> Dict[str, LedgerApi]:
        """Get the apis."""
        return self._apis

    @property
    def has_fetchai(self) -> bool:
        """Check if it has the fetchai API."""
        return FETCHAI in self.apis.keys()

    @property
    def has_ethereum(self) -> bool:
        """Check if it has the ethereum API."""
        return ETHEREUM in self.apis.keys()

    @property
    def has_default_ledger(self) -> bool:
        """Check if it has the default ledger API."""
        return self.default_ledger_id in self.apis.keys()

    @property
    def last_tx_statuses(self) -> Dict[str, str]:
        """Get the statuses for the last transaction."""
        return self._last_tx_statuses

    @property
    def default_ledger_id(self) -> str:
        """Get the default ledger id."""
        return self._default_ledger_id

    def token_balance(self, identifier: str, address: str) -> int:
        """
        Get the token balance.

        :param identifier: the identifier of the ledger
        :param address: the address to check for
        :return: the token balance
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        api = self.apis[identifier]
        try:
            balance = api.get_balance(address)
            self._last_tx_statuses[identifier] = OK
        except Exception:
            logger.warning(
                "An error occurred while attempting to get the current balance."
            )
            self._last_tx_statuses[identifier] = ERROR
            # TODO raise exception instead of returning zero.
            balance = 0
        return balance

    def transfer(
        self,
        crypto_object: Crypto,
        destination_address: str,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        **kwargs
    ) -> Optional[str]:
        """
        Transfer from self to destination.

        :param tx_nonce: verifies the authenticity of the tx
        :param crypto_object: the crypto object that contains the fucntions for signing transactions.
        :param destination_address: the address of the receive
        :param amount: the amount
        :param tx_fee: the tx fee

        :return: tx digest if successful, otherwise None
        """
        assert (
            crypto_object.identifier in self.apis.keys()
        ), "Unsupported ledger identifier."
        api = self.apis[crypto_object.identifier]
        logger.info("Waiting for the validation of the transaction ...")
        try:
            tx_digest = api.send_transaction(
                crypto_object, destination_address, amount, tx_fee, tx_nonce, **kwargs,
            )
            logger.info("transaction validated. TX digest: {}".format(tx_digest))
            self._last_tx_statuses[crypto_object.identifier] = OK
        except Exception:
            logger.warning("An error occurred while attempting the transfer.")
            tx_digest = None
            self._last_tx_statuses[crypto_object.identifier] = ERROR
        return tx_digest

    def _is_tx_settled(self, identifier: str, tx_digest: str) -> bool:
        """
        Check whether the transaction is settled and correct.

        :param identifier: the identifier of the ledger
        :param tx_digest: the transaction digest
        :return: True if correctly settled, False otherwise
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        api = self.apis[identifier]
        try:
            is_successful = api.is_transaction_settled(tx_digest)
            self._last_tx_statuses[identifier] = OK
        except Exception:
            logger.warning(
                "An error occured while attempting to check the transaction!"
            )
            is_successful = False
            self._last_tx_statuses[identifier] = ERROR
        return is_successful

    def is_tx_valid(
        self,
        identifier: str,
        tx_digest: str,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """
        Check whether the transaction is valid

        :param identifier: Ledger identifier
        :param tx_digest:  the transaction digest
        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :return: True if is valid , False otherwise
        """
        assert identifier in self.apis.keys()
        is_settled = self._is_tx_settled(identifier=identifier, tx_digest=tx_digest)
        api = self.apis[identifier]
        try:
            tx_valid = api.validate_transaction(
                tx_digest, seller, client, tx_nonce, amount
            )
        except Exception:
            logger.warning(
                "An error occurred while attempting to validate the transaction."
            )
            tx_valid = False
        is_valid = is_settled and tx_valid
        return is_valid

    def generate_tx_nonce(
        self, identifier: str, seller: Address, client: Address
    ) -> str:
        """
        Generate a random str message.

        :param identifier: ledger identifier.
        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        assert identifier in self.apis.keys()
        api = self.apis[identifier]
        try:
            tx_nonce = api.generate_tx_nonce(seller=seller, client=client)
        except Exception:
            logger.warning(
                "An error occurred while attempting to generate the tx_nonce"
            )
            tx_nonce = ""
        return tx_nonce


def _try_to_instantiate_fetchai_ledger_api(**kwargs) -> None:
    """
    Try to instantiate the fetchai ledger api.

    :param kwargs: the keyword arguments
    """
    try:
        from fetchai.ledger.api import LedgerApi

        LedgerApi(**kwargs)
    except Exception as e:
        logger.error(
            "Cannot connect to fetchai ledger with provided config:\n{}".format(e)
        )
        sys.exit(1)


def _try_to_instantiate_ethereum_ledger_api(address: str) -> None:
    """
    Try to instantiate the ethereum ledger api.

    :param addr: the address
    """
    try:
        from web3 import Web3, HTTPProvider

        Web3(HTTPProvider(address))
    except Exception:
        logger.error("Cannot connect to ethereum ledger with provided config.")
        sys.exit(1)
