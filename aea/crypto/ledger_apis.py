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
import sys
import time
from typing import Any, Dict, Optional, cast, List, Union

import web3
import web3.exceptions
from fetchai.ledger.api import LedgerApi as FetchLedgerApi
# from fetchai.ledger.api.tx import TxStatus
from web3 import Web3, HTTPProvider

from aea.crypto.base import Crypto
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI

DEFAULT_FETCHAI_CONFIG = ('alpha.fetch-ai.com', 80)
SUCCESSFUL_TERMINAL_STATES = ('Executed', 'Submitted')
SUPPORTED_LEDGER_APIS = [ETHEREUM, FETCHAI]

logger = logging.getLogger(__name__)

GAS_PRICE = '50'
GAS_ID = 'gwei'
UNKNOWN = "UNKNOWN"
OK = "OK"
ERROR = "ERROR"


class LedgerApis(object):
    """Store all the ledger apis we initialise."""

    def __init__(self, ledger_api_configs: Dict[str, List[Union[str, int]]]):
        """
        Instantiate a wallet object.

        :param ledger_api_configs: the ledger api configs
        """
        apis = {}  # type: Dict[str, Any]
        configs = {}  # type: Dict[str, List[Union[str, int]]]
        self._last_tx_statuses = {}  # type: Dict[str, str]
        for identifier, config in ledger_api_configs.items():
            self._last_tx_statuses[identifier] = UNKNOWN
            if identifier == FETCHAI:
                api = FetchLedgerApi(config[0], config[1])
                apis[identifier] = api
                configs[identifier] = config
            elif identifier == ETHEREUM:
                api = Web3(HTTPProvider(config[0]))
                apis[identifier] = api
                configs[identifier] = config
            else:
                raise ValueError("Unsupported identifier in ledger apis.")

        self._apis = apis
        self._configs = configs

    @property
    def configs(self) -> Dict[str, List[Union[str, int]]]:
        """Get the configs."""
        return self._configs

    @property
    def apis(self) -> Dict[str, Any]:
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
    def last_tx_statuses(self) -> Dict[str, str]:
        """Get the statuses for the last transaction."""
        return self._last_tx_statuses

    def token_balance(self, identifier: str, address: str) -> int:
        """
        Get the token balance.

        :param identifier: the identifier of the ledger
        :param address: the address to check for
        :return: the token balance
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        api = self.apis[identifier]
        if identifier == FETCHAI:
            try:
                balance = api.tokens.balance(address)
                self._last_tx_statuses[identifier] = OK
            except Exception:
                logger.warning("An error occurred while attempting to get the current balance.")
                balance = 0
                self._last_tx_statuses[identifier] = ERROR
        elif identifier == ETHEREUM:
            try:
                balance = api.eth.getBalance(address)
                self._last_tx_statuses[identifier] = OK
            except Exception:
                logger.warning("An error occurred while attempting to get the current balance.")
                balance = 0
                self._last_tx_statuses[identifier] = ERROR
        else:       # pragma: no cover
            raise Exception("Ledger id is not known")
        return balance

    def transfer(self, crypto_object: Crypto, destination_address: str, amount: int, tx_fee: int) -> Optional[str]:
        """
        Transfer from self to destination.

        :param crypto_object: the crypto object that contains the fucntions for signing transactions.
        :param destination_address: the address of the receive
        :param amount: the amount
        :param tx_fee: the tx fee

        :return: tx digest if successful, otherwise None
        """
        assert crypto_object.identifier in self.apis.keys(), "Unsupported ledger identifier."
        api = self.apis[crypto_object.identifier]
        logger.info("Waiting for the validation of the transaction ...")
        if crypto_object.identifier == FETCHAI:
            try:
                tx_digest = api.tokens.transfer(crypto_object.entity, destination_address, amount, tx_fee)
                api.sync(tx_digest)
                logger.info("Transaction validated ...")
                self._last_tx_statuses[crypto_object.identifier] = OK
            except Exception:
                logger.warning("An error occurred while attempting the transfer.")
                tx_digest = None
                self._last_tx_statuses[crypto_object.identifier] = ERROR
        elif crypto_object.identifier == ETHEREUM:
            try:
                nonce = api.eth.getTransactionCount(api.toChecksumAddress(crypto_object.address))
                # TODO : handle misconfiguration
                chain_id = self.configs.get(crypto_object.identifier)[1]  # type: ignore
                transaction = {
                    'nonce': nonce,
                    'chainId': chain_id,
                    'to': destination_address,
                    'value': amount,
                    'gas': tx_fee,
                    'gasPrice': api.toWei(GAS_PRICE, GAS_ID)
                }
                signed = api.eth.account.signTransaction(transaction, crypto_object.entity.privateKey)
                hex_value = api.eth.sendRawTransaction(signed.rawTransaction)
                logger.info("TX Hash: {}".format(str(hex_value.hex())))
                while True:
                    try:
                        api.eth.getTransactionReceipt(hex_value)
                        logger.info("transaction validated - exiting")
                        tx_digest = hex_value.hex()
                        self._last_tx_statuses[crypto_object.identifier] = OK
                        break
                    except web3.exceptions.TransactionNotFound:     # pragma: no cover
                        logger.info("transaction not found - sleeping for 3.0 seconds")
                        self._last_tx_statuses[crypto_object.identifier] = ERROR
                        time.sleep(3.0)
                return tx_digest
            except Exception:
                logger.warning("An error occurred while attempting the transfer.")
                tx_digest = None
                self._last_tx_statuses[crypto_object.identifier] = ERROR
        else:  # pragma: no cover
            raise Exception("Ledger id is not known")
        return tx_digest

    def is_tx_settled(self, identifier: str, tx_digest: str, amount: int) -> bool:
        """
        Check whether the transaction is settled and correct.

        :param identifier: the identifier of the ledger
        :param tx_digest: the transaction digest
        :return: True if correctly settled, False otherwise
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        is_successful = False
        api = self.apis[identifier]
        if identifier == FETCHAI:
            try:
                logger.info("Checking the transaction ...")
                # tx_status = cast(TxStatus, api.tx.status(tx_digest))
                tx_status = cast(str, api.tx.status(tx_digest))
                # if tx_status.successful:
                if tx_status in SUCCESSFUL_TERMINAL_STATES:
                    # tx_contents = cast(TxContents, api.tx.contents(tx_digest))
                    # tx_contents.transfers_to()
                    # TODO: check the amount of the transaction is correct
                    is_successful = True
                logger.info("Transaction validated ...")
                self._last_tx_statuses[identifier] = OK
            except Exception:
                logger.warning("An error occurred while attempting to check the transaction.")
                self._last_tx_statuses[identifier] = ERROR
        elif identifier == ETHEREUM:
            try:
                logger.info("Checking the transaction ...")
                tx_status = api.eth.getTransactionReceipt(tx_digest)
                if tx_status is not None:
                    is_successful = True
                logger.info("Transaction validated ...")
                self._last_tx_statuses[identifier] = OK
            except Exception:
                logger.warning("An error occured while attempting to check the transaction!")
                self._last_tx_statuses[identifier] = ERROR

        return is_successful


def _try_to_instantiate_fetchai_ledger_api(addr: str, port: int) -> None:
    """
    Tro to instantiate the fetchai ledger api.

    :param addr: the address
    :param port: the port
    """
    try:
        from fetchai.ledger.api import LedgerApi
        LedgerApi(addr, port)
    except Exception:
        logger.error("Cannot connect to fetchai ledger with provided config.")
        sys.exit(1)


def _try_to_instantiate_ethereum_ledger_api(addr: str, port: int) -> None:
    """
    Tro to instantiate the fetchai ledger api.

    :param addr: the address
    :param port: the port
    """
    try:
        from web3 import Web3, HTTPProvider
        Web3(HTTPProvider(addr))
    except Exception:
        logger.error("Cannot connect to ethereum ledger with provided config.")
        sys.exit(1)
