# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

import hashlib
import logging
import math
import random
import tempfile
import time
from pathlib import Path
from typing import Dict, cast
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from aea_ledger_ethereum import (
    AttributeDictTranslator,
    EthereumApi,
    EthereumCrypto,
    EthereumFaucetApi,
    EthereumHelper,
    LruLockWrapper,
    get_gas_price_strategy,
    get_gas_price_strategy_eip1559,
    requests,
    rpc_gas_price_strategy_wrapper,
)
from aea_ledger_ethereum.ethereum import (
    DEFAULT_EIP1559_STRATEGY,
    DEFAULT_GAS_STATION_STRATEGY,
)
from web3 import Web3
from web3._utils.request import _session_cache as session_cache

from aea.crypto.helpers import DecryptError, KeyIsIncorrect

from tests.conftest import DEFAULT_GANACHE_CHAIN_ID, MAX_FLAKY_RERUNS, ROOT_DIR


def get_default_gas_strategies() -> Dict:
    """Returns default gas price strategy."""
    return {
        "default_gas_price_strategy": "eip1559",
        "gas_price_strategies": {
            "gas_station": DEFAULT_GAS_STATION_STRATEGY,
            "eip1559": DEFAULT_EIP1559_STRATEGY,
        },
    }


def get_history_data(n_blocks: int, base_multiplier: int = 100) -> Dict:
    """Returns dummy blockchain history data."""

    return {
        "oldestBlock": 1,
        "reward": [
            math.ceil(random.random() * base_multiplier) * 1e1 for _ in range(n_blocks)
        ],
        "baseFeePerGas": [
            math.ceil(random.random() * base_multiplier) * 1e9 for _ in range(n_blocks)
        ],
    }


def test_attribute_dict_translator():
    """Test the AttributeDictTranslator."""
    di = {
        "1": None,
        "2": True,
        "3": b"some",
        "4": 0.1,
        "5": [1, None, True, {}],
        "6": {"hex": "0x01"},
    }
    res = AttributeDictTranslator.from_dict(di)
    assert AttributeDictTranslator.to_dict(res) == di


def test_creation(ethereum_private_key_file):
    """Test the creation of the crypto_objects."""
    assert EthereumCrypto(), "Managed to initialise the eth_account"
    assert EthereumCrypto(
        ethereum_private_key_file
    ), "Managed to load the eth private key"


def test_initialization():
    """Test the initialisation of the variables."""
    account = EthereumCrypto()
    assert account.entity is not None, "The property must return the account."
    assert (
        account.address is not None and type(account.address) == str
    ), "After creation the display address must not be None"
    assert (
        account.public_key is not None and type(account.public_key) == str
    ), "After creation the public key must no be None"
    assert account.entity is not None, "After creation the entity must no be None"


def test_derive_address():
    """Test the get_address_from_public_key method"""
    account = EthereumCrypto()
    address = EthereumApi.get_address_from_public_key(account.public_key)
    assert account.address == address, "Address derivation incorrect"


def test_sign_and_recover_message(ethereum_private_key_file):
    """Test the signing and the recovery function for the eth_crypto."""
    account = EthereumCrypto(ethereum_private_key_file)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = EthereumApi.recover_message(
        message=b"hello", signature=sign_bytes
    )
    assert len(recovered_addresses) == 1, "Wrong number of addresses recovered."
    assert (
        recovered_addresses[0] == account.address
    ), "Failed to recover the correct address."


def test_sign_and_recover_message_deprecated(ethereum_private_key_file):
    """Test the signing and the recovery function for the eth_crypto."""
    account = EthereumCrypto(ethereum_private_key_file)
    message = b"hello"
    message_hash = hashlib.sha256(message).digest()
    sign_bytes = account.sign_message(message=message_hash, is_deprecated_mode=True)
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = EthereumApi.recover_message(
        message=message_hash, signature=sign_bytes, is_deprecated_mode=True
    )
    assert len(recovered_addresses) == 1, "Wrong number of addresses recovered."
    assert (
        recovered_addresses[0] == account.address
    ), "Failed to recover the correct address."


