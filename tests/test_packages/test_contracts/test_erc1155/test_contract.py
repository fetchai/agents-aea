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

"""The tests module contains the tests of the packages/contracts/erc1155 dir."""

import time
from pathlib import Path
from typing import Dict, cast

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

from aea.configurations.base import ComponentType, ContractConfig
from aea.configurations.loader import load_component_configuration
from aea.contracts.base import Contract, contract_registry
from aea.crypto.registries import (
    crypto_registry,
    faucet_apis_registry,
    ledger_apis_registry,
)

from tests.conftest import (
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_ADDRESS_TWO,
    FETCHAI_TESTNET_CONFIG,
    MAX_FLAKY_RERUNS,
    ROOT_DIR,
)


crypto = [
    (EthereumCrypto.identifier,),
]


@pytest.fixture(params=crypto)
def crypto_api(request):
    """Crypto api fixture."""
    crypto_id = request.param[0]
    api = crypto_registry.make(crypto_id)
    yield api


@pytest.mark.integration
@pytest.mark.ledger
def test_helper_methods_and_get_transactions(ledger_api, erc1155_contract):
    """Test helper methods and get transactions."""
    contract, contract_address = erc1155_contract
    expected_a = [
        340282366920938463463374607431768211456,
        340282366920938463463374607431768211457,
        340282366920938463463374607431768211458,
        340282366920938463463374607431768211459,
        340282366920938463463374607431768211460,
        340282366920938463463374607431768211461,
        340282366920938463463374607431768211462,
        340282366920938463463374607431768211463,
        340282366920938463463374607431768211464,
        340282366920938463463374607431768211465,
    ]
    actual = contract.generate_token_ids(token_type=1, nb_tokens=10)
    assert expected_a == actual
    expected_b = [
        680564733841876926926749214863536422912,
        680564733841876926926749214863536422913,
    ]
    actual = contract.generate_token_ids(token_type=2, nb_tokens=2)
    assert expected_b == actual
    tx = contract.get_deploy_transaction(
        ledger_api=ledger_api, deployer_address=ETHEREUM_ADDRESS_ONE
    )
    assert len(tx) == 6
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [key in tx for key in ["value", "from", "gas", "gasPrice", "nonce"]]
    ), "Error, found: {}".format(tx)
    tx = contract.get_create_batch_transaction(
        ledger_api=ledger_api,
        contract_address=ETHEREUM_ADDRESS_ONE,
        deployer_address=ETHEREUM_ADDRESS_ONE,
        token_ids=expected_a,
    )
    assert len(tx) == 7
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [key in tx for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]]
    ), "Error, found: {}".format(tx)
    tx = contract.get_create_single_transaction(
        ledger_api=ledger_api,
        contract_address=ETHEREUM_ADDRESS_ONE,
        deployer_address=ETHEREUM_ADDRESS_ONE,
        token_id=expected_b[0],
    )
    assert len(tx) == 7
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [key in tx for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]]
    ), "Error, found: {}".format(tx)
    mint_quantities = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    tx = contract.get_mint_batch_transaction(
        ledger_api=ledger_api,
        contract_address=ETHEREUM_ADDRESS_ONE,
        deployer_address=ETHEREUM_ADDRESS_ONE,
        recipient_address=ETHEREUM_ADDRESS_ONE,
        token_ids=expected_a,
        mint_quantities=mint_quantities,
    )
    assert len(tx) == 7
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [key in tx for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]]
    ), "Error, found: {}".format(tx)
    mint_quantity = 1
    tx = contract.get_mint_single_transaction(
        ledger_api=ledger_api,
        contract_address=ETHEREUM_ADDRESS_ONE,
        deployer_address=ETHEREUM_ADDRESS_ONE,
        recipient_address=ETHEREUM_ADDRESS_ONE,
        token_id=expected_b[1],
        mint_quantity=mint_quantity,
    )
    assert len(tx) == 7
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [key in tx for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]]
    ), "Error, found: {}".format(tx)


