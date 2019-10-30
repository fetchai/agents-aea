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
import time
from typing import Any, Dict, Optional, Tuple, cast

import web3
from fetchai.ledger.api import LedgerApi as FetchLedgerApi
# from fetchai.ledger.api.tx import TxStatus
from fetchai.ledger.crypto import Identity, Address
from web3 import Web3, HTTPProvider

from aea.crypto.base import Crypto
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI

DEFAULT_FETCHAI_CONFIG = ('alpha.fetch-ai.com', 80)
SUCCESSFUL_TERMINAL_STATES = ('Executed', 'Submitted')

logger = logging.getLogger(__name__)


class LedgerApis(object):
    """Store all the ledger apis we initialise."""

    def __init__(self, ledger_api_configs: Dict[str, Tuple[str, int]]):
        """
        Instantiate a wallet object.

        :param ledger_api_configs: the ledger api configs
        """
        apis = {}  # type: Dict[str, Any]
        for identifier, config in ledger_api_configs.items():
            if identifier == FETCHAI:
                api = FetchLedgerApi(config[0], config[1])
                apis[identifier] = api
            elif identifier == ETHEREUM:
                api = Web3(HTTPProvider(config[0]))
                apis[identifier] = api
            else:
                raise ValueError("Unsupported identifier in private key paths.")
        self._apis = apis

    @property
    def apis(self) -> Dict[str, Any]:
        """Get the apis."""
        return self._apis

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
            except Exception:
                logger.warning("An error occurred while attempting to get the current balance.")
                balance = 0
        elif identifier == ETHEREUM:
            try:
                balance = api.eth.getBalance(address)
            except Exception:
                logger.warning("An error occurred while attempting to get the current balance.")
                balance = 0
        else:
            balance = 0
        return balance

    def transfer(self, identifier: str, crypto_object: Crypto, destination_address: str, amount: int, tx_fee: int) -> Optional[str]:
        """
        Transfer from self to destination.

        :param identifier: the crypto code
        :param crypto_object: the crypto object that contains the fucntions for signing transactions.
        :param destination_address: the address of the receive
        :param amount: the amount
        :param tx_fee: the tx fee

        :return: tx digest if successful, otherwise None
        """
        assert identifier in self.apis.keys(), "Unsupported ledger identifier."
        api = self.apis[identifier]
        logger.info("Waiting for the validation of the transaction ...")
        if identifier == FETCHAI:
            try:
                tx_digest = api.tokens.transfer(crypto_object.entity, destination_address, amount, tx_fee)
                api.sync(tx_digest)
                logger.info("Transaction validated ...")
            except Exception:
                logger.warning("An error occurred while attempting the transfer.")
                tx_digest = None
        elif identifier == ETHEREUM:

            nonce = api.eth.getTransactionCount(api.toChecksumAddress(crypto_object.address))
            transaction = {
                'nonce': nonce,
                'chainId': 3,
                'to': destination_address,
                'value': amount,
                'gas': tx_fee + 200000,
                'gasPrice': api.toWei('50', 'gwei')
            }
            signed = api.eth.account.signTransaction(transaction, crypto_object.entity.privateKey)
            hex_value = api.eth.sendRawTransaction(signed.rawTransaction)
            print("TX Hash: ", hex_value.hex())
            print("connect_to https://ropsten.etherscan.io/tx/{}".format(hex_value.hex()))
            while True:
                try:
                    api.eth.getTransactionReceipt(hex_value)
                    logger.info("transaction validated - exiting")
                    tx_digest = hex_value.hex()
                    break
                except web3.exceptions.TransactionNotFound:
                    logger.info("transaction not found - sleeping for 3.0 seconds")
                    time.sleep(3.0)

            return tx_digest
        else:
            tx_digest = None
        return tx_digest

    def is_tx_settled(self, identifier: str, tx_digest: str, amount: int) -> bool:
        """
        Check whether the transaction is settled and correct.

        :param identifier: the identifier of the ledger
        :param tx_digest: the transaction digest
        :param amount: the amount
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
                if tx_status in SUCCESSFUL_TERMINAL_STATES:
                    # TODO: check the amount of the transaction is correct
                    is_successful = True
                logger.info("Transaction validated ...")
            except Exception:
                logger.warning("An error occurred while attempting to check the transaction.")
        elif identifier == ETHEREUM:
            try:
                logger.info("Checking the transaction ...")
                tx_status = api.eth.getTransactionReceipt(tx_digest)
                logger.info(tx_status)
                if tx_status is not None:
                    is_successful = True
                logger.info("Transaction validated ...")
            except Exception:
                logger.warning("An error occured while attempting to check the transaction!")

        return is_successful

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