def test_sign_and_recover_message_public_key(ethereum_private_key_file):
    """Test the signing and the recovery function for the eth_crypto."""
    account = EthereumCrypto(ethereum_private_key_file)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_public_keys = EthereumApi.recover_public_keys_from_message(
        message=b"hello", signature=sign_bytes
    )
    assert len(recovered_public_keys) == 1, "Wrong number of public keys recovered."
    assert (
        EthereumApi.get_address_from_public_key(recovered_public_keys[0])
        == account.address
    ), "Failed to recover the correct address."


def test_get_hash():
    """Test the get hash functionality."""
    expected_hash = "0x1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8"
    hash_ = EthereumApi.get_hash(message=b"hello")
    assert expected_hash == hash_


def test_dump_positive(ethereum_private_key_file):
    """Test dump."""
    account = EthereumCrypto(ethereum_private_key_file)
    account.dump(MagicMock())


def test_api_creation(ethereum_testnet_config):
    """Test api instantiation."""
    assert EthereumApi(**ethereum_testnet_config), "Failed to initialise the api"


def test_api_none(ethereum_testnet_config):
    """Test the "api" of the cryptoApi is none."""
    eth_api = EthereumApi(**ethereum_testnet_config)
    assert eth_api.api is not None, "The api property is None."


def test_validate_address():
    """Test the is_valid_address functionality."""
    account = EthereumCrypto()
    assert EthereumApi.is_valid_address(account.address)
    assert not EthereumApi.is_valid_address(account.address + "wrong")


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_balance(ethereum_testnet_config, ganache, ethereum_private_key_file):
    """Test the balance is zero for a new account."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    ec = EthereumCrypto()
    balance = ethereum_api.get_balance(ec.address)
    assert balance == 0, "New account has a positive balance."
    ec = EthereumCrypto(private_key_path=ethereum_private_key_file)
    balance = ethereum_api.get_balance(ec.address)
    assert balance > 0, "Existing account has no balance."


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_state(ethereum_testnet_config, ganache):
    """Test that get_state() with 'get_block' function returns something containing the block number."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    callable_name = "get_block"
    args = ("latest",)
    block = ethereum_api.get_state(callable_name, *args)
    assert block is not None, "response to get_block is empty."
    assert "number" in block, "response to get_block() does not contain 'number'"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_construct_sign_and_submit_transfer_transaction(
    ethereum_testnet_config, ganache, ethereum_private_key_file
):
    """Test the construction, signing and submitting of a transfer transaction."""
    account = EthereumCrypto(private_key_path=ethereum_private_key_file)
    ec2 = EthereumCrypto()
    ethereum_api = EthereumApi(**ethereum_testnet_config)

    amount = 40000
    tx_nonce = ethereum_api.generate_tx_nonce(ec2.address, account.address)
    max_priority_fee_per_gas = 1_000_000_000
    max_fee_per_gas = 1_000_000_000
    transfer_transaction = ethereum_api.get_transfer_transaction(
        sender_address=account.address,
        destination_address=ec2.address,
        amount=amount,
        tx_fee=30000,
        tx_nonce=tx_nonce,
        chain_id=DEFAULT_GANACHE_CHAIN_ID,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
        max_fee_per_gas=max_fee_per_gas,
    )
    assert (
        isinstance(transfer_transaction, dict) and len(transfer_transaction) == 8
    ), "Incorrect transfer_transaction constructed."

    signed_transaction = account.sign_transaction(transfer_transaction)
    assert (
        isinstance(signed_transaction, dict) and len(signed_transaction) == 5
    ), "Incorrect signed_transaction constructed."

    transaction_digest = ethereum_api.send_signed_transaction(signed_transaction)
    assert transaction_digest is not None, "Failed to submit transfer transaction!"

    not_settled = True
    elapsed_time = 0
    while not_settled and elapsed_time < 20:
        elapsed_time += 1
        time.sleep(2)
        transaction_receipt = ethereum_api.get_transaction_receipt(transaction_digest)
        if transaction_receipt is None:
            continue
        is_settled = ethereum_api.is_transaction_settled(transaction_receipt)
        not_settled = not is_settled
    assert transaction_receipt is not None, "Failed to retrieve transaction receipt."
    assert is_settled, "Failed to verify tx!"

    tx = ethereum_api.get_transaction(transaction_digest)
    is_valid = ethereum_api.is_transaction_valid(
        tx, ec2.address, account.address, tx_nonce, amount
    )
    assert is_valid, "Failed to settle tx correctly!"
    assert tx != transaction_receipt, "Should not be same!"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_wealth_positive(caplog):
    """Test the balance is zero for a new account."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.ethereum._default_logger"):
        ethereum_faucet_api = EthereumFaucetApi()
        ec = EthereumCrypto()
        ethereum_faucet_api.get_wealth(ec.address, "some_url")
        assert (
            "Invalid URL" in caplog.text
        ), f"Cannot find message in output: {caplog.text}"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_deploy_transaction(ethereum_testnet_config, ganache):
    """Test the get deploy transaction method."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    ec2 = EthereumCrypto()
    interface = {"abi": [], "bytecode": b""}
    max_priority_fee_per_gas = 1000000000
    max_fee_per_gas = 1000000000
    deploy_tx = ethereum_api.get_deploy_transaction(
        contract_interface=interface,
        deployer_address=ec2.address,
        value=0,
        max_priority_fee_per_gas=max_priority_fee_per_gas,
        max_fee_per_gas=max_fee_per_gas,
    )
    assert type(deploy_tx) == dict and len(deploy_tx) == 8
    assert all(
        key
        in [
            "from",
            "value",
            "gas",
            "nonce",
            "data",
            "maxPriorityFeePerGas",
            "maxFeePerGas",
            "chainId",
        ]
        for key in deploy_tx.keys()
    )


