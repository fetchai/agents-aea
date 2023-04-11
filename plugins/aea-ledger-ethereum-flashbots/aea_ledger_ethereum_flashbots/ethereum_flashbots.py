# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

# pylint: disable=no-member

"""Python package extending the default open-aea ethereum ledger plugin to add support for flashbots."""

import logging
from typing import Any, List, Optional, Union, cast
from uuid import uuid4

from aea_ledger_ethereum import EthereumApi, EthereumCrypto
from eth_account import Account
from flashbots import Flashbots, flashbot
from flashbots.types import FlashbotsBundleRawTx, FlashbotsBundleTx
from hexbytes import HexBytes
from web3.exceptions import TransactionNotFound

from aea.common import JSONLike
from aea.helpers.base import try_decorator


_default_logger = logging.getLogger("aea.ledger_apis.ethereum_flashbots")

_ETHEREUM_FLASHBOTS = "ethereum_flashbots"

_TARGET_BLOCKS = "target_blocks"

_DEFAULT_TARGET_BLOCKS = 25

_RAISE_ON_FAILED_SIMULATION = "raise_on_failed_simulation"


class EthereumFlashbotApi(EthereumApi):
    """Class to interact with the Ethereum Web3 APIs."""

    identifier = _ETHEREUM_FLASHBOTS

    def __init__(self, **kwargs: Any):
        """
        Initialize the Ethereum API.

        :param kwargs: the keyword arguments.
        """
        super().__init__(**kwargs)
        authentication_private_key = kwargs.pop("authentication_private_key", None)
        authentication_account = (
            Account.create()  # pylint: disable=no-value-for-parameter
            if authentication_private_key is None
            else Account.from_key(  # pylint: disable=no-value-for-parameter
                private_key=authentication_private_key
            )
        )
        flashbot_relayer_uri = kwargs.pop("flashbot_relayer_uri", None)

        # if flashbot_relayer_uri is None, the default URI is used
        flashbot(self.api, authentication_account, flashbot_relayer_uri)

    @property
    def flashbots(self) -> Flashbots:
        """Get the flashbots Web3 module."""
        flashbots_module = getattr(self.api, "flashbots", None)
        if flashbots_module is None:  # pragma: nocover
            raise ValueError("Flashbots have not been registered as a Web3 module.")
        return cast(Flashbots, flashbots_module)

    @staticmethod
    def bundle_transactions(
        signed_transactions: List[JSONLike],
    ) -> List[FlashbotsBundleRawTx]:
        """Bundle transactions."""
        return [
            FlashbotsBundleRawTx(
                signed_transaction=HexBytes(signed_transaction.get("raw_transaction"))
            )
            for signed_transaction in signed_transactions
        ]

    def simulate(
        self,
        bundle: List[Union[FlashbotsBundleTx, FlashbotsBundleRawTx]],
        target_block: Optional[int],
    ) -> bool:
        """
        Simulate a bundle.

        1. Simulate the bundle in a try catch block.
        2. Return True if simulation went through, or False if something went wrong.

        :param bundle: the bundle to simulate.
        :param target_block: the target block for the transaction, the current block if not provided.
        :return: True if the simulation went through, False otherwise.
        """
        _default_logger.debug(f"Simulating bundle: {bundle}")
        try:
            self.flashbots.simulate(bundle, target_block)
            _default_logger.debug(f"Simulation successful for bundle {bundle}.")
            return True
        except Exception as e:  # pylint: disable=broad-except
            _default_logger.warning(f"Simulation failed for bundle {bundle}: {e}")
        return False

    def send_bundle(
        self,
        bundle: List[Union[FlashbotsBundleTx, FlashbotsBundleRawTx]],
        target_blocks: List[int],
        raise_on_failed_simulation: bool = False,
    ) -> Optional[List[str]]:
        """
        Send a bundle.

        1. Simulate the bundle.
        2. Send the bundle in a try catch block.
        3. Wait for the response. If successful, go to step 4.
         If current block number is less than the maximum target block number, go to step 1.
        4. Return the transaction digests if the transactions went through, or None if something went wrong.

        :param bundle: the signed transactions to bundle together and send.
        :param target_blocks: the target blocks for the transactions.
        :param raise_on_failed_simulation: whether to raise an exception if the simulation fails.
        :return: the transaction digest if the transaction went through, None otherwise.
        """
        for target_block in target_blocks:
            if not self.simulate(bundle, target_block):
                msg = f"Simulation failed for bundle {bundle} targeting block {target_block}."
                if raise_on_failed_simulation:
                    raise ValueError(msg)
                _default_logger.warning(msg)
                continue

            replacement_uuid = str(uuid4())
            _default_logger.debug(
                f"Sending bundle {bundle} with replacement_uuid {replacement_uuid} targeting block {target_block}"
            )
            response = self.flashbots.send_bundle(
                bundle, target_block, opts={"replacementUuid": replacement_uuid}
            )
            _default_logger.debug(
                f"Response from bundle with replacement uuid {replacement_uuid}: {response}"
            )
            response.wait()
            try:
                receipts = response.receipts()
                tx_hashes = [tx["hash"].hex() for tx in response.bundle]
                _default_logger.debug(
                    f"Bundle with replacement uuid {replacement_uuid} was mined in block {receipts[0]['blockNumber']}"
                    f"Tx hashes: {tx_hashes}"
                )
                return tx_hashes
            except TransactionNotFound:
                # get & log the bundle stats in case it was not included in the block
                stats = self.flashbots.get_bundle_stats_v2(
                    self.api.toHex(response.bundle_hash()), target_block
                )
                _default_logger.info(
                    f"Bundle with replacement uuid {replacement_uuid} not found in block {target_block}. "
                    f"bundle stats: {stats}"
                )
                # essentially a no-op but it shows that the function works
                cancel_res = self.flashbots.cancel_bundles(replacement_uuid)
                _default_logger.debug(
                    f"Response from canceling bundle with replacement uuid {replacement_uuid}: {cancel_res}"
                )
        return None

    def _get_next_blocks(self, num_blocks: int = _DEFAULT_TARGET_BLOCKS) -> List[int]:
        """
        Get the next blocks.

        :param num_blocks: the number of blocks to get.
        :return: the next blocks.
        """
        current_block = self.api.eth.blockNumber
        return list(range(current_block, current_block + num_blocks))

    @try_decorator("Unable to send transactions: {}", logger_method="warning")
    def _try_send_signed_transactions(
        self, signed_transactions: List[JSONLike], **_kwargs: Any
    ) -> Optional[List[str]]:
        """
        Try sending a bundle of transactions.

        :param signed_transactions: the raw signed transactions to bundle together and send.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
            `target_blocks`: the target blocks for the transactions.
        :return: the transaction digest if the transactions went through, None otherwise.
        """
        bundle = self.bundle_transactions(signed_transactions)
        target_blocks = _kwargs.get(_TARGET_BLOCKS, self._get_next_blocks())
        raise_on_failed_simulation = _kwargs.get(_RAISE_ON_FAILED_SIMULATION, False)
        tx_hashes = self.send_bundle(bundle, target_blocks, raise_on_failed_simulation)
        return tx_hashes

    def send_signed_transactions(
        self,
        signed_transactions: List[JSONLike],
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[List[str]]:
        """
        Simulate and send a bundle of transactions.

        :param signed_transactions: the raw signed transactions to bundle together and send.
        :param raise_on_try: whether to raise an exception if the transaction is not successful.
        :param kwargs: the keyword arguments.
        :return: the transaction digest if the transactions went through, None otherwise.
        """
        tx_hashes = self._try_send_signed_transactions(
            signed_transactions,
            **kwargs,
            raise_on_try=raise_on_try,
        )
        return tx_hashes


class EthereumFlashbotCrypto(EthereumCrypto):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _ETHEREUM_FLASHBOTS
