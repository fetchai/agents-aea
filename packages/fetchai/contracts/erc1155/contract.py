# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains the erc1155 contract definition."""
import logging
import random
from enum import Enum
from typing import Any, Dict, List

from vyper.utils import keccak256

from aea.configurations.base import ContractConfig, ContractId
from aea.contracts.ethereum import Contract
from aea.crypto.base import LedgerApi
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import Address

logger = logging.getLogger(__name__)


class ERC1155Contract(Contract):
    """The ERC1155 contract class."""

    class Performative(Enum):
        """The ERC1155 performatives."""

        CONTRACT_DEPLOY = "contract_deploy"
        CONTRACT_CREATE_BATCH = "contract_create_batch"
        CONTRACT_MINT_BATCH = "contract_mint_batch"
        CONTRACT_ATOMIC_SWAP_SINGLE = "contract_atomic_swap_single"
        CONTRACT_ATOMIC_SWAP_BATCH = "contract_atomic_swap_batch"
        CONTRACT_SIGN_HASH = "contract_sign_hash"

    def __init__(
        self,
        contract_id: ContractId,
        contract_config: ContractConfig,
        contract_interface: Dict[str, Any],
    ):
        """Initialize.

        super().__init__(contract_id, contract_config)


        :param contract_id: the contract id.
        :param config: the contract configurations.
        :param contract_interface: the contract interface.
        """
        super().__init__(contract_id, contract_config, contract_interface)
        self._token_ids = {}  # type: Dict[int, int]

    @property
    def token_ids(self) -> Dict[int, int]:
        """The generated token ids."""
        return self._token_ids

    def create_token_ids(self, token_type: int, nb_tokens: int) -> List[int]:
        """Populate the token_ids dictionary."""
        assert self.token_ids == {}, "Item ids already created."
        lowest_valid_integer = 0
        token_id = Helpers().generate_id(token_type, lowest_valid_integer)
        token_id_list = []
        for _i in range(nb_tokens):
            while self.instance.functions.is_token_id_exists(token_id).call():
                # id already taken
                lowest_valid_integer += 1
                token_id = Helpers().generate_id(token_type, lowest_valid_integer)
            token_id_list.append(token_id)
            self.token_ids[token_id] = token_type

        return token_id_list

    def get_deploy_transaction(
        self,
        deployer_address: Address,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
    ) -> TransactionMessage:
        """
        Deploy a smart contract.

        :params deployer_address: The address that deploys the smart-contract
        """
        assert not self.is_deployed, "The contract is already deployed!"
        tx = self._create_deploy_transaction(
            deployer_address=deployer_address, ledger_api=ledger_api
        )

        #  Create the transaction message for the Decision maker
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_DEPLOY.value,
            tx_sender_addr=deployer_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx": tx},
        )

        return tx_message

    def _create_deploy_transaction(
        self, deployer_address: Address, ledger_api: LedgerApi
    ) -> Dict[str, Any]:
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
            "nonce": ledger_api.api.eth.getTransactionCount(
                deployer_address
            ),  # Get Nonce
            "data": tx_data,  # Here is the data sent through the network
        }

        # estimate the gas and update the transaction dict
        gas_estimate = ledger_api.api.eth.estimateGas(transaction=tx)
        logger.info("gas estimate deploy: {}".format(gas_estimate))
        tx["gas"] = gas_estimate
        return tx

    def get_create_batch_transaction(
        self,
        deployer_address: Address,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
    ) -> TransactionMessage:
        """
        Create an mint a batch of items.

        :params address: The address that will receive the items
        :params mint_quantities: A list[10] of ints. The index represents the id in the token_ids dict.
        """
        # create the items

        tx = self._get_create_batch_tx(
            deployer_address=deployer_address, ledger_api=ledger_api
        )

        #  Create the transaction message for the Decision maker
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_CREATE_BATCH.value,
            tx_sender_addr=deployer_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx": tx},
        )

        return tx_message

    def _get_create_batch_tx(
        self, deployer_address: Address, ledger_api: LedgerApi
    ) -> str:
        """Create a batch of items."""
        # create the items
        nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        tx = self.instance.functions.createBatch(
            deployer_address, self.token_ids
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 300000,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        return tx

    def get_create_single_transaction(
        self,
        deployer_address: Address,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        token_id: int,
    ) -> TransactionMessage:

        """
              Create an mint a batch of items.

              :params address: The address that will receive the items
              :params mint_quantities: A list[10] of ints. The index represents the id in the item_ids list.
              """
        # create the items

        tx = self._get_create_single_tx(
            deployer_address=deployer_address, ledger_api=ledger_api, token_id=token_id
        )

        #  Create the transaction message for the Decision maker
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id="contract_create_currency",
            tx_sender_addr=deployer_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx": tx},
        )

        return tx_message

    def _get_create_single_tx(
        self, deployer_address: Address, ledger_api: LedgerApi, token_id: int
    ) -> str:
        """Create an item."""
        nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        tx = self.instance.functions.createSingle(
            deployer_address, token_id, ""
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 500000,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        return tx

    def get_mint_batch_transaction(
        self,
        deployer_address: Address,
        recipient_address: Address,
        mint_quantities: List[int],
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
    ):

        assert len(mint_quantities) == len(self.token_ids), "Wrong number of items."
        tx = self._create_mint_batch_tx(
            deployer_address=deployer_address,
            recipient_address=recipient_address,
            batch_mint_quantities=mint_quantities,
            ledger_api=ledger_api,
        )

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_MINT_BATCH.value,
            tx_sender_addr=deployer_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx": tx},
        )

        return tx_message

    def _create_mint_batch_tx(
        self,
        deployer_address: Address,
        recipient_address: Address,
        batch_mint_quantities: List[int],
        ledger_api: LedgerApi,
    ) -> str:
        """Mint a batch of items."""
        # mint batch
        nonce = ledger_api.api.eth.getTransactionCount(
            ledger_api.api.toChecksumAddress(deployer_address)
        )
        nonce += 1
        tx = self.instance.functions.mintBatch(
            recipient_address, self.token_ids, batch_mint_quantities
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 500000,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )

        return tx

    def get_mint_single_tx(
        self,
        deployer_address: Address,
        recipient_address: Address,
        mint_quantity: int,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        token_id: int,
    ) -> TransactionMessage:

        tx = self._create_mint_single_tx(
            deployer_address=deployer_address,
            recipient_address=recipient_address,
            token_id=token_id,
            mint_quantity=mint_quantity,
            ledger_api=ledger_api,
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id="contract_mint_batch",
            tx_sender_addr=deployer_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx": tx},
        )

        return tx_message

    def _create_mint_single_tx(
        self, deployer_address, recipient_address, token_id, mint_quantity, ledger_api,
    ) -> str:
        """Mint a batch of items."""
        # mint batch
        nonce = ledger_api.api.eth.getTransactionCount(
            ledger_api.api.toChecksumAddress(deployer_address)
        )
        assert recipient_address is not None
        decoded_type = Helpers().decode_id(token_id)
        assert (
            decoded_type == 1 or decoded_type == 2
        ), "The token prefix must be 1 or 2."
        if decoded_type == 1:
            assert mint_quantity == 1, "Cannot mint NFT with mint_quantity more than 1"
        data = b"MintingSingle"
        tx = self.instance.functions.mint(
            recipient_address, token_id, mint_quantity, data
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 300000,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )

        return tx

    def _create_trade_tx(
        self,
        from_address: Address,
        to_address: Address,
        item_id: int,
        from_supply: int,
        to_supply: int,
        value_eth_wei: int,
        trade_nonce: int,
        signature: str,
        ledger_api: LedgerApi,
    ) -> str:
        """
        Create a trade tx.

        :params terms: The class (can be Dict[str, Any]) that contains the details for the transaction.
        :params signature: The signed terms from the counterparty.
        """
        data = b"hello"
        nonce = ledger_api.api.eth.getTransactionCount(from_address) + 1
        tx = self.instance.functions.trade(
            from_address,
            to_address,
            item_id,
            from_supply,
            to_supply,
            value_eth_wei,
            trade_nonce,
            signature,
            data,
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 2818111,
                "from": from_address,
                "value": value_eth_wei,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )

        return tx

    def _create_trade_batch_tx(
        self,
        from_address: Address,
        to_address: Address,
        token_ids: List[int],
        from_supplies: List[int],
        to_supplies: List[int],
        value: int,
        trade_nonce: int,
        signature: str,
        ledger_api: LedgerApi,
    ) -> str:
        """
        Create a batch trade tx.

        :params terms: The class (can be Dict[str, Any]) that contains the details for the transaction.
        :params signature: The signed terms from the counterparty.
        """
        data = b"hello"
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        nonce = ledger_api.api.eth.getTransactionCount(from_address) + 1
        tx = self.instance.functions.tradeBatch(
            from_address,
            to_address,
            token_ids,
            from_supplies,
            to_supplies,
            value_eth_wei,
            trade_nonce,
            signature,
            data,
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 2818111,
                "from": from_address,
                "value": value_eth_wei,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": nonce,
            }
        )
        return tx

    def get_balance(self, from_address: Address, item_id: int):
        """Get the balance for the specific id."""
        return self.instance.functions.balanceOf(from_address, item_id).call()

    def get_atomic_swap_single_proposal(
        self,
        from_address: Address,
        to_address: Address,
        item_id: int,
        from_supply: int,
        to_supply: int,
        value: int,
        trade_nonce: int,
        signature: str,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
    ) -> TransactionMessage:
        """Make a trustless trade between to agents for a single token."""
        # assert self.address == terms.from_address, "Wrong from address"
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        tx = self._create_trade_tx(
            from_address,
            to_address,
            item_id,
            from_supply,
            to_supply,
            value_eth_wei,
            trade_nonce,
            signature,
            ledger_api,
        )

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_ATOMIC_SWAP_SINGLE.value,
            tx_sender_addr=from_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx": tx},
        )

        return tx_message

    def get_balance_of_batch(self, address: Address):
        """Get the balance for a batch of items"""
        return self.instance.functions.balanceOfBatch(
            [address] * 10, self.token_ids
        ).call()

    def get_atomic_swap_batch_transaction_proposal(
        self,
        deployer_address: Address,
        from_address: Address,
        to_address: Address,
        token_ids: List[int],
        from_supplies: List[int],
        to_supplies: List[int],
        value: int,
        trade_nonce: int,
        signature: str,
        skill_callback_id: ContractId,
        ledger_api: LedgerApi,
    ) -> TransactionMessage:
        """Make a trust-less trade for a batch of items between 2 agents."""
        assert deployer_address == from_address, "Wrong 'from' address"
        tx = self._create_trade_batch_tx(
            from_address=from_address,
            to_address=to_address,
            token_ids=token_ids,
            from_supplies=from_supplies,
            to_supplies=to_supplies,
            value=value,
            trade_nonce=trade_nonce,
            signature=signature,
            ledger_api=ledger_api,
        )

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_ATOMIC_SWAP_BATCH.value,
            tx_sender_addr=from_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx": tx},
        )

        return tx_message

    def get_hash_single_transaction(
        self,
        from_address: Address,
        to_address: Address,
        item_id: int,
        from_supply: int,
        to_supply: int,
        value: int,
        trade_nonce: int,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
    ) -> TransactionMessage:
        """Sign the transaction before send them to agent1."""
        # assert self.address == terms.to_address
        from_address_hash = self.instance.functions.getAddress(from_address).call()
        to_address_hash = self.instance.functions.getAddress(to_address).call()
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        tx_hash = Helpers().get_single_hash(
            _from=from_address_hash,
            _to=to_address_hash,
            _id=item_id,
            _from_value=from_supply,
            _to_value=to_supply,
            _value_eth=value_eth_wei,
            _nonce=trade_nonce,
        )

        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_SIGN_HASH.value,
            tx_sender_addr=from_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info={},
            ledger_id="ethereum",
            signing_payload={"tx_hash": tx_hash},
        )

        return tx_message

    def get_hash_batch_transaction(
        self,
        from_address: Address,
        to_address: Address,
        token_ids: List[int],
        from_supplies: List[int],
        to_supplies: List[int],
        value: int,
        trade_nonce: int,
        ledger_api: LedgerApi,
    ):
        """Sign the transaction before send them to agent1."""
        from_address_hash = self.instance.functions.getAddress(from_address).call()
        to_address_hash = self.instance.functions.getAddress(to_address).call()
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        tx_hash = Helpers().get_hash(
            _from=from_address_hash,
            _to=to_address_hash,
            _ids=token_ids,
            _from_values=from_supplies,
            _to_values=to_supplies,
            _value_eth=value_eth_wei,
            _nonce=trade_nonce,
        )

        return tx_hash

    def generate_trade_nonce(self, address: Address):  # nosec
        """Generate a valid trade nonce."""
        trade_nonce = random.randrange(0, 10000000)
        while self.instance.functions.is_nonce_used(address, trade_nonce).call():
            trade_nonce = random.randrange(0, 10000000)
        return trade_nonce


class Helpers:
    """Helper functions for hashing."""

    def get_single_hash(
        self,
        _from: bytes,
        _to: bytes,
        _id: int,
        _from_value: int,
        _to_value: int,
        _value_eth: int,
        _nonce: int,
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
        self,
        _from: bytes,
        _to: bytes,
        _ids: List[int],
        _from_values: List[int],
        _to_values: List[int],
        _value_eth: int,
        _nonce: int,
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

    def generate_id(self, index: int, token_type: int):
        """Generate a token_id"""
        final_id_int = (token_type << 128) + index
        return final_id_int

    def decode_id(self, token_id: int):
        """Decode a give token id."""
        decoded_type = token_id >> 128
        return decoded_type