def test_load_contract_interface():
    """Test the load_contract_interface method."""
    path = Path(ROOT_DIR, "tests", "data", "dummy_contract", "build", "some.json")
    result = EthereumApi.load_contract_interface(path)
    assert "abi" in result
    assert "bytecode" in result


@patch.object(EthereumApi, "_try_get_transaction_count", return_value=None)
def test_ethereum_api_get_transfer_transaction(*args):
    """Test EthereumApi.get_transfer_transaction."""
    ec1 = EthereumCrypto()
    ec2 = EthereumCrypto()
    ethereum_api = EthereumApi(**get_default_gas_strategies())
    args = {
        "sender_address": ec1.address,
        "destination_address": ec2.address,
        "amount": 1,
        "tx_fee": 0,
        "tx_nonce": "",
        "max_fee_per_gas": 20,
    }
    assert ethereum_api.get_transfer_transaction(**args) is None


@patch.object(EthereumApi, "_try_get_transaction_count", return_value=1)
@patch.object(EthereumApi, "_try_get_max_priority_fee", return_value=1)
def test_ethereum_api_get_transfer_transaction_2(*args):
    """Test EthereumApi.get_transfer_transaction."""
    ec1 = EthereumCrypto()
    ec2 = EthereumCrypto()
    ethereum_api = EthereumApi(**get_default_gas_strategies())
    ethereum_api._is_gas_estimation_enabled = True
    args = {
        "sender_address": ec1.address,
        "destination_address": ec2.address,
        "amount": 1,
        "tx_fee": 0,
        "tx_nonce": "",
        "max_fee_per_gas": 10,
    }
    with patch.object(ethereum_api.api.eth, "estimate_gas", return_value=1):
        assert len(ethereum_api.get_transfer_transaction(**args)) == 8