@pytest.mark.integration
@pytest.mark.ledger
def test_get_single_atomic_swap(ledger_api, crypto_api, erc1155_contract):
    """Test get single atomic swap."""
    contract, contract_address = erc1155_contract
    from_address = ETHEREUM_ADDRESS_ONE
    to_address = ETHEREUM_ADDRESS_TWO
    token_id = contract.generate_token_ids(token_type=2, nb_tokens=1)[0]
    from_supply = 0
    to_supply = 10
    value = 1
    trade_nonce = 1
    tx_hash = contract.get_hash_single(
        ledger_api,
        contract_address,
        from_address,
        to_address,
        token_id,
        from_supply,
        to_supply,
        value,
        trade_nonce,
    )
    assert isinstance(tx_hash, bytes)
    signature = crypto_api.sign_message(tx_hash)
    tx = contract.get_atomic_swap_single_transaction(
        ledger_api=ledger_api,
        contract_address=contract_address,
        from_address=from_address,
        to_address=to_address,
        token_id=token_id,
        from_supply=from_supply,
        to_supply=to_supply,
        value=value,
        trade_nonce=trade_nonce,
        signature=signature,
    )
    assert len(tx) == 8
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [
            key in tx
            for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to", "from"]
        ]
    ), "Error, found: {}".format(tx)


@pytest.mark.integration
@pytest.mark.ledger
def test_get_batch_atomic_swap(ledger_api, crypto_api, erc1155_contract):
    """Test get batch atomic swap."""
    contract, contract_address = erc1155_contract
    from_address = ETHEREUM_ADDRESS_ONE
    to_address = ETHEREUM_ADDRESS_TWO
    token_ids = contract.generate_token_ids(token_type=2, nb_tokens=10)
    from_supplies = [0, 1, 0, 0, 1, 0, 0, 0, 0, 1]
    to_supplies = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    value = 1
    trade_nonce = 1
    tx_hash = contract.get_hash_batch(
        ledger_api,
        contract_address,
        from_address,
        to_address,
        token_ids,
        from_supplies,
        to_supplies,
        value,
        trade_nonce,
    )
    assert isinstance(tx_hash, bytes)
    signature = crypto_api.sign_message(tx_hash)
    tx = contract.get_atomic_swap_batch_transaction(
        ledger_api=ledger_api,
        contract_address=contract_address,
        from_address=from_address,
        to_address=to_address,
        token_ids=token_ids,
        from_supplies=from_supplies,
        to_supplies=to_supplies,
        value=value,
        trade_nonce=trade_nonce,
        signature=signature,
    )
    assert len(tx) == 8
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [
            key in tx
            for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to", "from"]
        ]
    ), "Error, found: {}".format(tx)


