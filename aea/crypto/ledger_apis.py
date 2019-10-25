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

LEDGER_IDENTIFIERS

DEFAULT_FETCHAI_CONFIG = ("127.0.0.1", 8000)

class LedgerApis(object):
    """Store all the ledger apis we initialise."""

    def __init__(self, ledger_api_configs: Dict[str, Tuple[str, int]]):
        """
        Instantiate a wallet object.

        :param private_key_paths: the private key paths
        :param ledger_api_configs: the ledger api configs
        """
        apis = {}  # type: Dict[str, Any]
        for identifier, configs in ledger_api_configs.items():
            if identifier == FETCHAI:
            	api = LedgerApi(self._ledger_api_config[0], self._ledger_api_config[1])
            	apis[identifier] = api
            elif identifier == ETHEREUM:
                NotImplementedError
            else:
                ValueError("Unsupported identifier in private key paths.")
        self._apis = apis

    @property
    def apis(self):
        """Get the apis."""
        return self._apis

    @property
    def token_balance(self, identifier: str) -> float:
        """
        Get the token balance.

        :return: the token balance
        """
        assert identifier in LEDGER_IDENTIFIERS
        try:
            api = self.apis[identifier]
            token_balance = api.tokens.balance(self.address)
        except Exception:
            logger.warning("An error occurred while attempting to get the current balance.")
            token_balance = 0.0
        return token_balance

    def transfer(self, identifier: str, entity, destination_address: str, amount: float, tx_fee: float) -> bool:
        """
        Transfer from self to destination.

        :param destination_address: the address of the receive
        :param amount: the amount
        :param tx_fee: the tx fee

        :return: bool indicating success
        """
        try:
            api = self.apis[identifier]
            logger.info("Waiting for the validation of the transaction...")
            tx_digest = api.tokens.transfer(self._entity, destination_address, amount, tx_fee)
            api.sync(tx_digest)
            logger.info("Done!")
            success = True
        except Exception:
            logger.warning("An error occurred while attempting the transfer.")
            success = False
        return success

    def generate_counterparty_address(self, counterparty_pbk: str) -> str:
        """
        Generate the address from the public key.

        :param counterparty_pbk: the public key of the counterparty

        :return: the address
        """
        address = Address(Identity.from_hex(counterparty_pbk))
        return address

    @staticmethod
    def get_address_from_public_key(public_key: str) -> Address:
        """
        Get the address from the public key.

        :return: str
        """
        identity = Identity.from_hex(public_key)
        return Address(identity)
        
    def sign_transaction(self, message: bytes) -> bytes:
        """
        Sing a transaction to send it to the ledger.

        :param message:
        :return: Signed message in bytes
        """
        signature = self._entity.sign(message)
        return signature