@patch.object(EthereumApi, "_try_get_transaction_count", return_value=1)
def test_ethereum_api_get_transfer_transaction_3(*args):
    """Test EthereumApi.get_transfer_transaction."""
    ec1 = EthereumCrypto()
    ec2 = EthereumCrypto()
    ethereum_api = EthereumApi(**get_default_gas_strategies())
    ethereum_api._is_gas_estimation_enabled = True
    args = {
        "sender_address": ec1.address,
        "destination_address": ec2.address,
        "amount": 1,
        "tx_fee": 0,
        "tx_nonce": "",
        "max_fee_per_gas": 10,
    }
    with patch.object(ethereum_api.api.eth, "_max_priority_fee", return_value=1):
        assert len(ethereum_api.get_transfer_transaction(**args)) == 8


def test_ethereum_api_get_deploy_transaction(ethereum_testnet_config):
    """Test EthereumApi.get_deploy_transaction."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    ec1 = EthereumCrypto()
    with patch.object(ethereum_api.api.eth, "get_transaction_count", return_value=None):
        assert (
            ethereum_api.get_deploy_transaction(
                **{
                    "contract_interface": {"": ""},
                    "deployer_address": ec1.address,
                    "value": 1,
                    "max_fee_per_gas": 10,
                }
            )
            is None
        )


def test_session_cache():
    """Test session cache."""
    assert isinstance(session_cache, LruLockWrapper)

    session_cache[1] = 1
    assert session_cache[1] == 1
    del session_cache[1]
    assert 1 not in session_cache


def test_gas_price_strategy_eip1559() -> None:
    """Test eip1559 based gas price strategy."""

    callable_ = get_gas_price_strategy_eip1559(**DEFAULT_EIP1559_STRATEGY)

    web3 = Web3()
    get_block_mock = mock.patch.object(
        web3.eth, "get_block", return_value={"baseFeePerGas": 150e9, "number": 1}
    )

    fee_history_mock = mock.patch.object(
        web3.eth, "fee_history", return_value=get_history_data(n_blocks=5,),
    )

    with get_block_mock:
        with fee_history_mock:
            gas_stregy = callable_(web3, "tx_params")

    assert all([key in gas_stregy for key in ["maxFeePerGas", "maxPriorityFeePerGas"]])

    assert all([value > 1e8 for value in gas_stregy.values()])


def test_gas_price_strategy_eip1559_estimate_none() -> None:
    """Test eip1559 based gas price strategy."""

    callable_ = get_gas_price_strategy_eip1559(**DEFAULT_EIP1559_STRATEGY)

    web3 = Web3()
    get_block_mock = mock.patch.object(
        web3.eth, "get_block", return_value={"baseFeePerGas": 150e9, "number": 1}
    )

    fee_history_mock = mock.patch.object(
        web3.eth, "fee_history", return_value=get_history_data(n_blocks=5,),
    )
    with get_block_mock:
        with fee_history_mock:
            with mock.patch(
                "aea_ledger_ethereum.ethereum.estimate_priority_fee",
                new_callable=lambda: lambda *args, **kwargs: None,
            ):
                gas_stregy = callable_(web3, "tx_params")

    assert all([key in gas_stregy for key in ["maxFeePerGas", "maxPriorityFeePerGas"]])

    assert gas_stregy["baseFee"] is None


def test_gas_price_strategy_eip1559_fallback() -> None:
    """Test eip1559 based gas price strategy."""

    strategy_kwargs = DEFAULT_EIP1559_STRATEGY.copy()
    strategy_kwargs["max_gas_fast"] = -1

    callable_ = get_gas_price_strategy_eip1559(**strategy_kwargs)
    web3 = Web3()
    get_block_mock = mock.patch.object(
        web3.eth, "get_block", return_value={"baseFeePerGas": 150e9, "number": 1}
    )

    fee_history_mock = mock.patch.object(
        web3.eth, "fee_history", return_value=get_history_data(n_blocks=5,),
    )
    with get_block_mock:
        with fee_history_mock:
            with mock.patch(
                "aea_ledger_ethereum.ethereum.estimate_priority_fee",
                new_callable=lambda: lambda *args, **kwargs: None,
            ):
                gas_stregy = callable_(web3, "tx_params")

    assert all([key in gas_stregy for key in ["maxFeePerGas", "maxPriorityFeePerGas"]])

    assert gas_stregy["baseFee"] is None


def test_gas_price_strategy_eth_gasstation():
    """Test the gas price strategy when using eth gasstation."""
    gas_price_strategy = "fast"
    excepted_result = 10
    callable_ = get_gas_price_strategy(gas_price_strategy, "api_key")
    with patch.object(
        requests,
        "get",
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={gas_price_strategy: excepted_result}),
        ),
    ):
        result = callable_(Web3, "tx_params")
    assert cast(int, result["gasPrice"]) == cast(int, excepted_result / 10 * 1000000000)


def test_gas_price_strategy_not_supported(caplog):
    """Test the gas price strategy when not supported."""
    gas_price_strategy = "superfast"
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.ethereum._default_logger"):
        callable_ = get_gas_price_strategy(gas_price_strategy, "api_key")
    assert callable_ == rpc_gas_price_strategy_wrapper
    assert (
        f"Gas price strategy `{gas_price_strategy}` not in list of supported modes:"
        in caplog.text
    )


def test_gas_price_strategy_no_api_key(caplog):
    """Test the gas price strategy when no api key is provided."""
    gas_price_strategy = "fast"
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.ethereum._default_logger"):
        callable_ = get_gas_price_strategy(gas_price_strategy, None)
    assert callable_ == rpc_gas_price_strategy_wrapper
    assert (
        "No ethgasstation api key provided. Falling back to `rpc_gas_price_strategy`."
        in caplog.text
    )


def test_dump_load_with_password():
    """Test dumping and loading a key with password."""
    with tempfile.TemporaryDirectory() as dirname:
        encrypted_file_name = Path(dirname, "eth_key_encrypted")
        password = "somePwd"  # nosec
        ec = EthereumCrypto()
        ec.dump(encrypted_file_name, password)
        assert encrypted_file_name.exists()
        with pytest.raises(DecryptError, match="Decrypt error! Bad password?"):
            ec2 = EthereumCrypto.load_private_key_from_path(
                encrypted_file_name, "wrongPassw"
            )
        ec2 = EthereumCrypto(encrypted_file_name, password)
        assert ec2.private_key == ec.private_key


def test_load_errors():
    """Test load errors: bad password, no password specified."""
    ec = EthereumCrypto()
    with patch.object(EthereumCrypto, "load", return_value="bad sTring"):
        with pytest.raises(KeyIsIncorrect, match="Try to specify `password`"):
            ec.load_private_key_from_path("any path")

        with pytest.raises(KeyIsIncorrect, match="Wrong password?"):
            ec.load_private_key_from_path("any path", password="some")


def test_decrypt_error():
    """Test bad password error on decrypt."""
    ec = EthereumCrypto()
    ec._pritvate_key = EthereumCrypto.generate_private_key()
    password = "test"
    encrypted_data = ec.encrypt(password=password)
    with pytest.raises(DecryptError, match="Bad password"):
        ec.decrypt(encrypted_data, password + "some")

    with patch(
        "aea_ledger_ethereum.ethereum.Account.decrypt",
        side_effect=ValueError("expected"),
    ):
        with pytest.raises(ValueError, match="expected"):
            ec.decrypt(encrypted_data, password + "some")


def test_helper_get_contract_address():
    """Test EthereumHelper.get_contract_address."""
    assert EthereumHelper.get_contract_address({"contractAddress": "123"}) == "123"
