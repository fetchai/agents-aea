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
from web3 import Web3

from aea.configurations.base import ContractId
from aea.contracts.base import Contract
from aea.crypto.base import Crypto, LedgerApi
from aea.decision_maker.messages.contract_transaction import ContractTransactionMessage
from aea.mail.base import Address

CHAIN_ID = 3
PROVIDER = "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe"

NFT = 1
FT = 2

logger = logging.getLogger(__name__)


class ERC1155Contract(Contract):
    """The ERC1155 contract class."""

    contract_id = ContractId("fetchai", "erc1155", "0.1.0")

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self.deployed = False
        self.abi = None
        self.bytecode = None
        self.instance = None
        # We can consider of passing the list of ids rather than creating them here.
        batch_token_ids = []
        for j in range(10):
            batch_token_ids.append(Helpers().generate_id(FT, j))
        self.item_ids = batch_token_ids

    def load_from_json(self, ledger_api: LedgerApi) -> None:
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
        self.instance = ledger_api.eth.contract(abi=self.abi, bytecode=self.bytecode)

    #  This should go to the Decision Maker.
    def _sign_transaction(self, tx, account: Crypto):
        tx_signed = self.w3.eth.account.signTransaction(
            transaction_dict=tx, private_key=account.entity.key
        )
        return tx_signed

    def deploy_contract(self, deployer_address: Address, ledger_api: LedgerApi) -> ContractTransactionMessage:
        """
        Deploy a smart contract.

        :params deployer_address: The address that deploys the smart-contract
        """
        #  Request to deploy the contract from the decision maker and then ask ledger_apis ?
        tx = self._create_deploy_transaction(deployer_address=deployer_address, ledger_api=ledger_api)

        #  Create the transaction message for the Decision maker
        contract_deploy_message = ContractTransactionMessage(
            performative=ContractTransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[ContractId("fetchai", "erc1155", "0.1.0")],
            tx_type='contract_deployment',
            tx_sender_addr= deployer_address,
            tx_sender_fee=0,
            ledger_id=ledger_api.identifier,
            info=Dict[str, Any],
            payload=tx,
        )

        return contract_deploy_message
        # tx_signed = self._sign_transaction(tx=tx)
        # self.send_tx(tx_signed=tx_signed, tx_type="contract_deployment")

    def _create_deploy_transaction(self, deployer_address: Address, ledger_api: LedgerApi) -> Dict[str, Any]:
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
            "gasPrice": ledger_api.api.toWei("50", "gwei"),  # Get Gas Price
            "nonce": ledger_api.api.eth.getTransactionCount(deployer_address),  # Get Nonce
            "data": tx_data,  # Here is the data sent through the network
        }

        # estimate the gas and update the transaction dict
        gas_estimate = ledger_api.api.eth.estimateGas(transaction=tx)
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

    def _get_create_batch_tx(self, deployer_address: Address) -> str:
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

    def _get_trade_tx(self, terms, signature) -> str:
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

        return tx

    def _get_trade_batch_tx(self, terms, signature) -> str:
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
    ) -> str:
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

    def atomic_swap_single(self, contract, terms, signature) -> None:
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

    def atomic_swap_batch(self, contract, terms, signature) -> None:
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

    def sign_single_transaction(self, terms, account: Crypto) -> bytes:
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
        signature_dict = account.entity.signHash(tx_hash)
        signature = bytes(signature_dict["signature"])

        # This is more of a sanity check. I ll add the check in the ledger_api.
        # assert (
        #     self.w3.eth.account.recoverHash(tx_hash, signature=signature)
        #     == self.address
        # )
        return signature

    def sign_batch_transaction(self, terms, account: Crypto):
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
        signature_dict = account.entity.signHash(tx_hash)
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