class TestCosmWasmContract:
    """Test the cosmwasm contract."""

    def setup(self):
        """Setup."""
        self.ledger_api = ledger_apis_registry.make(
            FetchAICrypto.identifier, **FETCHAI_TESTNET_CONFIG
        )
        self.faucet_api = faucet_apis_registry.make(FetchAICrypto.identifier)
        self.deployer_crypto = crypto_registry.make(FetchAICrypto.identifier)
        self.item_owner_crypto = crypto_registry.make(FetchAICrypto.identifier)

        # Test tokens IDs
        self.token_ids_a = [
            340282366920938463463374607431768211456,
            340282366920938463463374607431768211457,
            340282366920938463463374607431768211458,
            340282366920938463463374607431768211459,
            340282366920938463463374607431768211460,
            340282366920938463463374607431768211461,
            340282366920938463463374607431768211462,
            340282366920938463463374607431768211463,
            340282366920938463463374607431768211464,
            340282366920938463463374607431768211465,
        ]

        self.token_id_b = 680564733841876926926749214863536422912

        # Refill deployer account from faucet
        self.refill_from_faucet(
            self.ledger_api, self.faucet_api, self.deployer_crypto.address
        )

        # Refill item owner account from faucet
        self.refill_from_faucet(
            self.ledger_api, self.faucet_api, self.item_owner_crypto.address
        )
        self.set_contract()

    def refill_from_faucet(self, ledger_api, faucet_api, address):
        """Refill from faucet."""
        start_balance = ledger_api.get_balance(address)

        faucet_api.get_wealth(address)

        tries = 15
        while tries > 0:
            tries -= 1
            time.sleep(1)

            balance = ledger_api.get_balance(address)
            if balance != start_balance:
                break

    def sign_send_verify_handle_transaction(self, tx: Dict[str, str], sender_crypto):
        """
        Sign, send and verify if HandleMsg transaction was successful.

        :param tx: the transaction
        :param sender_crypto: Crypto to sign transaction with
        :return: Nothing - asserts pass if transaction is successful
        """

        signed_tx = sender_crypto.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(signed_tx)
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_hash)
        assert len(tx_receipt) == 8
        assert self.ledger_api.is_transaction_settled(tx_receipt), tx_receipt["raw_log"]

    def set_contract(self):
        """Set contract."""
        directory = Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")
        configuration = load_component_configuration(ComponentType.CONTRACT, directory)
        configuration._directory = directory
        configuration = cast(ContractConfig, configuration)

        if str(configuration.public_id) not in contract_registry.specs:
            # load contract into sys modules
            Contract.from_config(configuration)

        self.contract = contract_registry.make(str(configuration.public_id))

    def deploy_contract(self):
        """Deploy contract."""
        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=self.deployer_crypto.address,
            gas=2000000,
        )
        assert len(tx) == 6
        signed_tx = self.deployer_crypto.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(signed_tx)
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_hash)
        assert len(tx_receipt) == 9
        assert self.ledger_api.is_transaction_settled(tx_receipt), tx_receipt["raw_log"]

        code_id = self.ledger_api.get_code_id(tx_receipt)

        assert code_id is not None
        assert code_id == self.ledger_api.get_last_code_id()
        self.code_id = code_id

        # Init contract
        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=self.deployer_crypto.address,
            code_id=self.code_id,
            init_msg={},
            tx_fee=0,
            amount=0,
            label="ERC1155",
            gas=1000000,
        )
        assert len(tx) == 6
        signed_tx = self.deployer_crypto.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(signed_tx)
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_hash)
        assert len(tx_receipt) == 9
        assert self.ledger_api.is_transaction_settled(tx_receipt), tx_receipt["raw_log"]

        contract_address = self.ledger_api.get_contract_address(tx_receipt)

        assert contract_address is not None
        assert contract_address == self.ledger_api.get_last_contract_address(
            self.code_id
        )
        self.contract_address = contract_address

    @pytest.mark.integration
    @pytest.mark.ledger
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_cosmwasm_contract_deploy_and_interact(self):
        """Test cosmwasm contract deploy and interact."""
        self.deploy_contract()

        # Create single token
        tx = self.contract.get_create_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            token_id=self.token_id_b,
        )
        assert len(tx) == 6
        self.sign_send_verify_handle_transaction(tx, self.deployer_crypto)

        # Create batch of tokens
        tx = self.contract.get_create_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            token_ids=self.token_ids_a,
        )
        assert len(tx) == 6
        self.sign_send_verify_handle_transaction(tx, self.deployer_crypto)

        # Mint single token
        tx = self.contract.get_mint_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.item_owner_crypto.address,
            token_id=self.token_id_b,
            mint_quantity=1,
        )
        assert len(tx) == 6
        self.sign_send_verify_handle_transaction(tx, self.deployer_crypto)

        # Get balance of single token
        res = self.contract.get_balance(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            agent_address=self.item_owner_crypto.address,
            token_id=self.token_id_b,
        )
        assert "balance" in res
        assert res["balance"][self.token_id_b] == 1

        # Mint batch of tokens
        tx = self.contract.get_mint_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.item_owner_crypto.address,
            token_ids=self.token_ids_a,
            mint_quantities=[1] * len(self.token_ids_a),
        )
        assert len(tx) == 6
        self.sign_send_verify_handle_transaction(tx, self.deployer_crypto)

        # Get balances of multiple tokens
        res = self.contract.get_balances(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            agent_address=self.item_owner_crypto.address,
            token_ids=self.token_ids_a,
        )

        assert "balances" in res
        assert res["balances"] == {token_id: 1 for token_id in self.token_ids_a}

    @pytest.mark.integration
    @pytest.mark.ledger
    def test_cosmwasm_unimplemented_exception_single_atomic_swap(self):
        """Test unimplemented exception single atomic swap."""
        pytest.raises(
            NotImplementedError,
            self.contract.get_atomic_swap_single_transaction,
            self.ledger_api,
            contract_address=None,
            from_address=None,
            to_address=None,
            token_id=0,
            from_supply=0,
            to_supply=0,
            value=0,
            trade_nonce=0,
            signature="",
        )

    @pytest.mark.integration
    @pytest.mark.ledger
    def test_cosmwasm_unimplemented_exception_batch_atomic_swap(self):
        """Test unimplemented exception batch atomic swap."""
        pytest.raises(
            NotImplementedError,
            self.contract.get_atomic_swap_batch_transaction,
            self.ledger_api,
            contract_address=None,
            from_address=None,
            to_address=None,
            token_ids=[0],
            from_supplies=[0],
            to_supplies=[0],
            value=0,
            trade_nonce=0,
            signature="",
        )
