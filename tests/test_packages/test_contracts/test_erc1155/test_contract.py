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

import json
import time

import pytest

from aea.crypto.registries import crypto_registry, faucet_apis_registry, ledger_apis_registry

from tests.conftest import (
    COSMOS,
    COSMOS_TESTNET_CONFIG,
    ETHEREUM,
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_ADDRESS_TWO,
    ETHEREUM_TESTNET_CONFIG,
)

ledger = [
    (ETHEREUM, ETHEREUM_TESTNET_CONFIG),
]

crypto = [
    (ETHEREUM,),
]

cosmos_ledger = [
    (COSMOS, COSMOS_TESTNET_CONFIG),
]

cosmos_crypto = [
    (COSMOS,)
]


@pytest.fixture(params=ledger)
def ledger_api(request):
    ledger_id, config = request.param
    api = ledger_apis_registry.make(ledger_id, **config)
    yield api


@pytest.fixture(params=crypto)
def crypto_api(request):
    crypto_id = request.param[0]
    api = crypto_registry.make(crypto_id)
    yield api


@pytest.mark.integration
@pytest.mark.ledger
def test_helper_methods_and_get_transactions(ledger_api, erc1155_contract):
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
    actual = erc1155_contract.generate_token_ids(token_type=1, nb_tokens=10)
    assert expected_a == actual
    expected_b = [
        680564733841876926926749214863536422912,
        680564733841876926926749214863536422913,
    ]
    actual = erc1155_contract.generate_token_ids(token_type=2, nb_tokens=2)
    assert expected_b == actual
    tx = erc1155_contract.get_deploy_transaction(
        ledger_api=ledger_api, deployer_address=ETHEREUM_ADDRESS_ONE
    )
    assert len(tx) == 6
    data = tx.pop("data")
    assert len(data) > 0 and data.startswith("0x")
    assert all(
        [key in tx for key in ["value", "from", "gas", "gasPrice", "nonce"]]
    ), "Error, found: {}".format(tx)
    tx = erc1155_contract.get_create_batch_transaction(
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
    tx = erc1155_contract.get_create_single_transaction(
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
    tx = erc1155_contract.get_mint_batch_transaction(
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
    tx = erc1155_contract.get_mint_single_transaction(
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
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    from_address = ETHEREUM_ADDRESS_ONE
    to_address = ETHEREUM_ADDRESS_TWO
    token_id = erc1155_contract.generate_token_ids(token_type=2, nb_tokens=1)[0]
    from_supply = 0
    to_supply = 10
    value = 1
    trade_nonce = 1
    tx_hash = erc1155_contract.get_hash_single(
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
    tx = erc1155_contract.get_atomic_swap_single_transaction(
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
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    from_address = ETHEREUM_ADDRESS_ONE
    to_address = ETHEREUM_ADDRESS_TWO
    token_ids = erc1155_contract.generate_token_ids(token_type=2, nb_tokens=10)
    from_supplies = [0, 1, 0, 0, 1, 0, 0, 0, 0, 1]
    to_supplies = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    value = 1
    trade_nonce = 1
    tx_hash = erc1155_contract.get_hash_batch(
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
    tx = erc1155_contract.get_atomic_swap_batch_transaction(
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


@pytest.fixture(params=cosmos_ledger)
def cosmos_ledger_api(request):
    ledger_id, config = request.param
    api = ledger_apis_registry.make(ledger_id, **config)
    yield api


@pytest.fixture(params=cosmos_crypto)
def deployer_cosmos_crypto_api(request):
    crypto_id = request.param[0]
    api = crypto_registry.make(crypto_id)
    yield api


@pytest.fixture(params=cosmos_crypto)
def item_owner_cosmos_crypto_api(request):
    crypto_id = request.param[0]
    api = crypto_registry.make(crypto_id)
    yield api


@pytest.fixture(params=cosmos_crypto)
def cosmos_faucet_api(request):
    item_id = request.param[0]
    api = faucet_apis_registry.make(item_id)
    yield api


def refill_from_faucet(ledger_api, faucet_api, address):
    start_balance = ledger_api.get_balance(address)

    faucet_api.get_wealth(address)

    tries = 10
    while tries > 0:
        tries -= 1
        time.sleep(1)

        balance = ledger_api.get_balance(address)
        if balance != start_balance:
            break


@pytest.mark.integration
@pytest.mark.ledger
def test_cosmwasm_get_transactions(cosmos_ledger_api, deployer_cosmos_crypto_api, item_owner_cosmos_crypto_api,
                                   erc1155_contract, cosmos_faucet_api):
    token_ids_a = [
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

    token_id_b = 680564733841876926926749214863536422912

    # Refill deployer account from faucet
    refill_from_faucet(cosmos_ledger_api, cosmos_faucet_api, deployer_cosmos_crypto_api.address)

    # Refill item owner account from faucet
    refill_from_faucet(cosmos_ledger_api, cosmos_faucet_api, item_owner_cosmos_crypto_api.address)

    # Deploy contract
    tx = erc1155_contract.get_deploy_transaction(
        ledger_api=cosmos_ledger_api, deployer_address=deployer_cosmos_crypto_api.address, gas=900000
    )
    assert len(tx) == 6
    signed_tx = deployer_cosmos_crypto_api.sign_transaction(tx)
    receipt = json.loads(cosmos_ledger_api.send_signed_transaction(signed_tx))
    assert len(receipt) == 7
    assert all(
        [
            key in receipt
            for key in ["height", "txhash", "data", "raw_log", "logs", "gas_wanted", "gas_used"]
        ])

    code_id = cosmos_ledger_api.get_last_code_id()

    # Init contract
    tx = cosmos_ledger_api.get_init_transaction(deployer_cosmos_crypto_api.address, code_id, {}, 0, 0, label="ERC1155")
    signed_tx = deployer_cosmos_crypto_api.sign_transaction(tx)
    receipt = json.loads(cosmos_ledger_api.send_signed_transaction(signed_tx))
    assert len(receipt) == 7
    assert all(
        [
            key in receipt
            for key in ["height", "txhash", "data", "raw_log", "logs", "gas_wanted", "gas_used"]
        ])

    contract_address = cosmos_ledger_api.get_contract_address(code_id)

    # Create single token
    tx = erc1155_contract.get_create_single_transaction(
        ledger_api=cosmos_ledger_api,
        contract_address=contract_address,
        deployer_address=deployer_cosmos_crypto_api.address,
        token_id=token_id_b,
    )
    assert len(tx) == 6
    signed_tx = deployer_cosmos_crypto_api.sign_transaction(tx)
    receipt = json.loads(cosmos_ledger_api.send_signed_transaction(signed_tx))
    assert len(receipt) == 6
    assert all(
        [
            key in receipt
            for key in ["height", "txhash", "raw_log", "logs", "gas_wanted", "gas_used"]
        ])

    # Create batch of tokens
    tx = erc1155_contract.get_create_batch_transaction(
        ledger_api=cosmos_ledger_api,
        contract_address=contract_address,
        deployer_address=deployer_cosmos_crypto_api.address,
        token_ids=token_ids_a,
    )
    assert len(tx) == 6
    signed_tx = deployer_cosmos_crypto_api.sign_transaction(tx)
    receipt = json.loads(cosmos_ledger_api.send_signed_transaction(signed_tx))
    assert len(receipt) == 6
    assert all(
        [
            key in receipt
            for key in ["height", "txhash", "raw_log", "logs", "gas_wanted", "gas_used"]
        ])

    # Mint single token
    tx = erc1155_contract.get_mint_single_transaction(
        ledger_api=cosmos_ledger_api,
        contract_address=contract_address,
        deployer_address=deployer_cosmos_crypto_api.address,
        recipient_address=item_owner_cosmos_crypto_api.address,
        token_id=token_id_b,
        mint_quantity=1
    )
    assert len(tx) == 6
    signed_tx = deployer_cosmos_crypto_api.sign_transaction(tx)
    receipt = json.loads(cosmos_ledger_api.send_signed_transaction(signed_tx))
    assert len(receipt) == 6
    assert all(
        [
            key in receipt
            for key in ["height", "txhash", "raw_log", "logs", "gas_wanted", "gas_used"]
        ])

    # Get balance of single token
    res = erc1155_contract.get_balance(
        ledger_api=cosmos_ledger_api,
        contract_address=contract_address,
        agent_address=item_owner_cosmos_crypto_api.address,
        token_id=token_id_b,
    )
    assert "balance" in res
    assert res["balance"] == '1'

    # Mint batch of tokens
    tx = erc1155_contract.get_mint_batch_transaction(
        ledger_api=cosmos_ledger_api,
        contract_address=contract_address,
        deployer_address=deployer_cosmos_crypto_api.address,
        recipient_address=item_owner_cosmos_crypto_api.address,
        token_ids=token_ids_a,
        mint_quantities=[1] * len(token_ids_a)
    )
    assert len(tx) == 6
    signed_tx = deployer_cosmos_crypto_api.sign_transaction(tx)
    receipt = json.loads(cosmos_ledger_api.send_signed_transaction(signed_tx))
    assert len(receipt) == 6
    assert all(
        [
            key in receipt
            for key in ["height", "txhash", "raw_log", "logs", "gas_wanted", "gas_used"]
        ])

    # Get balances of multiple tokens
    res = erc1155_contract.get_balances(
        ledger_api=cosmos_ledger_api,
        contract_address=contract_address,
        agent_address=item_owner_cosmos_crypto_api.address,
        token_ids=token_ids_a,
    )
    assert "balances" in res
    assert res["balances"] == ['1'] * len(token_ids_a)
