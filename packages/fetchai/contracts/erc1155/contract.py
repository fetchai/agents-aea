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

"""This module contains the scaffold contract definition."""
import json
import logging
import os
import random
import sys
import time
from operator import add
from pathlib import Path
from typing import Any, Dict, List

from vyper.utils import keccak256

import web3.exceptions
from web3 import Web3, eth

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.mail.base import Address

CHAIN_ID = 3
PROVIDER = "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe"
PRIVATE_KEY_1 = "6F611408F7EF304947621C51A4B7D84A13A2B9786E9F984DA790A096E8260C64"
PRIVATE_KEY_2 = "44AE85D1046EB947AC5776881D0CC487036F88C3B1CDC1CB18E1265204B40E85"
PRIVATE_KEY_3 = "80080D7FF9A46AEF5CC9468252163EEEDF512BB2BE7D567C7B23EB464AB25B92"
NFT = 1
FT = 2

logger = logging.getLogger(__name__)


class ERC1155Contract(Contract):
    """The ERC1155 contract class."""

    contract_id = PublicId("fetchai", "erc1155", "0.1.0")

    def __init__(self, **kwargs):
        """
        Initialize.

        :param performative: the type of message.
        """
        super().__init__(**kwargs)
        self.w3 = Web3(Web3.HTTPProvider(PROVIDER))
        self.address = None
        self.deployed = False
        self.abi = None
        self.bytecode = None
        self.instance = None
        batch_token_ids = []
        for j in range(10):
            batch_token_ids.append(Helpers().generate_id(FT, j))
        self.item_ids = batch_token_ids
        self._account = eth.Account.from_key(PRIVATE_KEY_1)

    def load_from_json(self):
        """Load ABI and BYTECODE from json file."""
        path = Path(
            os.getcwd(),
            "vendor",
            "fetchai",
            "contracts",
            "erc1155",
            "build",
            "erc1155.json",
        )
        with open(path, "r") as f_contract:
            contract_interface = json.load(f_contract)

        self.abi = contract_interface["abi"]
        self.bytecode = contract_interface["bytecode"]
        self.instance = self.w3.eth.contract(abi=self.abi, bytecode=self.bytecode)

    #  This should go to the Decision Maker.
    def _sign_transaction(self, tx):
        tx_signed = self.w3.eth.account.signTransaction(
            transaction_dict=tx, private_key=self._account.key
        )
        return tx_signed

    def deploy_contract(self):
        #  Request to deploy the contract from the decision maker and then ask ledger_apis ?
        tx = self._get_deploy_tx(deployer_address=self._account.address)
        tx_signed = self._sign_transaction(tx=tx)
        self.send_tx(tx_signed=tx_signed, tx_type="contract_deployment")
        logger.info("We just deployed the contract!")

    def _get_deploy_tx(self, deployer_address: Address) -> Dict[str, Any]:
        """
        Get the deployment transaction.

        :params: deployer_address: The address that will deploy the contract.

        :returns tx: The Transaction dictionary.
        """
        # create the transaction dict
        tx_data = self.instance.constructor().__dict__.get("data_in_transaction")
        tx = {
            "from": deployer_address,  # Only 'from' address, don't insert 'to' address
            "value": 0,  # Add how many ethers you'll transfer during the deploy
            "gas": 0,  # Trying to make it dynamic ..
            "gasPrice": self.w3.toWei("50", "gwei"),  # Get Gas Price
            "nonce": self.w3.eth.getTransactionCount(deployer_address),  # Get Nonce
            "data": tx_data,  # Here is the data sent through the network
        }

        # estimate the gas and update the transaction dict
        gas_estimate = self.w3.eth.estimateGas(transaction=tx)
        logger.info("gas estimate deploy: {}".format(gas_estimate))
        tx["gas"] = gas_estimate
        return tx

    def create_mint_batch(self, address: Address, mint_quantities: List[int]) -> None:
        """
        Create an mint a batch of items.

        :params address: The address that will receive the items
        :params mint_quantities: A list[10] of ints. The index represents the id in the item_ids list.
        """
        # create the items
        tx = self._get_create_batch_tx(deployer_address=self.address)
        tx_signed = self._sign_transaction(tx=tx)
        self.send_tx(tx_signed=tx_signed, tx_type="create_batch")

        assert len(mint_quantities) == len(self.item_ids)

        tx = self._get_mint_batch_tx(
            deployer_address=self.address,
            recipient_address=address,
            batch_mint_quantities=mint_quantities,
        )
        tx_signed = self._sign_transaction(tx=tx)
        self.send_tx(tx_signed=tx_signed, tx_type="mint_batch_agent_1")

        # assert balances match
        actual_balances = self.instance.functions.balanceOfBatch(
            [address] * 10, self.item_ids
        ).call()
        assert actual_balances == mint_quantities

    def _get_create_batch_tx(self, deployer_address):
        """Create a batch of items."""
        # create the items
        nonce = self.w3.eth.getTransactionCount(deployer_address)
        tx = self.instance.functions.createBatch(
            deployer_address, self.item_ids
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 300000,
                "gasPrice": self.w3.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        # gas_estimate = self.w3.eth.estimateGas(transaction=tx)
        # logger.info("gas estimate create_batch: {}".format(gas_estimate))
        return tx

    def _get_trade_tx(self, terms, signature):
        """
        Create a trade tx.

        :params terms: The class (can be Dict[str, Any]) that contains the details for the transaction.
        :params signature: The signed terms from the counterparty.
        """
        data = b"hello"
        nonce = self.w3.eth.getTransactionCount(terms.from_address)
        tx = self.instance.functions.trade(
            terms.from_address,
            terms.to_address,
            terms.item_id,
            terms.from_supply,
            terms.to_supply,
            terms.value_eth_wei,
            terms.trade_nonce,
            signature,
            data,
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 2818111,
                "from": terms.from_address,
                "value": terms.value_eth_wei,
                "gasPrice": self.w3.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        # gas_estimate = self.w3.eth.estimateGas(transaction=tx)
        # logger.info("gas estimate trade: {}".format(gas_estimate))
        return tx

    def _get_trade_batch_tx(self, terms, signature):
        """
        Create a batch trade tx.

        :params terms: The class (can be Dict[str, Any]) that contains the details for the transaction.
        :params signature: The signed terms from the counterparty.
        """
        data = b"hello"
        nonce = self.w3.eth.getTransactionCount(terms.from_address)
        tx = self.instance.functions.tradeBatch(
            terms.from_address,
            terms.to_address,
            terms.item_ids,
            terms.from_supplies,
            terms.to_supplies,
            terms.value_eth_wei,
            terms.trade_nonce,
            signature,
            data,
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 2818111,
                "from": terms.from_address,
                "value": terms.value_eth_wei,
                "gasPrice": self.w3.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        # gas_estimate = self.w3.eth.estimateGas(transaction=tx)
        # logger.info("gas estimate trade_batch: {}".format(gas_estimate))
        return tx

    def _get_mint_batch_tx(
        self, deployer_address, recipient_address, batch_mint_quantities
    ):
        """Mint a batch of items."""
        # mint batch
        nonce = self.w3.eth.getTransactionCount(deployer_address)
        tx = self.instance.functions.mintBatch(
            recipient_address, self.item_ids, batch_mint_quantities
        ).buildTransaction(
            {
                "chainId": CHAIN_ID,
                "gas": 300000,
                "gasPrice": self.w3.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        # gas_estimate = self.w3.eth.estimateGas(transaction=tx)
        # logger.info("gas estimate mint_batch: {}".format(gas_estimate))
        return tx

    def atomic_swap_single(self, contract, terms, signature):
        """Make a trustless trade between to agents for a single token."""
        assert self.address == terms.from_address, "Wrong from address"
        before_token_balance = contract.instance.functions.balanceOf(
            terms.from_address, terms.item_id
        ).call()
        before_eth_balance = self.w3.eth.getBalance(terms.from_address)

        tx = contract.get_trade_tx(terms=terms, signature=signature)
        tx_signed = self._sign_transaction(tx=tx)
        contract.send_tx(tx_signed=tx_signed, tx_type="single_trade")

        after_token_balance = contract.instance.functions.balanceOf(
            terms.from_address, terms.item_id
        ).call()
        after_eth_balance = self.w3.eth.getBalance(terms.from_address)
        assert (
            before_token_balance - terms.from_supply + terms.to_supply
            == after_token_balance
        ), "Token balances don't match"
        assert (
            before_eth_balance - terms.value_eth_wei > after_eth_balance
        ), "Eth balances don't match"  # note, gas fee also is paid by this account

    def atomic_swap_batch(self, contract, terms, signature):
        """Make a trust-less trade for a batch of items between 2 agents."""
        assert self.address == terms.from_address, "Wrong 'from' address"
        before_trade_balance_agent1 = contract.instance.functions.balanceOfBatch(
            [self.address] * 10, terms.item_ids
        ).call()
        before_trade_balance_agent2 = contract.instance.functions.balanceOfBatch(
            [terms.to_address] * 10, terms.item_ids
        ).call()

        tx = contract.get_trade_batch_tx(terms=terms, signature=signature)
        tx_signed = self._sign_transaction(tx=tx)
        contract.send_tx(tx_signed=tx_signed, tx_type="batch_trade")

        after_trade_balance_agent1 = contract.instance.functions.balanceOfBatch(
            [self.address] * 10, terms.item_ids
        ).call()
        after_trade_balance_agent2 = contract.instance.functions.balanceOfBatch(
            [terms.to_address] * 10, terms.item_ids
        ).call()

        assert list(map(add, after_trade_balance_agent1, terms.from_supplies)) == list(
            map(add, before_trade_balance_agent1, terms.to_supplies)
        ), "Balances don't match"
        assert list(map(add, after_trade_balance_agent2, terms.to_supplies)) == list(
            map(add, before_trade_balance_agent2, terms.from_supplies)
        ), "Balances don't match"

    def send_tx(self, tx_signed, tx_type):
        """Send a signed transaction and wait for confirmation."""
        # send the transaction to the ropsten test network
        tx_hash = self.w3.eth.sendRawTransaction(tx_signed.rawTransaction)

        # check for the transaction to go through
        not_found = True
        logger.info("sending {} transaction".format(tx_type))
        while not_found:
            try:
                tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
                if not tx_receipt.get("status") == 1:
                    logger.info("transaction {} was un-successful".format(tx_type))
                    logger.info("tx_receipt: {}".format(tx_receipt))
                    sys.exit()
                else:
                    logger.info("{} transaction validated!".format(tx_type))
                    # processed_receipt = self.instance.events.TransferBatch().processReceipt(tx_receipt)
                    # logger.debug(msg=processed_receipt)
                not_found = False
            except web3.exceptions.TransactionNotFound:
                logger.info(
                    "{} transaction not found - sleeping for 3.0 seconds!".format(
                        tx_type
                    )
                )
                time.sleep(3.0)

    def sign_single_transaction(self, terms):
        """Sign the transaction before send them to agent1."""
        assert self.address == terms.to_address
        from_address_hash = self.instance.functions.getAddress(
            terms.from_address
        ).call()
        to_address_hash = self.instance.functions.getAddress(terms.to_address).call()
        tx_hash = Helpers().get_single_hash(
            _from=from_address_hash,
            _to=to_address_hash,
            _id=terms.item_id,
            _from_value=terms.from_supply,
            _to_value=terms.to_supply,
            _value_eth=terms.value_eth_wei,
            _nonce=terms.trade_nonce,
        )
        assert (
            tx_hash
            == self.instance.functions.getSingleHash(
                terms.from_address,
                terms.to_address,
                terms.item_id,
                terms.from_supply,
                terms.to_supply,
                terms.value_eth_wei,
                terms.trade_nonce,
            ).call()
        )
        signature_dict = self._account.signHash(tx_hash)
        signature = bytes(signature_dict["signature"])
        assert (
            self.w3.eth.account.recoverHash(tx_hash, signature=signature)
            == self.address
        )
        return signature

    def sign_batch_transaction(self, terms):
        """Sign the transaction before send them to agent1."""
        assert self.address == terms.to_address
        from_address_hash = self.instance.functions.getAddress(
            terms.from_address
        ).call()
        to_address_hash = self.instance.functions.getAddress(terms.to_address).call()
        tx_hash = Helpers().get_hash(
            _from=from_address_hash,
            _to=to_address_hash,
            _ids=terms.item_ids,
            _from_values=terms.from_supplies,
            _to_values=terms.to_supplies,
            _value_eth=terms.value_eth_wei,
            _nonce=terms.trade_nonce,
        )
        assert (
            tx_hash
            == self.instance.functions.getHash(
                terms.from_address,
                terms.to_address,
                terms.item_ids,
                terms.from_supplies,
                terms.to_supplies,
                terms.value_eth_wei,
                terms.trade_nonce,
            ).call()
        )
        signature_dict = self._account.signHash(tx_hash)
        signature = bytes(signature_dict["signature"])
        assert (
            self.w3.eth.account.recoverHash(tx_hash, signature=signature)
            == self.address
        )
        return signature


class Helpers:
    """Helper functions for hashing."""

    def get_single_hash(
        self, _from, _to, _id, _from_value, _to_value, _value_eth, _nonce
    ) -> bytes:
        """Generate a hash mirroring the way we are creating this in the contract."""
        return keccak256(
            b"".join(
                [
                    _from,
                    _to,
                    _id.to_bytes(32, "big"),
                    _from_value.to_bytes(32, "big"),
                    _to_value.to_bytes(32, "big"),
                    _value_eth.to_bytes(32, "big"),
                    _nonce.to_bytes(32, "big"),
                ]
            )
        )

    def get_hash(
        self, _from, _to, _ids, _from_values, _to_values, _value_eth, _nonce
    ) -> bytes:
        """Generate a hash mirroring the way we are creating this in the contract."""
        aggregate_hash = keccak256(
            b"".join(
                [
                    _ids[0].to_bytes(32, "big"),
                    _from_values[0].to_bytes(32, "big"),
                    _to_values[0].to_bytes(32, "big"),
                ]
            )
        )
        for i in range(len(_ids)):
            if not i == 0:
                aggregate_hash = keccak256(
                    b"".join(
                        [
                            aggregate_hash,
                            _ids[i].to_bytes(32, "big"),
                            _from_values[i].to_bytes(32, "big"),
                            _to_values[i].to_bytes(32, "big"),
                        ]
                    )
                )

        m_list = []
        m_list.append(_from)
        m_list.append(_to)
        m_list.append(aggregate_hash)
        m_list.append(_value_eth.to_bytes(32, "big"))
        m_list.append(_nonce.to_bytes(32, "big"))
        return keccak256(b"".join(m_list))

    def generate_id(self, token_id, item_id):
        token_id = token_id
        index = item_id
        final_id_int = (token_id << 128) + index
        return final_id_int

    def generate_trade_nonce(self, contract, address):
        """Generate a valid trade nonce."""
        trade_nonce = random.randrange(0, 10000000)
        while contract.instance.functions.is_nonce_used(address, trade_nonce).call():
            trade_nonce = random.randrange(0, 10000000)
        return trade_nonce
