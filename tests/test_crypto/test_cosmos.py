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

"""This module contains the tests of the ethereum module."""
import logging
import time
from unittest.mock import MagicMock

import pytest

from aea.crypto.cosmos import CosmosApi, CosmosCrypto, CosmosFaucetApi

from tests.conftest import (
    COSMOS_PRIVATE_KEY_PATH,
    COSMOS_TESTNET_CONFIG,
    MAX_FLAKY_RERUNS,
)


def test_creation():
    """Test the creation of the crypto_objects."""
    assert CosmosCrypto(), "Did not manage to initialise the crypto module"
    assert CosmosCrypto(
        COSMOS_PRIVATE_KEY_PATH
    ), "Did not manage to load the cosmos private key"


def test_initialization():
    """Test the initialisation of the variables."""
    account = CosmosCrypto()
    assert account.entity is not None, "The property must return the account."
    assert (
        account.address is not None
    ), "After creation the display address must not be None"
    assert (
        account.public_key is not None
    ), "After creation the public key must no be None"


def test_sign_and_recover_message():
    """Test the signing and the recovery of a message."""
    account = CosmosCrypto(COSMOS_PRIVATE_KEY_PATH)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = CosmosApi.recover_message(
        message=b"hello", signature=sign_bytes
    )
    assert (
        account.address in recovered_addresses
    ), "Failed to recover the correct address."


def test_get_hash():
    """Test the get hash functionality."""
    expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    hash_ = CosmosApi.get_hash(message=b"hello")
    assert expected_hash == hash_


def test_dump_positive():
    """Test dump."""
    account = CosmosCrypto(COSMOS_PRIVATE_KEY_PATH)
    account.dump(MagicMock())


def test_api_creation():
    """Test api instantiation."""
    assert CosmosApi(**COSMOS_TESTNET_CONFIG), "Failed to initialise the api"


def test_api_none():
    """Test the "api" of the cryptoApi is none."""
    cosmos_api = CosmosApi(**COSMOS_TESTNET_CONFIG)
    assert cosmos_api.api is None, "The api property is not None."


