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
import time
from typing import Any, Dict, Optional, Union, cast

from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.ethereum import ETHEREUM, EthereumApi
from aea.crypto.fetchai import FETCHAI, FetchAIApi
from aea.mail.base import Address

SUCCESSFUL_TERMINAL_STATES = ("Executed", "Submitted")
SUPPORTED_LEDGER_APIS = [ETHEREUM, FETCHAI]
SUPPORTED_CURRENCIES = {ETHEREUM: "ETH", FETCHAI: "FET"}
IDENTIFIER_FOR_UNAVAILABLE_BALANCE = -1

logger = logging.getLogger(__name__)

MAX_CONNECTION_RETRY = 3
GAS_PRICE = "50"
GAS_ID = "gwei"
LEDGER_STATUS_UNKNOWN = "UNKNOWN"


class LedgerApis:
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
        for identifier, config in ledger_api_configs.items():
            retry = 0
            is_connected = False
            if identifier == FETCHAI:
                while retry < MAX_CONNECTION_RETRY:
                    try:
                        api = FetchAIApi(**config)  # type: LedgerApi
                        is_connected = True
                        break
                    except Exception:
                        retry += 1
                        logger.debug(
                            "Connection attempt {} to fetchai ledger with provided config failed.".format(
                                retry
                            )
                        )
                        time.sleep(0.5)
                if not is_connected:
                    logger.error(
                        "Cannot connect to fetchai ledger with provided config after {} attemps. Giving up!".format(
                            MAX_CONNECTION_RETRY
                        )
                    )
                    sys.exit(1)
            elif identifier == ETHEREUM:
                while retry < MAX_CONNECTION_RETRY:
                    try:
                        api = EthereumApi(
                            cast(str, config["address"]), cast(str, config["gas_price"])
                        )
                        is_connected = True
                        break
                    except Exception:
                        retry += 1
                        logger.debug(
                            "Connection attempt {} to ethereum ledger with provided config failed.".format(
                                retry
                            )
                        )
                        time.sleep(0.5)
                if not is_connected:
                    logger.error(
                        "Cannot connect to ethereum ledger with provided config after {} attemps. Giving up!".format(
                            MAX_CONNECTION_RETRY
                        )
                    )
                    sys.exit(1)
            else:
                raise ValueError("Unsupported identifier in ledger apis.")
            apis[identifier] = api
            configs[identifier] = config
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
    def fetchai_api(self) -> FetchAIApi:
        """Get the Fetchai API."""
        assert self.has_fetchai, "Fetchai API not instantiated!"
        return cast(FetchAIApi, self.apis[FETCHAI])

    @property
    def has_ethereum(self) -> bool:
        """Check if it has the ethereum API."""
        return ETHEREUM in self.apis.keys()

    @property
    def ethereum_api(self) -> EthereumApi:
        """Get the Ethereum API."""
        assert self.has_ethereum, "Ethereum API not instantiated!"
        return cast(EthereumApi, self.apis[ETHEREUM])

    @property
    def has_default_ledger(self) -> bool:
        """Check if it has the default ledger API."""
        return self.default_ledger_id in self.apis.keys()

    @property
    def last_tx_statuses(self) -> Dict[str, str]:
        """Get last tx statuses."""
        logger.warning("This API is deprecated, please no longer use this API.")
        return {identifier: LEDGER_STATUS_UNKNOWN for identifier in self.apis.keys()}

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
        balance = api.get_balance(address)
        if balance is None:
            _balance = IDENTIFIER_FOR_UNAVAILABLE_BALANCE
        else:
            _balance = balance
        return _balance

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
        tx_digest = api.transfer(
            crypto_object, destination_address, amount, tx_fee, tx_nonce, **kwargs,
        )
        return tx_digest

    def send_signed_transaction(self, identifier: str, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :return: the tx_digest, if present
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        api = self.apis[identifier]
        tx_digest = api.send_signed_transaction(tx_signed)
        return tx_digest

    def is_transaction_settled(self, identifier: str, tx_digest: str) -> bool:
        """
        Check whether the transaction is settled and correct.

        :param identifier: the identifier of the ledger
        :param tx_digest: the transaction digest
        :return: True if correctly settled, False otherwise
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        api = self.apis[identifier]
        is_settled = api.is_transaction_settled(tx_digest)
        return is_settled

    def is_tx_valid(
        self,
        identifier: str,
        tx_digest: str,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """Kept for backwards compatibility!"""
        logger.warning("This is a deprecated api, use 'is_transaction_valid' instead")
        return self.is_transaction_valid(
            identifier, tx_digest, seller, client, tx_nonce, amount
        )

    def is_transaction_valid(
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
        assert identifier in self.apis.keys(), "Not a registered ledger api identifier."
        api = self.apis[identifier]
        is_valid = api.is_transaction_valid(tx_digest, seller, client, tx_nonce, amount)
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
        assert identifier in self.apis.keys(), "Not a registered ledger api identifier."
        api = self.apis[identifier]
        tx_nonce = api.generate_tx_nonce(seller=seller, client=client)
        return tx_nonce
