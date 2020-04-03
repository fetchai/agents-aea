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
from typing import Any, Dict, List, Optional

from vyper.utils import keccak256

from aea.configurations.base import ContractConfig, ContractId
from aea.contracts.ethereum import Contract
from aea.crypto.base import LedgerApi
from aea.crypto.ethereum import ETHEREUM
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import Address

logger = logging.getLogger("aea.packages.fetchai.contracts.erc1155.contract")


class ERC1155Contract(Contract):
    """The ERC1155 contract class which acts as a bridge between AEA framework and ERC1155 ABI."""

    class Performative(Enum):
        """The ERC1155 performatives."""

        CONTRACT_DEPLOY = "contract_deploy"
        CONTRACT_CREATE_BATCH = "contract_create_batch"
        CONTRACT_CREATE_SINGLE = "contract_create_single"
        CONTRACT_MINT_BATCH = "contract_mint_batch"
        CONTRACT_ATOMIC_SWAP_SINGLE = "contract_atomic_swap_single"
        CONTRACT_ATOMIC_SWAP_BATCH = "contract_atomic_swap_batch"
        CONTRACT_SIGN_HASH = "contract_sign_hash"

    def __init__(
        self, contract_config: ContractConfig, contract_interface: Dict[str, Any],
    ):
        """Initialize.

        super().__init__(contract_id, contract_config)

        :param config: the contract configurations.
        :param contract_interface: the contract interface.
        """
        super().__init__(contract_config, contract_interface)
        self._token_ids = {}  # type: Dict[int, int]
        self.nonce = 0

    @property
    def token_ids(self) -> Dict[int, int]:
        """The generated token ids."""
        return self._token_ids

    def create_token_ids(self, token_type: int, nb_tokens: int) -> List[int]:
        """
        Populate the token_ids dictionary.

        :param token_type: the token type (nft or ft)
        :param nb_tokens: the number of tokens
        :return: the list of token ids newly created
        """
        lowest_valid_integer = 1
        token_id = Helpers().generate_id(lowest_valid_integer, token_type)
        token_id_list = []
        for _i in range(nb_tokens):
            while self.instance.functions.is_token_id_exists(token_id).call():
                # token_id already taken
                lowest_valid_integer += 1
                token_id = Helpers().generate_id(lowest_valid_integer, token_type)
            token_id_list.append(token_id)
            self.token_ids[token_id] = token_type
            lowest_valid_integer += 1
            token_id = Helpers().generate_id(lowest_valid_integer, token_type)
        return token_id_list

    def get_deploy_transaction(
        self,
        deployer_address: Address,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Deploy a smart contract.

        :param deployer_address: The address that deploys the smart-contract
        :param ledger_api: the ledger API
        :param skill_callback_id: the skill callback id
        :param info: optional info to pass with the transaction message
        :return: the transaction message for the decision maker
        """
        assert not self.is_deployed, "The contract is already deployed!"
        tx = self._create_deploy_transaction(
            deployer_address=deployer_address, ledger_api=ledger_api
        )
        logger.debug(
            "get_deploy_transaction: deployer_address={}, tx={}".format(
                deployer_address, tx,
            )
        )
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
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx": tx},
        )

        return tx_message

    def _create_deploy_transaction(
        self, deployer_address: Address, ledger_api: LedgerApi
    ) -> Dict[str, Any]:
        """
        Get the deployment transaction.

        :param deployer_address: The address that will deploy the contract.
        :param ledger_api: the ledger API
        :returns tx: the transaction dictionary.
        """
        # create the transaction dict
        self.nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        tx_data = self.instance.constructor().__dict__.get("data_in_transaction")
        tx = {
            "from": deployer_address,  # Only 'from' address, don't insert 'to' address
            "value": 0,  # Add how many ethers you'll transfer during the deploy
            "gas": 0,  # Trying to make it dynamic ..
            "gasPrice": ledger_api.api.eth.gasPrice,  # Get Gas Price
            "nonce": self.nonce,  # Get Nonce
            "data": tx_data,  # Here is the data sent through the network
        }

        # estimate the gas and update the transaction dict
        gas_estimate = ledger_api.api.eth.estimateGas(transaction=tx)
        logger.debug("gas estimate deploy: {}".format(gas_estimate))
        tx["gas"] = gas_estimate
        return tx

    def get_create_batch_transaction(
        self,
        deployer_address: Address,
        token_ids: List[int],
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Create a batch of items.

        :param deployer_address: the address of the deployer (owner)
        :param token_ids: the list of token ids for creation
        :param ledger_api: the ledger API
        :param skill_callback_id: the skill callback id
        :param info: optional info to pass with the transaction message
        :return: the transaction message for the decision maker
        """
        tx = self._get_create_batch_tx(
            deployer_address=deployer_address,
            token_ids=token_ids,
            ledger_api=ledger_api,
        )
        logger.debug(
            "get_create_batch_transaction: deployer_address={}, token_ids={}, tx={}".format(
                deployer_address, token_ids, tx,
            )
        )
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
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx": tx},
        )
        return tx_message

    def _get_create_batch_tx(
        self, deployer_address: Address, token_ids: List[int], ledger_api: LedgerApi
    ) -> str:
        """
        Create a batch of items.

        :param deployer_address: the address of the deployer
        :param token_ids: the list of token ids for creation
        :param ledger_api: the ledger API
        :return: the transaction object
        """
        self.nonce += 1
        nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        assert nonce <= self.nonce, "The local nonce should be >= from the chain nonce."
        tx = self.instance.functions.createBatch(
            deployer_address, token_ids
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 300000,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": self.nonce,
            }
        )
        return tx

    def get_create_single_transaction(
        self,
        deployer_address: Address,
        token_id: int,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Create a single item.

        :param deployer_address: the address of the deployer (owner)
        :param token_id: the token id for creation
        :param ledger_api: the ledger API
        :param skill_callback_id: the skill callback id
        :param info: optional info to pass with the transaction message
        :return: the transaction message for the decision maker
        """
        tx = self._get_create_single_tx(
            deployer_address=deployer_address, token_id=token_id, ledger_api=ledger_api,
        )
        logger.debug(
            "get_create_single_transaction: deployer_address={}, token_id={}, tx={}".format(
                deployer_address, token_id, tx,
            )
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_CREATE_SINGLE.value,
            tx_sender_addr=deployer_address,
            tx_counterparty_addr="",
            tx_amount_by_currency_id={"ETH": 0},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx": tx},
        )
        return tx_message

    def _get_create_single_tx(
        self, deployer_address: Address, token_id: int, ledger_api: LedgerApi
    ) -> str:
        """
        Create a single item.

        :param deployer_address: the address of the deployer
        :param token_id: the token id for creation
        :param ledger_api: the ledger API
        :return: the transaction object
        """
        self.nonce += 1
        nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        assert nonce <= self.nonce, "The local nonce should be >= from the chain nonce."
        tx = self.instance.functions.createSingle(
            deployer_address, token_id, ""
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 500000,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": self.nonce,
            }
        )
        return tx

    def get_mint_batch_transaction(
        self,
        deployer_address: Address,
        recipient_address: Address,
        token_ids: List[int],
        mint_quantities: List[int],
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Mint a batch of tokens.

        :param deployer_address: the deployer_address
        :param recipient_address: the recipient_address
        :param token_ids: the token ids
        :param mint_quantities: the mint_quantities of each token
        :param ledger_api: the ledger api
        :param skill_callback_id: the skill callback id
        :param info: the optional info payload for the transaction message
        :return: the transaction message for the decision maker
        """
        assert len(mint_quantities) == len(token_ids), "Wrong number of items."
        tx = self._create_mint_batch_tx(
            deployer_address=deployer_address,
            recipient_address=recipient_address,
            token_ids=token_ids,
            mint_quantities=mint_quantities,
            ledger_api=ledger_api,
        )
        logger.debug(
            "get_mint_batch_transaction: deployer_address={}, recipient_address={}, token_ids={}, mint_quantities={}, tx={}".format(
                deployer_address, recipient_address, token_ids, mint_quantities, tx,
            )
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
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx": tx},
        )

        return tx_message

    def _create_mint_batch_tx(
        self,
        deployer_address: Address,
        recipient_address: Address,
        token_ids: List[int],
        mint_quantities: List[int],
        ledger_api: LedgerApi,
    ) -> str:
        """
        Get transaction object to mint a batch of tokens.

        :param deployer_address: the address of the deployer
        :param recipient_address: the address of the recipient
        :param token_ids: the token ids
        :param mint_quantities: the quantity to mint for each token
        :param ledger_api: the ledger API
        :return: the transaction object
        """
        self.nonce += 1
        nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        assert nonce <= self.nonce, "The local nonce should be > from the chain nonce."
        for i in range(len(token_ids)):
            decoded_type = Helpers().decode_id(token_ids[i])
            assert (
                decoded_type == 1 or decoded_type == 2
            ), "The token prefix must be 1 or 2."
            if decoded_type == 1:
                assert (
                    mint_quantities[i] == 1
                ), "Cannot mint NFT with mint_quantity more than 1"
        tx = self.instance.functions.mintBatch(
            recipient_address, token_ids, mint_quantities
        ).buildTransaction(
            {
                "chainId": 3,
                "gas": 500000,
                "gasPrice": ledger_api.api.toWei("50", "gwei"),
                "nonce": self.nonce,
            }
        )
        return tx

    def get_mint_single_tx(
        self,
        deployer_address: Address,
        recipient_address: Address,
        token_id: int,
        mint_quantity: int,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Mint a single token.

        :param deployer_address: the deployer_address
        :param recipient_address: the recipient_address
        :param token_id: the token id
        :param mint_quantity: the mint_quantity of each token
        :param ledger_api: the ledger api
        :param skill_callback_id: the skill callback id
        :param info: the optional info payload for the transaction message
        :return: the transaction message for the decision maker
        """
        tx = self._create_mint_single_tx(
            deployer_address=deployer_address,
            recipient_address=recipient_address,
            token_id=token_id,
            mint_quantity=mint_quantity,
            ledger_api=ledger_api,
        )
        logger.debug(
            "get_mint_single_tx: deployer_address={}, recipient_address={}, token_id={}, mint_quantity={}, tx={}".format(
                deployer_address, recipient_address, token_id, mint_quantity, tx,
            )
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
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx": tx},
        )
        return tx_message

    def _create_mint_single_tx(
        self, deployer_address, recipient_address, token_id, mint_quantity, ledger_api,
    ) -> str:
        """
        Get transaction object to mint single token.

        :param deployer_address: the address of the deployer
        :param recipient_address: the address of the recipient
        :param token_id: the token id
        :param mint_quantity: the quantity to mint
        :param ledger_api: the ledger API
        :return: the transaction object
        """
        self.nonce += 1
        nonce = ledger_api.api.eth.getTransactionCount(deployer_address)
        assert nonce <= self.nonce, "The local nonce should be >= from the chain nonce."
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
                "nonce": self.nonce,
            }
        )

        return tx

    def get_balance(self, address: Address, token_id: int) -> int:
        """
        Get the balance for a specific token id.

        :param address: the address
        :param token_id: the token id
        :return: the balance
        """
        return self.instance.functions.balanceOf(address, token_id).call()

    def get_atomic_swap_single_transaction_proposal(
        self,
        from_address: Address,
        to_address: Address,
        token_id: int,
        from_supply: int,
        to_supply: int,
        value: int,
        trade_nonce: int,
        signature: str,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Create a transaction message for a trustless trade between two agents for a single token.

        :param from_address: the address of the agent sending tokens, receiving ether
        :param to_address: the address of the agent receiving tokens, sending ether
        :param token_id: the token id
        :param from_supply: the supply of tokens by the sender
        :param to_supply: the supply of tokens by the receiver
        :param value: the amount of ether sent from the to_address to the from_address
        :param trade_nonce: the nonce of the trade, this is separate from the nonce of the transaction
        :param signature: the signature of the trade
        :param ledger_api: the ledger API
        :param skill_callback_id: the skill callback id
        :param info: optional info to pass around with the transaction message
        :return: the transaction message for the decision maker
        """
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        tx = self._create_trade_tx(
            from_address,
            to_address,
            token_id,
            from_supply,
            to_supply,
            value_eth_wei,
            trade_nonce,
            signature,
            ledger_api,
        )
        logger.debug(
            "get_atomic_swap_single_transaction_proposal: from_address={}, to_address={}, token_id={}, from_supply={}, to_supply={}, value_eth_wei={}, trade_nonce={}, signature={}, tx={}".format(
                from_address,
                to_address,
                token_id,
                from_supply,
                to_supply,
                value_eth_wei,
                trade_nonce,
                signature,
                tx,
            )
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_ATOMIC_SWAP_SINGLE.value,
            tx_sender_addr=from_address,
            tx_counterparty_addr=to_address,
            tx_amount_by_currency_id={"ETH": value},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx": tx},
        )
        return tx_message

    def _create_trade_tx(
        self,
        from_address: Address,
        to_address: Address,
        token_id: int,
        from_supply: int,
        to_supply: int,
        value_eth_wei: int,
        trade_nonce: int,
        signature: str,
        ledger_api: LedgerApi,
    ) -> str:
        """
        Create a trade tx.

        :param from_address: the address of the agent sending tokens, receiving ether
        :param to_address: the address of the agent receiving tokens, sending ether
        :param token_id: the token id
        :param from_supply: the supply of tokens by the sender
        :param to_supply: the supply of tokens by the receiver
        :param value: the amount of ether sent from the to_address to the from_address
        :param trade_nonce: the nonce of the trade, this is separate from the nonce of the transaction
        :param signature: the signature of the trade
        :param ledger_api: the ledger API
        :return: a ledger transaction object
        """
        data = b"single_atomic_swap"
        self.nonce += 1
        nonce = ledger_api.api.eth.getTransactionCount(from_address)
        assert nonce <= self.nonce, "The local nonce should be >= from the chain nonce."
        tx = self.instance.functions.trade(
            from_address,
            to_address,
            token_id,
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
                "nonce": self.nonce,
            }
        )
        return tx

    def get_balance_of_batch(self, address: Address, token_ids: List[int]) -> List[int]:
        """
        Get the balance for a batch of specific token ids.

        :param address: the address
        :param token_id: the token id
        :return: the balance
        """
        result = self.instance.functions.balanceOfBatch(
            [address] * 10, token_ids
        ).call()
        return result

    def get_atomic_swap_batch_transaction_proposal(
        self,
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
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Create a transaction message for a trustless trade between two agents for a batch of tokens.

        :param from_address: the address of the agent sending tokens, receiving ether
        :param to_address: the address of the agent receiving tokens, sending ether
        :param token_ids: the token ids
        :param from_supplies: the supplies of tokens by the sender
        :param to_supplies: the supplies of tokens by the receiver
        :param value: the amount of ether sent from the to_address to the from_address
        :param trade_nonce: the nonce of the trade, this is separate from the nonce of the transaction
        :param signature: the signature of the trade
        :param ledger_api: the ledger API
        :param skill_callback_id: the skill callback id
        :param info: optional info to pass around with the transaction message
        :return: the transaction message for the decision maker
        """
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        tx = self._create_trade_batch_tx(
            from_address=from_address,
            to_address=to_address,
            token_ids=token_ids,
            from_supplies=from_supplies,
            to_supplies=to_supplies,
            value_eth_wei=value_eth_wei,
            trade_nonce=trade_nonce,
            signature=signature,
            ledger_api=ledger_api,
        )
        logger.debug(
            "get_atomic_swap_batch_transaction_proposal: from_address={}, to_address={}, token_id={}, from_supplies={}, to_supplies={}, value_eth_wei={}, trade_nonce={}, signature={}, tx={}".format(
                from_address,
                to_address,
                token_ids,
                from_supplies,
                to_supplies,
                value_eth_wei,
                trade_nonce,
                signature,
                tx,
            )
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_ATOMIC_SWAP_BATCH.value,
            tx_sender_addr=from_address,
            tx_counterparty_addr=to_address,
            tx_amount_by_currency_id={"ETH": value},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx": tx},
        )
        return tx_message

    def _create_trade_batch_tx(
        self,
        from_address: Address,
        to_address: Address,
        token_ids: List[int],
        from_supplies: List[int],
        to_supplies: List[int],
        value_eth_wei: int,
        trade_nonce: int,
        signature: str,
        ledger_api: LedgerApi,
    ) -> str:
        """
        Create a batch trade tx.

        :param from_address: the address of the agent sending tokens, receiving ether
        :param to_address: the address of the agent receiving tokens, sending ether
        :param token_id: the token id
        :param from_supply: the supply of tokens by the sender
        :param to_supply: the supply of tokens by the receiver
        :param value_eth_wei: the amount of ether (in wei) sent from the to_address to the from_address
        :param trade_nonce: the nonce of the trade, this is separate from the nonce of the transaction
        :param signature: the signature of the trade
        :param ledger_api: the ledger API
        :return: a ledger transaction object
        """
        data = b"batch_atomic_swap"
        self.nonce += 1
        nonce = ledger_api.api.eth.getTransactionCount(from_address)
        assert nonce <= self.nonce, "The local nonce should be >= from the chain nonce."
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
                "nonce": self.nonce,
            }
        )
        return tx

    def get_hash_single_transaction(
        self,
        from_address: Address,
        to_address: Address,
        token_id: int,
        from_supply: int,
        to_supply: int,
        value: int,
        trade_nonce: int,
        ledger_api: LedgerApi,
        skill_callback_id: ContractId,
        info: Optional[Dict[str, Any]] = None,
    ) -> TransactionMessage:
        """
        Get the hash for a transaction involving a single token.

        :param from_address: the address of the agent sending tokens, receiving ether
        :param to_address: the address of the agent receiving tokens, sending ether
        :param token_id: the token id
        :param from_supply: the supply of tokens by the sender
        :param to_supply: the supply of tokens by the receiver
        :param value: the amount of ether sent from the to_address to the from_address
        :param ledger_api: the ledger API
        :param skill_callback_id: the skill callback id
        :param info: optional info to pass with the transaction message
        :return: the transaction message for the decision maker
        """
        from_address_hash = self.instance.functions.getAddress(from_address).call()
        to_address_hash = self.instance.functions.getAddress(to_address).call()
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        tx_hash = Helpers().get_single_hash(
            _from=from_address_hash,
            _to=to_address_hash,
            _id=token_id,
            _from_value=from_supply,
            _to_value=to_supply,
            _value_eth_wei=value_eth_wei,
            _nonce=trade_nonce,
        )
        assert (
            tx_hash
            == self.instance.functions.getSingleHash(
                from_address,
                to_address,
                token_id,
                from_supply,
                to_supply,
                value_eth_wei,
                trade_nonce,
            ).call()
        )
        logger.debug(
            "get_hash_single_transaction: from_address={}, to_address={}, token_id={}, from_supply={}, to_supply={}, value_eth_wei={}, trade_nonce={}, tx_hash={!r}".format(
                from_address,
                to_address,
                token_id,
                from_supply,
                to_supply,
                value_eth_wei,
                trade_nonce,
                tx_hash,
            )
        )
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            skill_callback_ids=[skill_callback_id],
            tx_id=ERC1155Contract.Performative.CONTRACT_SIGN_HASH.value,
            tx_sender_addr=from_address,
            tx_counterparty_addr=to_address,
            tx_amount_by_currency_id={"ETH": value},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={},
            info=info if info is not None else {},
            ledger_id=ETHEREUM,
            signing_payload={"tx_hash": tx_hash, "is_deprecated_mode": True},
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
    ) -> None:
        """
        Sign the transaction before send them to agent1.

        :param from_address: the address of the agent sending tokens, receiving ether
        :param to_address: the address of the agent receiving tokens, sending ether
        :param token_ids: the list of token ids for the bash transaction
        :param from_supplies: the quantities of tokens sent from the from_address to the to_address
        :param to_supplies: the quantities of tokens sent from the to_address to the from_address
        :param value: the value of ether sent from the from_address to the to_address
        :param trade_nonce: the trade nonce
        :param ledger_api: the ledger API
        :raise: NotImplementedError
        """
        from_address_hash = self.instance.functions.getAddress(from_address).call()
        to_address_hash = self.instance.functions.getAddress(to_address).call()
        value_eth_wei = ledger_api.api.toWei(value, "ether")
        tx_hash = Helpers().get_hash(
            _from=from_address_hash,
            _to=to_address_hash,
            _ids=token_ids,
            _from_values=from_supplies,
            _to_values=to_supplies,
            _value_eth_wei=value_eth_wei,
            _nonce=trade_nonce,
        )
        logger.debug(
            "get_hash_batch_transaction: from_address={}, to_address={}, token_ids={}, from_supplies={}, to_supplies={}, value_eth_wei={}, trade_nonce={}, tx_hash={!r}".format(
                from_address,
                to_address,
                token_ids,
                from_supplies,
                to_supplies,
                value_eth_wei,
                trade_nonce,
                tx_hash,
            )
        )
        raise NotImplementedError

    def generate_trade_nonce(self, address: Address) -> int:  # nosec
        """
        Generate a valid trade nonce.

        :param address: the address to use
        :return: the generated trade nonce
        """
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
        _value_eth_wei: int,
        _nonce: int,
    ) -> bytes:
        """
        Generate a hash mirroring the way we are creating this in the contract.

        :param _from: the from address hashed
        :param _to: the to address hashed
        :param _ids: the token ids
        :param _from_value: the from value
        :param _to_value: the to value
        :param _value_eth_wei: the value eth (in wei)
        :param _nonce: the trade nonce
        :return: the hash in bytes string representation
        """
        return keccak256(
            b"".join(
                [
                    _from,
                    _to,
                    _id.to_bytes(32, "big"),
                    _from_value.to_bytes(32, "big"),
                    _to_value.to_bytes(32, "big"),
                    _value_eth_wei.to_bytes(32, "big"),
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
        _value_eth_wei: int,
        _nonce: int,
    ) -> bytes:
        """
        Generate a hash mirroring the way we are creating this in the contract.

        :param _from: the from address hashed
        :param _to: the to address hashed
        :param _ids: the token ids
        :param _from_values: the from values
        :param _to_values: the to values
        :param _value_eth_wei: the value of eth (in wei)
        :param _nonce: the trade nonce
        :return: the hash in bytes string representation
        """
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
        m_list.append(_value_eth_wei.to_bytes(32, "big"))
        m_list.append(_nonce.to_bytes(32, "big"))
        return keccak256(b"".join(m_list))

    def generate_id(self, index: int, token_type: int):
        """
        Generate a token_id.

        :param index: the index to byte-shift
        :param token_type: the token type
        :return: the token id
        """
        final_id_int = (token_type << 128) + index
        return final_id_int

    def decode_id(self, token_id: int):
        """
        Decode a give token id.

        :param token_id: the byte shifted token id
        :return: the non-shifted id
        """
        decoded_type = token_id >> 128
        return decoded_type