def test_generate_nonce():
    """Test generate nonce."""
    nonce = CosmosApi.generate_tx_nonce(
        seller="some_seller_addr", client="some_buyer_addr"
    )
    assert len(nonce) > 0 and int(
        nonce, 16
    ), "The len(nonce) must not be 0 and must be hex"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_construct_sign_and_submit_transfer_transaction():
    """Test the construction, signing and submitting of a transfer transaction."""
    account = CosmosCrypto(COSMOS_PRIVATE_KEY_PATH)
    cc2 = CosmosCrypto()
    cosmos_api = CosmosApi(**COSMOS_TESTNET_CONFIG)

    amount = 10000
    transfer_transaction = cosmos_api.get_transfer_transaction(
        sender_address=account.address,
        destination_address=cc2.address,
        amount=amount,
        tx_fee=1000,
        tx_nonce="something",
    )
    assert (
        isinstance(transfer_transaction, dict) and len(transfer_transaction) == 6
    ), "Incorrect transfer_transaction constructed."

    signed_transaction = account.sign_transaction(transfer_transaction)
    assert (
        isinstance(signed_transaction, dict)
        and len(signed_transaction["tx"]) == 4
        and isinstance(signed_transaction["tx"]["signatures"], list)
    ), "Incorrect signed_transaction constructed."

    transaction_digest = cosmos_api.send_signed_transaction(signed_transaction)
    assert transaction_digest is not None, "Failed to submit transfer transaction!"

    not_settled = True
    elapsed_time = 0
    while not_settled and elapsed_time < 20:
        elapsed_time += 1
        time.sleep(2)
        transaction_receipt = cosmos_api.get_transaction_receipt(transaction_digest)
        if transaction_receipt is None:
            continue
        is_settled = cosmos_api.is_transaction_settled(transaction_receipt)
        not_settled = not is_settled
    assert transaction_receipt is not None, "Failed to retrieve transaction receipt."
    assert is_settled, "Failed to verify tx!"

    tx = cosmos_api.get_transaction(transaction_digest)
    is_valid = cosmos_api.is_transaction_valid(
        tx, cc2.address, account.address, "", amount
    )
    assert is_valid, "Failed to settle tx correctly!"
    assert tx == transaction_receipt, "Should be same!"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_balance():
    """Test the balance is zero for a new account."""
    cosmos_api = CosmosApi(**COSMOS_TESTNET_CONFIG)
    cc = CosmosCrypto()
    balance = cosmos_api.get_balance(cc.address)
    assert balance == 0, "New account has a positive balance."
    cc = CosmosCrypto(private_key_path=COSMOS_PRIVATE_KEY_PATH)
    balance = cosmos_api.get_balance(cc.address)
    assert balance > 0, "Existing account has no balance."


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_wealth_positive(caplog):
    """Test the balance is zero for a new account."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.cosmos"):
        cosmos_faucet_api = CosmosFaucetApi()
        cc = CosmosCrypto()
        cosmos_faucet_api.get_wealth(cc.address)
        assert "Wealth generated" in caplog.text


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_format_default():
    """Test if default CosmosSDK transaction is correctly formated."""
    account = CosmosCrypto(COSMOS_PRIVATE_KEY_PATH)
    cc2 = CosmosCrypto()
    cosmos_api = CosmosApi(**COSMOS_TESTNET_CONFIG)

    amount = 10000

    transfer_transaction = cosmos_api.get_transfer_transaction(
        sender_address=account.address,
        destination_address=cc2.address,
        amount=amount,
        tx_fee=1000,
        tx_nonce="something",
    )

    signed_transaction = cc2.sign_transaction(transfer_transaction)

    assert "tx" in signed_transaction
    assert "signatures" in signed_transaction["tx"]
    assert len(signed_transaction["tx"]["signatures"]) == 1

    assert "pub_key" in signed_transaction["tx"]["signatures"][0]
    assert "value" in signed_transaction["tx"]["signatures"][0]["pub_key"]
    base64_pbk = signed_transaction["tx"]["signatures"][0]["pub_key"]["value"]

    assert "signature" in signed_transaction["tx"]["signatures"][0]
    signature = signed_transaction["tx"]["signatures"][0]["signature"]

    default_formated_transaction = cc2.format_default_transaction(
        transfer_transaction, signature, base64_pbk
    )

    # Compare default formatted transaction with signed transaction
    assert signed_transaction == default_formated_transaction


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_format_cosmwasm():
    """Test if CosmWasm transaction is correctly formated."""
    cc2 = CosmosCrypto()

    # Dummy CosmWasm transaction
    wasm_transaction = {
        "account_number": "8",
        "chain_id": "agent-land",
        "fee": {"amount": [], "gas": "200000"},
        "memo": "",
        "msgs": [
            {
                "type": "wasm/execute",
                "value": {
                    "sender": "cosmos14xjnl2mwwfz6pztpwzj6s89npxr0e3lhxl52nv",
                    "contract": "cosmos1xzlgeyuuyqje79ma6vllregprkmgwgav5zshcm",
                    "msg": {
                        "create_single": {
                            "item_owner": "cosmos1fz0dcvvqv5at6dl39804jy92lnndf3d5saalx6",
                            "id": "1234",
                            "path": "SOME_URI",
                        }
                    },
                    "sent_funds": [],
                },
            }
        ],
        "sequence": "25",
    }

    signed_transaction = cc2.sign_transaction(wasm_transaction)

    assert "value" in signed_transaction
    assert "signatures" in signed_transaction["value"]
    assert len(signed_transaction["value"]["signatures"]) == 1

    assert "pub_key" in signed_transaction["value"]["signatures"][0]
    assert "value" in signed_transaction["value"]["signatures"][0]["pub_key"]
    base64_pbk = signed_transaction["value"]["signatures"][0]["pub_key"]["value"]

    assert "signature" in signed_transaction["value"]["signatures"][0]
    signature = signed_transaction["value"]["signatures"][0]["signature"]

    wasm_formated_transaction = cc2.format_wasm_transaction(
        wasm_transaction, signature, base64_pbk
    )

    # Compare Wasm formatted transaction with signed transaction
    assert signed_transaction == wasm_formated_transaction
