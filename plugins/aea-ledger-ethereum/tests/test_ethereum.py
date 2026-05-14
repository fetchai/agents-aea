# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2026 Valory AG
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

import copy
import hashlib
import logging
import math
import os
import random
import re
import tempfile
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Generator, Optional, Tuple, Union, cast
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest
from aea_ledger_ethereum import (
    AttributeDictTranslator,
    EthereumApi,
    EthereumCrypto,
    EthereumFaucetApi,
    EthereumHelper,
    get_gas_price_strategy,
    get_gas_price_strategy_eip1559,
    requests,
    rpc_gas_price_strategy_wrapper,
    to_eth_unit,
)
from aea_ledger_ethereum.ethereum import (
    DEFAULT_EIP1559_STRATEGY,
    DEFAULT_FALLBACK_ESTIMATE,
    DEFAULT_GAS_STATION_STRATEGY,
    DEFAULT_GNOSIS_MIN_ALLOWED_TIP,
    DEFAULT_MIN_ALLOWED_TIP,
    EIP1559,
    EIP1559_POLYGON,
    GAS_STATION,
    GWEI,
    TIP_INCREASE,
    estimate_priority_fee,
    get_base_fee_multiplier,
    get_gas_price_strategy_eip1559_polygon,
)
from eth_typing import BlockNumber
from eth_utils.currency import to_wei
from requests import HTTPError
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.exceptions import ContractLogicError
from web3.types import FeeHistory, Wei

from aea.common import JSONLike
from aea.crypto.helpers import DecryptError, KeyIsIncorrect

from tests.conftest import DEFAULT_GANACHE_CHAIN_ID, MAX_FLAKY_RERUNS, ROOT_DIR

RPC_ENV_VAR_PREFIX = "RPC_"


class EIP1559Networks(Enum):
    """The supported networks upgraded with EIP-1559."""

    ETHEREUM = "https://eth.drpc.org"
    ARBITRUM = "https://arb1.arbitrum.io/rpc"
    ZKSYNC = "https://mainnet.era.zksync.io"
    BINANCE = "https://bsc-dataseed1.binance.org"
    GNOSIS = "https://rpc.gnosischain.com"
    CELO = "https://forno.celo.org"
    OPTIMISM = "https://mainnet.optimism.io"
    BASE = "https://mainnet.base.org"
    MODE = "https://mainnet.mode.network"
    POLYGON = "https://polygon.drpc.org"
    FRAXTAL = "https://rpc.frax.com"


def __get_rpc(network: EIP1559Networks) -> str:
    """Get RPC with override from environment variables, or default value."""
    return os.getenv(f"{RPC_ENV_VAR_PREFIX}{network.name}", network.value)


RPCS = {network: __get_rpc(network) for network in EIP1559Networks}


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
            [math.ceil(random.random() * base_multiplier) * 1e9]
            for _ in range(n_blocks)
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


def test_attribute_dict_translator_plain_dict():
    """Test to_dict accepts a plain dict in addition to AttributeDict.

    TxReceipt and TxData are TypedDicts (dict subclasses) so callers may
    legitimately pass plain dicts; both arms of the isinstance guard and
    the recursive _remove_hexbytes path must handle them correctly.
    """
    di = {
        "blockNumber": 42,
        "status": True,
        "data": b"raw",
        "nested": {"value": 99},
    }
    result = AttributeDictTranslator.to_dict(di)
    assert result == {
        "blockNumber": 42,
        "status": True,
        "data": b"raw",
        "nested": {"value": 99},
    }


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
        account.address is not None and type(account.address) is str
    ), "After creation the display address must not be None"
    assert (
        account.public_key is not None and type(account.public_key) is str
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


def test_api_creation_poa(ethereum_testnet_config):
    """Test api instantiation with the poa flag enabled."""
    ethereum_testnet_config["poa_chain"] = True
    assert EthereumApi(**ethereum_testnet_config), "Failed to initialise the api"


def test_attribute_dict_wrapping_on_rotation_path(ethereum_testnet_config):
    """Test responses routed through RotatingHTTPProvider are wrapped as AttributeDict."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    fake_receipt = {
        "blockNumber": 12345,
        "status": 1,
        "transactionHash": "0x" + "ab" * 32,
        "transactionIndex": 0,
        "blockHash": "0x" + "cd" * 32,
        "from": "0x" + "11" * 20,
        "to": "0x" + "22" * 20,
        "cumulativeGasUsed": 21000,
        "gasUsed": 21000,
        "contractAddress": None,
        "logs": [],
        "logsBloom": "0x" + "00" * 256,
        "type": "0x2",
        "effectiveGasPrice": 1000000000,
    }
    # Patch every rotation provider's make_request so the rotation middleware
    # returns the fake response without touching the network.  The default
    # AttributeDictMiddleware (inner to rotation) must still wrap the result.
    fake_response = {"jsonrpc": "2.0", "id": 1, "result": fake_receipt}
    for provider in ethereum_api._rpc_rotation._providers:
        provider.make_request = MagicMock(return_value=fake_response)
    result = ethereum_api.api.eth.get_transaction_receipt(
        "0x" + "ab" * 32  # type: ignore[arg-type]
    )
    assert isinstance(result, AttributeDict)
    assert result.blockNumber == 12345


def test_user_injected_middleware_runs_on_rotation_path(ethereum_testnet_config):
    """Test user middleware injected at layer 0 still runs through the rotation path."""
    from web3.middleware import Web3Middleware  # local import — test-only

    seen = []

    class SpyMiddleware(Web3Middleware):
        def request_processor(self, method, params):
            seen.append(("req", method))
            return method, params

        def response_processor(self, method, response):
            seen.append(("resp", method))
            return response

    ethereum_api = EthereumApi(**ethereum_testnet_config)
    ethereum_api.api.middleware_onion.inject(
        SpyMiddleware, name="SpyMiddleware", layer=0
    )
    fake_response = {"jsonrpc": "2.0", "id": 1, "result": "0x2a"}
    for provider in ethereum_api._rpc_rotation._providers:
        provider.make_request = MagicMock(return_value=fake_response)
    ethereum_api.api.eth.get_block_number()
    assert ("req", "eth_blockNumber") in seen
    assert ("resp", "eth_blockNumber") in seen


def test_poa_middleware_transforms_response_on_rotation_path(ethereum_testnet_config):
    """Test ExtraDataToPOAMiddleware truncates extraData on the rotation path."""
    ethereum_testnet_config["poa_chain"] = True
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    # PoA's response_processor renames extraData -> proofOfAuthorityData on
    # eth_getBlockByNumber.  Use an oversized extraData (>32 bytes) which web3's
    # default formatters would reject, but PoA's transform should normalize.
    fake_block = {
        "number": "0x1",
        "hash": "0x" + "ab" * 32,
        "parentHash": "0x" + "cd" * 32,
        "extraData": "0x" + "ee" * 64,  # 64-byte extraData (PoA-style)
        "miner": "0x" + "11" * 20,
        "difficulty": "0x0",
        "totalDifficulty": "0x0",
        "size": "0x100",
        "gasLimit": "0x1c9c380",
        "gasUsed": "0x0",
        "timestamp": "0x0",
        "transactions": [],
        "uncles": [],
        "logsBloom": "0x" + "00" * 256,
        "sha3Uncles": "0x" + "00" * 32,
        "stateRoot": "0x" + "00" * 32,
        "transactionsRoot": "0x" + "00" * 32,
        "receiptsRoot": "0x" + "00" * 32,
        "mixHash": "0x" + "00" * 32,
        "nonce": "0x0000000000000000",
        "baseFeePerGas": "0x0",
    }
    fake_response = {"jsonrpc": "2.0", "id": 1, "result": fake_block}
    for provider in ethereum_api._rpc_rotation._providers:
        provider.make_request = MagicMock(return_value=fake_response)
    # Should not raise — without PoA middleware running, web3's default
    # formatter would reject the oversized extraData field.
    block = ethereum_api.api.eth.get_block(1)
    assert block is not None


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


def _wait_get_receipt(
    ethereum_api: EthereumApi, transaction_digest: str
) -> Tuple[Optional[JSONLike], bool]:
    transaction_receipt = None
    not_settled = True
    elapsed_time = 0
    time_to_wait = 40
    sleep_time = 2
    while not_settled and elapsed_time < time_to_wait:
        elapsed_time += sleep_time
        time.sleep(sleep_time)
        transaction_receipt = ethereum_api.get_transaction_receipt(transaction_digest)
        if transaction_receipt is None:
            continue
        is_settled = ethereum_api.is_transaction_settled(transaction_receipt)
        not_settled = not is_settled

    return transaction_receipt, not not_settled


def _construct_and_settle_tx(
    ethereum_api: EthereumApi,
    account: EthereumCrypto,
    tx_params: dict,
) -> Tuple[str, JSONLike, bool]:
    """Construct and settle a transaction."""
    transfer_transaction = ethereum_api.get_transfer_transaction(**tx_params)
    assert (
        isinstance(transfer_transaction, dict) and len(transfer_transaction) == 8
    ), "Incorrect transfer_transaction constructed."

    signed_transaction = account.sign_transaction(transfer_transaction)
    assert (
        isinstance(signed_transaction, dict) and len(signed_transaction) == 5
    ), "Incorrect signed_transaction constructed."

    transaction_digest = ethereum_api.send_signed_transaction(signed_transaction)
    assert transaction_digest is not None, "Failed to submit transfer transaction!"

    transaction_receipt, is_settled = _wait_get_receipt(
        ethereum_api, transaction_digest
    )

    assert transaction_receipt is not None, "Failed to retrieve transaction receipt."

    return transaction_digest, transaction_receipt, is_settled


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

    tx_params = {
        "sender_address": account.address,
        "destination_address": ec2.address,
        "amount": 40000,
        "tx_fee": 30000,
        "tx_nonce": ethereum_api.generate_tx_nonce(ec2.address, account.address),
        "chain_id": DEFAULT_GANACHE_CHAIN_ID,
        "max_priority_fee_per_gas": 1_000_000_000,
        "max_fee_per_gas": 1_000_000_000,
    }

    transaction_digest, transaction_receipt, is_settled = _construct_and_settle_tx(
        ethereum_api,
        account,
        tx_params,
    )
    assert is_settled, "Failed to verify tx!"

    tx = ethereum_api.get_transaction(transaction_digest)
    is_valid = ethereum_api.is_transaction_valid(
        tx, ec2.address, account.address, tx_params["tx_nonce"], tx_params["amount"]
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
        raise_on_try=True,
    )
    assert type(deploy_tx) is dict and len(deploy_tx) == 8
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
        assert len(ethereum_api.get_transfer_transaction(**args)) == 9


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
        assert len(ethereum_api.get_transfer_transaction(**args)) == 9


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

    contract_instance = Mock()
    constructor = Mock()
    constructor.build_transaction = lambda x: x
    contract_instance.constructor = Mock(return_value=constructor)

    with patch.object(
        ethereum_api.api.eth, "get_transaction_count", return_value=1
    ), patch.object(
        ethereum_api, "_is_gas_estimation_enabled", return_value=True
    ), mock.patch.object(
        ethereum_api,
        "_try_get_gas_estimate",
        return_value=120,
    ), patch.object(
        ethereum_api, "_is_gas_estimation_enabled", return_value=True
    ), patch.object(
        ethereum_api, "get_contract_instance", return_value=contract_instance
    ):
        tx = ethereum_api.get_deploy_transaction(
            **{
                "contract_interface": {"": ""},
                "deployer_address": ec1.address,
                "value": 1,
                "max_fee_per_gas": 1,
                "gas_price": 1,
                "max_priority_fee_per_gas": 1,
            }
        )
        assert tx["gas"] == 120


def test_gas_price_strategy_eip1559() -> None:
    """Test eip1559 based gas price strategy."""

    callable_ = get_gas_price_strategy_eip1559(**DEFAULT_EIP1559_STRATEGY)

    web3 = Mock()
    base_fee_per_gas_mock = 15e10
    get_block_mock = mock.patch.object(
        web3.eth,
        "get_block",
        return_value={"baseFeePerGas": base_fee_per_gas_mock, "number": 1},
    )
    get_chain_id_mock = mock.patch.object(web3.eth, "chain_id", return_value=1)

    mock_hist_data = get_history_data(n_blocks=5)
    rewards = [rew[0] for rew in mock_hist_data["reward"]]
    fee_history_mock = mock.patch.object(
        web3.eth,
        "fee_history",
        return_value=mock_hist_data,
    )

    with get_block_mock, fee_history_mock, get_chain_id_mock:
        gas_stregy = callable_(web3, "tx_params")

    assert all([key in gas_stregy for key in ["maxFeePerGas", "maxPriorityFeePerGas"]])
    assert gas_stregy["maxPriorityFeePerGas"] <= max(rewards)
    base_fee_per_gas_mock *= get_base_fee_multiplier(to_eth_unit(base_fee_per_gas_mock))
    assert gas_stregy["maxFeePerGas"] == base_fee_per_gas_mock


@pytest.mark.parametrize(
    "get_block_mock",
    [
        {"baseFeePerGas": None, "number": 1},
        {"baseFeePerGas": 150e9, "number": None},
        {"baseFeePerGas": None, "number": None},
    ],
)
def test_gas_price_strategy_eip1559_fallback_get_block(
    get_block_mock: Dict[str, Optional[int]],
) -> None:
    """Test eip1559 based gas price strategy."""

    strategy_kwargs = DEFAULT_EIP1559_STRATEGY.copy()
    strategy_kwargs["max_gas_fast"] = -1
    max_fee_per_gas = 1
    max_priority_fee_per_gas = 2
    strategy_kwargs["fallback_estimate"] = {
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": max_priority_fee_per_gas,
    }

    callable_ = get_gas_price_strategy_eip1559(**strategy_kwargs)
    web3 = Web3()

    get_block_mock = mock.patch.object(
        web3.eth,
        "get_block",
        return_value=get_block_mock,
    )

    fee_history_mock = mock.patch.object(
        web3.eth,
        "fee_history",
        return_value=get_history_data(
            n_blocks=5,
        ),
    )
    with get_block_mock:
        with fee_history_mock:
            with mock.patch(
                "aea_ledger_ethereum.ethereum.estimate_priority_fee",
                new_callable=lambda: lambda *args, **kwargs: 1,
            ):
                gas_stregy = callable_(web3, "tx_params")

    assert gas_stregy == strategy_kwargs["fallback_estimate"]


def test_gas_price_strategy_eip1559_fallback_max_gas_fast() -> None:
    """Test eip1559 based gas price strategy."""

    strategy_kwargs = DEFAULT_EIP1559_STRATEGY.copy()
    strategy_kwargs["max_gas_fast"] = -1
    max_fee_per_gas = 1
    max_priority_fee_per_gas = 2
    strategy_kwargs["fallback_estimate"] = {
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": max_priority_fee_per_gas,
    }

    callable_ = get_gas_price_strategy_eip1559(**strategy_kwargs)
    web3 = Web3()

    get_block_mock = mock.patch.object(
        web3.eth, "get_block", return_value={"baseFeePerGas": 150e9, "number": 1}
    )

    fee_history_mock = mock.patch.object(
        web3.eth,
        "fee_history",
        return_value=get_history_data(
            n_blocks=5,
        ),
    )
    with get_block_mock:
        with fee_history_mock:
            with mock.patch(
                "aea_ledger_ethereum.ethereum.estimate_priority_fee",
                new_callable=lambda: lambda *args, **kwargs: 1,
            ):
                gas_stregy = callable_(web3, "tx_params")

    assert gas_stregy == strategy_kwargs["fallback_estimate"]


@pytest.mark.parametrize(
    "chain_id,expected_max_fee_gwei,expected_tip_gwei,expected_max_gas_fast",
    [
        (10, 5, 3, 100),  # Optimism — 100 gwei ceiling, Worldcoin-era headroom
        (8453, 5, 3, 100),  # Base — 100 gwei ceiling, Mar 2024 memecoin headroom
        (34443, 5, 3, 50),  # Mode — 50 gwei defensive ceiling
        (252, 5, 3, 50),  # Fraxtal — 50 gwei defensive ceiling
        (42161, 2, 1, 5),  # Arbitrum One — 5 gwei (~250x the 0.02 gwei floor)
        (42220, 50, 25, 1500),  # Celo — 25 gwei network minimum
        (137, 6000, 30, 10000),  # Polygon — tip must clear 25 gwei validator floor
        (100, 5, 1, 30),  # Gnosis — 30 gwei ceiling, 1 gwei tip matches floor
        (1, 20, 3, 1500),  # Ethereum mainnet — unchanged default
        (56, 20, 3, 1500),  # BNB — unchanged (not in map)
        (324, 20, 3, 1500),  # zkSync — unchanged (not in map)
    ],
)
def test_get_default_gas_strategy_per_chain_fallbacks(
    chain_id, expected_max_fee_gwei, expected_tip_gwei, expected_max_gas_fast
) -> None:
    """`get_default_gas_strategy` returns chain-appropriate fallback values."""
    from aea_ledger_ethereum.ethereum import EIP1559, get_default_gas_strategy

    strategy = get_default_gas_strategy(chain_id)
    fallback = strategy[EIP1559]["fallback_estimate"]
    assert fallback["maxFeePerGas"] == expected_max_fee_gwei * 10**9
    assert fallback["maxPriorityFeePerGas"] == expected_tip_gwei * 10**9
    assert strategy[EIP1559]["max_gas_fast"] == expected_max_gas_fast


def _fallback_test(
    chain_id: int, base_fee_gwei: int, expect_fallback: bool
) -> Dict[str, Wei]:
    """Run the eip1559 strategy for ``chain_id`` against a mocked base fee."""
    from aea_ledger_ethereum.ethereum import EIP1559, get_default_gas_strategy

    strategy_kwargs = get_default_gas_strategy(chain_id)[EIP1559]
    callable_ = get_gas_price_strategy_eip1559(**strategy_kwargs)
    web3 = Web3()
    base_fee = to_wei(base_fee_gwei, GWEI)
    get_block_mock = mock.patch.object(
        web3.eth, "get_block", return_value={"baseFeePerGas": base_fee, "number": 1}
    )
    fee_history_mock = mock.patch.object(
        web3.eth, "fee_history", return_value=get_history_data(n_blocks=5)
    )
    with get_block_mock, fee_history_mock, mock.patch(
        "aea_ledger_ethereum.ethereum.estimate_priority_fee",
        new_callable=lambda: lambda *args, **kwargs: to_wei(1, GWEI),
    ):
        gas_strategy = callable_(web3, "tx_params")

    fallback = strategy_kwargs["fallback_estimate"]
    if expect_fallback:
        assert (
            gas_strategy == fallback
        ), f"chain {chain_id}: expected fallback, got {gas_strategy}"
    else:
        assert (
            gas_strategy != fallback
        ), f"chain {chain_id}: expected computed value, got fallback {fallback}"
    return gas_strategy


def test_gnosis_anomaly_triggers_fallback() -> None:
    """Gnosis: 150 gwei base fee exceeds the 30 gwei ceiling -> fallback."""
    gas_strategy = _fallback_test(100, 150, expect_fallback=True)
    assert gas_strategy["maxFeePerGas"] == to_wei(5, GWEI)
    assert gas_strategy["maxPriorityFeePerGas"] == to_wei(1, GWEI)


def test_gnosis_normal_fee_does_not_trigger_fallback() -> None:
    """Gnosis: 2 gwei base fee stays well under the 30 gwei ceiling."""
    gas_strategy = _fallback_test(100, 2, expect_fallback=False)
    assert gas_strategy["maxFeePerGas"] < to_wei(30, GWEI)


def test_base_anomaly_triggers_fallback() -> None:
    """Base: 200 gwei base fee exceeds the 100 gwei ceiling -> fallback.

    Symmetric to the Gnosis incident: Base inherits the same missing-
    `max_gas_fast` shape from `CHAIN_EIP1559_OVERRIDES` and is now
    explicitly capped at 100 gwei -- generous enough for the March 2024
    Dencun memecoin congestion (sustained ~24 gwei averages with bursts
    >100 gwei in individual blocks) but blocks oracle anomalies.
    """
    gas_strategy = _fallback_test(8453, 200, expect_fallback=True)
    assert gas_strategy["maxFeePerGas"] == to_wei(5, GWEI)
    assert gas_strategy["maxPriorityFeePerGas"] == to_wei(3, GWEI)


def test_base_normal_fee_does_not_trigger_fallback() -> None:
    """Base: 0.005 gwei base fee (typical post-Jovian) stays under the cap."""
    gas_strategy = _fallback_test(8453, 1, expect_fallback=False)
    assert gas_strategy["maxFeePerGas"] < to_wei(100, GWEI)


def test_arbitrum_anomaly_triggers_fallback() -> None:
    """Arbitrum One: 10 gwei base fee exceeds the 5 gwei ceiling -> fallback."""
    gas_strategy = _fallback_test(42161, 10, expect_fallback=True)
    assert gas_strategy["maxFeePerGas"] == to_wei(2, GWEI)
    assert gas_strategy["maxPriorityFeePerGas"] == to_wei(1, GWEI)


def test_get_default_gas_strategy_polygon_applies_to_eip1559_polygon() -> None:
    """Polygon's primary strategy `eip1559_polygon` picks up the override too."""
    from aea_ledger_ethereum.ethereum import EIP1559_POLYGON, get_default_gas_strategy

    strategy = get_default_gas_strategy(137)
    polygon_fallback = strategy[EIP1559_POLYGON]["fallback_estimate"]
    assert polygon_fallback["maxFeePerGas"] == 6000 * 10**9
    assert polygon_fallback["maxPriorityFeePerGas"] == 30 * 10**9


def test_ethereum_api_init_applies_chain_specific_fallback() -> None:
    """`make_ledger_api('ethereum', chain_id=8453)` picks up Base's 5-gwei fallback."""
    api = EthereumApi(address="http://127.0.0.1:8545", chain_id=8453)
    fallback = api._gas_price_strategies["eip1559"]["fallback_estimate"]  # noqa: SLF001
    assert fallback["maxFeePerGas"] == 5 * 10**9
    assert fallback["maxPriorityFeePerGas"] == 3 * 10**9


def test_ethereum_api_init_user_gas_price_strategies_wins() -> None:
    """User-supplied `gas_price_strategies` kwarg wins over per-chain defaults."""
    user_override = {
        "eip1559": {
            "max_gas_fast": 42,
            "fee_history_blocks": 10,
            "fee_history_percentile": 5,
            "min_allowed_tip": 1,
            "default_priority_fee": None,
            "fallback_estimate": {"maxFeePerGas": 123, "maxPriorityFeePerGas": 456},
            "priority_fee_increase_boundary": 200,
        },
    }
    api = EthereumApi(
        address="http://127.0.0.1:8545",
        chain_id=8453,  # Base — would otherwise get 5 gwei
        gas_price_strategies=user_override,
    )
    fallback = api._gas_price_strategies["eip1559"]["fallback_estimate"]  # noqa: SLF001
    assert fallback["maxFeePerGas"] == 123
    assert fallback["maxPriorityFeePerGas"] == 456


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


def test_contract_method_call():
    """Test EthereumApi.contract_method_call."""

    method_mock = MagicMock()
    method_mock().call = MagicMock(return_value={"value": 0})

    contract_instance = MagicMock()
    contract_instance.functions.dummy_method = method_mock

    result = EthereumApi.contract_method_call(
        contract_instance=contract_instance, method_name="dummy_method", dummy_arg=1
    )
    assert result["value"] == 0


def test_build_transaction(ethereum_testnet_config):
    """Test EthereumApi.build_transaction."""

    def pass_tx_params(tx_params):
        return tx_params

    tx_mock = MagicMock()
    tx_mock.build_transaction = pass_tx_params

    method_mock = MagicMock(return_value=tx_mock)

    contract_instance = MagicMock()
    contract_instance.functions.dummy_method = method_mock

    eth_api = EthereumApi(**ethereum_testnet_config)

    with pytest.raises(
        ValueError, match=re.escape("Argument 'method_args' cannot be 'None'.")
    ):
        eth_api.build_transaction(
            contract_instance=contract_instance,
            method_name="dummy_method",
            method_args=None,
            tx_args={},
        )
    with pytest.raises(
        ValueError, match=re.escape("Argument 'tx_args' cannot be 'None'.")
    ):
        eth_api.build_transaction(
            contract_instance=contract_instance,
            method_name="dummy_method",
            method_args={},
            tx_args=None,
        )

    with mock.patch(
        "web3.eth.Eth.get_transaction_count",
        return_value=0,
    ):
        result = eth_api.build_transaction(
            contract_instance=contract_instance,
            method_name="dummy_method",
            method_args={},
            tx_args=dict(
                sender_address="sender_address",
                eth_value=0,
                gas=0,
                gasPrice=0,  # camel-casing due to contract api requirements
                maxFeePerGas=0,  # camel-casing due to contract api requirements
                maxPriorityFeePerGas=0,  # camel-casing due to contract api requirements
            ),
        )

        assert result == dict(
            nonce=0,
            value=0,
            gas=0,
            gasPrice=0,
            maxFeePerGas=0,
            maxPriorityFeePerGas=0,
        )

        with mock.patch.object(
            EthereumApi,
            "try_get_gas_pricing",
            return_value={"gas": 0},
        ):
            result = eth_api.build_transaction(
                contract_instance=contract_instance,
                method_name="dummy_method",
                method_args={},
                tx_args=dict(
                    sender_address="sender_address",
                    eth_value=0,
                ),
            )

            assert result == dict(nonce=0, value=0, gas=0)

        # try get gas estimates if _is_gas_estimation_enabled
        with mock.patch.object(
            EthereumApi,
            "try_get_gas_pricing",
            return_value={"gas": 0},
        ), mock.patch.object(
            eth_api,
            "_is_gas_estimation_enabled",
            return_value=True,
        ), mock.patch.object(
            eth_api,
            "_try_get_gas_estimate",
            return_value=12,
        ):
            result = eth_api.build_transaction(
                contract_instance=contract_instance,
                method_name="dummy_method",
                method_args={},
                tx_args=dict(
                    sender_address="sender_address",
                    eth_value=0,
                ),
            )

            assert result == dict(nonce=0, value=0, gas=12)


def test_get_transaction_transfer_logs(ethereum_testnet_config):
    """Test EthereumApi.get_transaction_transfer_logs."""
    eth_api = EthereumApi(**ethereum_testnet_config)

    dummy_receipt = {"logs": [{"topics": ["0x0", "0x0"]}]}

    with mock.patch(
        "web3.eth.Eth.get_transaction_receipt",
        return_value=dummy_receipt,
    ):
        contract_instance = MagicMock()
        contract_instance.events.Transfer().processReceipt.return_value = {"log": "log"}

        result = eth_api.get_transaction_transfer_logs(
            contract_instance=contract_instance,
            tx_hash="dummy_hash",
        )

        assert result == dict(logs={"log": "log"})


def test_get_transaction_transfer_logs_raise(ethereum_testnet_config):
    """Test EthereumApi.get_transaction_transfer_logs."""
    eth_api = EthereumApi(**ethereum_testnet_config)

    with mock.patch(
        "web3.eth.Eth.get_transaction_receipt",
        return_value=None,
    ):
        contract_instance = MagicMock()
        contract_instance.events.Transfer().processReceipt.return_value = {"log": "log"}

        result = eth_api.get_transaction_transfer_logs(
            contract_instance=contract_instance,
            tx_hash="dummy_hash",
        )

        assert result == dict(logs=[])


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_revert_reason(
    ethereum_private_key_file: str,
    ethereum_testnet_config: dict,
    ganache: Generator,
) -> None:
    """Test the retrieval of the revert reason for a transaction."""
    account = EthereumCrypto(private_key_path=ethereum_private_key_file)
    ec2 = EthereumCrypto()
    ethereum_api = EthereumApi(**ethereum_testnet_config)

    tx_params = {
        "sender_address": account.address,
        "destination_address": ec2.address,
        "amount": 40000,
        "tx_fee": 30000,
        "tx_nonce": 0,
        "chain_id": DEFAULT_GANACHE_CHAIN_ID,
        "max_priority_fee_per_gas": 1_000_000_000,
        "max_fee_per_gas": 1_000_000_000,
    }

    with mock.patch(
        "web3.eth.Eth.get_transaction_receipt",
        return_value=AttributeDict({"status": 0}),
    ):
        with mock.patch(
            "web3.eth.Eth.call",
            side_effect=ContractLogicError("test revert reason"),
        ):
            _, transaction_receipt, is_settled = _construct_and_settle_tx(
                ethereum_api,
                account,
                tx_params,
            )

            assert transaction_receipt["revert_reason"] == "test revert reason"


@mock.patch(
    "web3.eth.Eth.fee_history",
    return_value=FeeHistory(
        baseFeePerGas=[Wei(0)],
        gasUsedRatio=[0],
        oldestBlock=BlockNumber(0),
        reward=[[Wei(0)]],
    ),
)
@pytest.mark.parametrize(
    "strategy",
    (
        {"name": EIP1559, "params": ("maxPriorityFeePerGas", "maxFeePerGas")},
        {"name": GAS_STATION, "params": ("gasPrice",)},
        {"name": EIP1559_POLYGON, "params": ("maxPriorityFeePerGas", "maxFeePerGas")},
    ),
)
def test_try_get_gas_pricing(
    _fee_history_mock: Mock,
    strategy: Dict[str, Union[str, Tuple[str, ...]]],
    ethereum_testnet_config: dict,
    ganache: Generator,
) -> None:
    """Test `try_get_gas_pricing`."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)

    # test gas pricing
    gas_price = ethereum_api.try_get_gas_pricing(gas_price_strategy=strategy["name"])
    assert set(strategy["params"]) == set(gas_price.keys())
    assert all(
        gas_price[param] > 0 and isinstance(gas_price[param], int)
        for param in strategy["params"]
    )
    expected_reprice = {
        param: math.ceil(value * TIP_INCREASE) for param, value in gas_price.items()
    }

    # test gas repricing
    gas_reprice = ethereum_api.try_get_gas_pricing(
        gas_price_strategy=strategy["name"], old_price=gas_price
    )
    assert all(
        gas_reprice[param] > 0 and isinstance(gas_reprice[param], int)
        for param in strategy["params"]
    )
    assert gas_reprice == expected_reprice, "The repricing was performed incorrectly!"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.parametrize(
    "chain_config, strategy_config_overrides, poa_chain",
    (
        ({"address": RPCS[EIP1559Networks.ETHEREUM], "chain_id": 1}, None, False),
        ({"address": RPCS[EIP1559Networks.ARBITRUM], "chain_id": 42161}, None, False),
        ({"address": RPCS[EIP1559Networks.ZKSYNC], "chain_id": 324}, None, False),
        ({"address": RPCS[EIP1559Networks.BINANCE], "chain_id": 56}, None, True),
        (
            {"address": RPCS[EIP1559Networks.GNOSIS], "chain_id": 100},
            {"min_allowed_tip": DEFAULT_GNOSIS_MIN_ALLOWED_TIP},
            False,
        ),
        (
            {
                "address": RPCS[EIP1559Networks.CELO],
                "chain_id": 42220,
            },
            None,
            True,
        ),
        ({"address": RPCS[EIP1559Networks.OPTIMISM], "chain_id": 10}, None, False),
        ({"address": RPCS[EIP1559Networks.BASE], "chain_id": 8453}, None, False),
        (
            {"address": RPCS[EIP1559Networks.MODE], "chain_id": 34443},
            {
                "fee_history_blocks": 20,
                "fallback_estimate": {
                    "maxFeePerGas": 2000000000,
                    "maxPriorityFeePerGas": 300000000,
                },
            },
            False,
        ),
        pytest.param(
            {"address": RPCS[EIP1559Networks.POLYGON], "chain_id": 137},
            None,
            True,
            marks=pytest.mark.xfail(reason="Polygon RPC is flaky on CI"),
        ),
        ({"address": RPCS[EIP1559Networks.FRAXTAL], "chain_id": 252}, None, False),
    ),
)
def test_eip1559_on_network(
    chain_config: Dict[str, Union[str, int]],
    strategy_config_overrides: Optional[Dict[str, int]],
    poa_chain: bool,
) -> None:
    """Test the `try_get_gas_pricing` using the eip1559 strategy on multiple chains."""
    config = {
        **chain_config,
        "denom": "wei",
        "default_gas_price_strategy": "eip1559",
        "gas_price_strategies": {
            "eip1559": DEFAULT_EIP1559_STRATEGY,
        },
        "poa_chain": poa_chain,
        "timeout": 30,
    }
    ethereum_api = EthereumApi(**config)
    latest_block = ethereum_api.api.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas")
    gas_price = ethereum_api.try_get_gas_pricing(
        gas_price_strategy=EIP1559, extra_config=strategy_config_overrides
    )
    min_allowed_tip = (
        strategy_config_overrides.get("min_allowed_tip", DEFAULT_MIN_ALLOWED_TIP)
        if strategy_config_overrides
        else DEFAULT_MIN_ALLOWED_TIP
    )
    assert {"maxFeePerGas", "maxPriorityFeePerGas"} == set(gas_price.keys())
    max_priority_fee = gas_price["maxPriorityFeePerGas"]
    assert max_priority_fee >= min_allowed_tip
    assert (
        gas_price["maxFeePerGas"] > max_priority_fee
        if base_fee
        else gas_price["maxFeePerGas"] == max_priority_fee
    )
    assert max_priority_fee != DEFAULT_FALLBACK_ESTIMATE["maxPriorityFeePerGas"]
    assert gas_price["maxFeePerGas"] != DEFAULT_FALLBACK_ESTIMATE["maxFeePerGas"]


@pytest.mark.parametrize(
    "strategy",
    ({"name": EIP1559_POLYGON, "params": ("maxPriorityFeePerGas", "maxFeePerGas")},),
)
def test_try_get_gas_pricing_poa(
    strategy: Dict[str, Union[str, Tuple[str, ...]]],
    polygon_testnet_config: dict,
    ganache: Generator,
) -> None:
    """Test `try_get_gas_pricing` for a poa chain like Rinkeby."""
    ethereum_api = EthereumApi(**polygon_testnet_config)
    assert "ExtraDataToPOAMiddleware" in ethereum_api.api.middleware_onion.keys()

    # test gas pricing
    gas_price = ethereum_api.try_get_gas_pricing(gas_price_strategy=strategy["name"])
    assert set(strategy["params"]) == set(gas_price.keys())
    assert all(
        gas_price[param] > 0 and isinstance(gas_price[param], int)
        for param in strategy["params"]
    )
    expteced_reprice = {
        param: math.ceil(value * TIP_INCREASE) for param, value in gas_price.items()
    }

    # test gas repricing
    gas_reprice = ethereum_api.try_get_gas_pricing(
        gas_price_strategy=strategy["name"], old_price=copy.deepcopy(gas_price)
    )
    assert all(
        gas_reprice[param] > 0 and isinstance(gas_reprice[param], int)
        for param in strategy["params"]
    )
    assert gas_reprice == expteced_reprice, "The repricing was performed incorrectly!"


@pytest.mark.parametrize("mock_exception", (True, False))
def test_gas_estimation(
    mock_exception,
    ethereum_testnet_config: dict,
    ganache: Generator,
    caplog,
) -> None:
    """Test gas estimation."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    tx = {
        "value": 0,
        "chainId": 1337,
        "from": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
        "gas": 291661,
        "maxPriorityFeePerGas": 3000000000,
        "maxFeePerGas": 4000000000,
        "to": "0x68FCdF52066CcE5612827E872c45767E5a1f6551",
        "data": "",
    }
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.ethereum._default_logger"):
        if mock_exception:
            with patch.object(
                ethereum_api._api.eth, "estimate_gas"
            ) as estimate_gas_mock:
                # raise exception on first call only
                estimate_gas_mock.side_effect = [
                    ValueError("triggered exception"),
                    None,
                ]
                ethereum_api.update_with_gas_estimate(tx)
        else:
            ethereum_api.update_with_gas_estimate(tx, raise_on_try=True)
        if mock_exception:
            assert (
                "ValueError: triggered exception" in caplog.text
            ), f"Cannot find message in output: {caplog.text}"


@pytest.mark.parametrize("mock_exception", (True, False))
def test_get_l1_data_fee_op_stack(
    mock_exception,
    ethereum_testnet_config: dict,
    caplog,
) -> None:
    """Test the OP-stack branch of get_l1_data_fee via the GasPriceOracle."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    # Force an OP-stack chain id (Base) so the dispatcher picks the OP-stack path.
    ethereum_api._chain_id = 8453  # noqa: SLF001
    tx = {
        "nonce": 0,
        "value": 0,
        "chainId": 8453,
        "from": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
        "gas": 291661,
        "maxPriorityFeePerGas": 3000000000,
        "maxFeePerGas": 4000000000,
        "to": "0x68FCdF52066CcE5612827E872c45767E5a1f6551",
        "data": "",
    }
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.ethereum._default_logger"):
        with patch.object(ethereum_api._api.eth, "contract") as contract_mock:
            contract_instance = contract_mock.return_value
            gas_oracle_function = contract_instance.functions.getL1Fee
            gas_oracle_function.return_value.call.return_value = 100

            if mock_exception:
                # raise exception on first call only
                gas_oracle_function.return_value.call.side_effect = [
                    ValueError("triggered exception"),
                    None,
                ]
                assert ethereum_api.get_l1_data_fee(tx) == 0
            else:
                assert ethereum_api.get_l1_data_fee(tx) == 112


@pytest.mark.parametrize("mock_exception", (True, False))
def test_get_l1_data_fee_arbitrum(
    mock_exception,
    ethereum_testnet_config: dict,
    caplog,
) -> None:
    """Test the Arbitrum branch of get_l1_data_fee via NodeInterface.gasEstimateL1Component."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    # Force Arbitrum One so the dispatcher picks the Arbitrum path.
    ethereum_api._chain_id = 42161  # noqa: SLF001
    tx = {
        "nonce": 0,
        "value": 0,
        "chainId": 42161,
        "from": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
        "gas": 291661,
        "maxPriorityFeePerGas": 3000000000,
        "maxFeePerGas": 4000000000,
        "to": "0x68FCdF52066CcE5612827E872c45767E5a1f6551",
        "data": "",
    }
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.ethereum._default_logger"):
        with patch.object(ethereum_api._api.eth, "contract") as contract_mock:
            contract_instance = contract_mock.return_value
            node_interface_function = contract_instance.functions.gasEstimateL1Component
            # (gasEstimateForL1=2000, baseFee=100, l1BaseFeeEstimate=ignored).
            # Expected: int(2000 * 100 * 1.1) = 220000 wei.
            node_interface_function.return_value.call.return_value = (
                2000,
                100,
                0,
            )

            if mock_exception:
                node_interface_function.return_value.call.side_effect = ValueError(
                    "triggered exception"
                )
                assert ethereum_api.get_l1_data_fee(tx) == 0
            else:
                assert ethereum_api.get_l1_data_fee(tx) == 220000


def test_get_l1_data_fee_non_l2_returns_zero(
    ethereum_testnet_config: dict,
) -> None:
    """Non-L2 chains return 0 without calling any oracle / precompile."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    # Gnosis (100) is not in _OP_STACK_CHAIN_IDS or _ARBITRUM_CHAIN_IDS.
    ethereum_api._chain_id = 100  # noqa: SLF001
    tx = {
        "nonce": 0,
        "value": 0,
        "chainId": 100,
        "from": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
        "gas": 291661,
        "maxPriorityFeePerGas": 3000000000,
        "maxFeePerGas": 4000000000,
        "to": "0x68FCdF52066CcE5612827E872c45767E5a1f6551",
        "data": "",
    }
    with patch.object(ethereum_api._api.eth, "contract") as contract_mock:
        assert ethereum_api.get_l1_data_fee(tx) == 0
        contract_mock.assert_not_called()


@patch.object(EthereumApi, "_try_get_transaction_count", return_value=1)
@patch.object(EthereumApi, "_try_get_max_priority_fee", return_value=1)
def test_ethereum_api_get_transfer_transaction_estimate_gas(*args) -> None:
    """Test EthereumApi.get_transfer_transaction gas auto estimate."""
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
        "max_fee_per_gas": None,
    }
    with patch.object(
        ethereum_api, "try_get_gas_pricing", return_value={"gasPrice": 12}
    ) as get_gas_pricing:
        result = ethereum_api.get_transfer_transaction(**args)
        assert result["gasPrice"] == 12
        get_gas_pricing.assert_called_once()

    args["gas_price"] = 13
    result = ethereum_api.get_transfer_transaction(**args)
    assert result["gasPrice"] == 13


def test_get_base_fee_multiplier() -> None:
    """Test get_base_fee_multiplier."""
    assert get_base_fee_multiplier(35) == 2.0
    assert get_base_fee_multiplier(45) == 1.6
    assert get_base_fee_multiplier(105) == 1.4
    assert get_base_fee_multiplier(205) == 1.2


def test_estimate_priority_fee() -> None:
    """Test estimate_priority_fee."""
    # return none on no rewards
    web3_mock = Mock()
    web3_mock.eth.fee_history = Mock(return_value={"reward": []})
    web3_mock.eth.chain_id = 100
    assert estimate_priority_fee(web3_mock, 1, None, 11, 1, 145, 1) == 145

    # test a single reward
    web3_mock.eth.fee_history = Mock(return_value={"reward": [[1]]})
    assert estimate_priority_fee(web3_mock, 1, None, 11, 1, 1, 1) == 1

    # test 2 rewards
    web3_mock.eth.fee_history = Mock(return_value={"reward": [[1], [2]]})
    assert estimate_priority_fee(web3_mock, 1, None, 11, 1, 1, 1) == 2

    # If we have big increase in value, we could be considering "outliers" in our estimate
    # Skip the low elements and take a new median
    web3_mock.eth.fee_history = Mock(return_value={"reward": [[1], [10], [10000]]})
    assert estimate_priority_fee(web3_mock, 1, None, 11, 1, 1, 1) == 10000

    # test the default priority fee
    assert estimate_priority_fee(web3_mock, 1, 20, 11, 1, 1, 1) == 20

    # set the fee history for block 38255060 on Gnosis as an example,
    # which was causing issues with the gas estimation in `v1.61.0`:
    # `EffectivePriorityFeePerGas too low 999999976 < 1000000000`
    web3_mock.eth.fee_history = Mock(
        return_value={
            "reward": [
                [999999946],
                [999999943],
                [1454999904],
                [999999976],
                [1454999872],
                [1000000011],
                [5],
                [1300000021],
                [1000000000],
                [1000000000],
                [999999888],
                [1000000000],
                [5],
                [1000000000],
                [5],
                [999999876],
                [5],
                [1000000000],
                [999999900],
                [5],
            ]
        }
    )
    assert (
        estimate_priority_fee(web3_mock, 1, None, 20, 5, 1000000000, 200) == 1000000000
    )


def test_try_get_revert_reason_http_error_propagated(ethereum_testnet_config) -> None:
    """Test httperror reraised if get_revert_reason fails."""
    eth_api = EthereumApi(**ethereum_testnet_config)
    tx = {"from": 1, "to": 1, "input": 1, "value": 1, "blockNumber": 1}
    api_mock = Mock()
    api_mock.eth.call = Mock(side_effect=HTTPError("http_error"))
    with patch.object(eth_api, "_api", new=api_mock):
        with pytest.raises(HTTPError):
            eth_api._try_get_revert_reason(tx, raise_on_try=True)


def test_get_gas_price_strategy() -> None:
    """Test get_gas_price_strategy and strategies."""
    strategy = get_gas_price_strategy(None)
    assert strategy is rpc_gas_price_strategy_wrapper
    assert "gasPrice" in strategy(Mock(), Mock())

    strategy = get_gas_price_strategy_eip1559_polygon("test", {"gasPrice": 12})

    resp_mock = Mock()
    resp_mock.status_code = 300
    with patch("aea_ledger_ethereum.ethereum.requests.get", return_value=resp_mock):
        assert strategy(Mock(), Mock()) == {"gasPrice": 12}

    resp_mock.status_code = 200
    resp_mock.json = Mock(return_value={"fast": {"maxFee": 2, "maxPriorityFee": 2}})
    with patch("aea_ledger_ethereum.ethereum.requests.get", return_value=resp_mock):
        assert strategy(Mock(), Mock()) == {
            "maxFeePerGas": 2000000000,
            "maxPriorityFeePerGas": 2000000000,
        }

    with patch(
        "aea_ledger_ethereum.ethereum.requests.get",
        side_effect=requests.exceptions.RequestException(Mock()),
    ):
        assert strategy(Mock(), Mock()) == {"gasPrice": 12}


@pytest.mark.ledger
def test_update_with_gas_estimate_method_raise_on_try(
    ethereum_testnet_config, ganache, ethereum_private_key_file, caplog
):
    """Test the balance is zero for a new account."""
    ethereum_api = EthereumApi(**ethereum_testnet_config)

    # The exception will be intercepted and logged
    with mock.patch.object(
        ethereum_api.api.eth, "estimate_gas", side_effect=ContractLogicError
    ), caplog.at_level(logging.WARNING):
        ethereum_api.update_with_gas_estimate(
            transaction={
                "value": 0,
                "chainId": 1337,
                "from": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
                "gas": 291661,
                "maxPriorityFeePerGas": 3000000000,
                "maxFeePerGas": 4000000000,
                "to": "0x68FCdF52066CcE5612827E872c45767E5a1f6551",
                "data": "",
            }
        )

        assert (
            "Unable to estimate gas with default state , ContractLogicError"
            in caplog.text
        )

    # The exception won't be intercepted
    with pytest.raises(ContractLogicError):
        with mock.patch.object(
            ethereum_api.api.eth, "estimate_gas", side_effect=ContractLogicError
        ):
            ethereum_api.update_with_gas_estimate(
                transaction={
                    "value": 0,
                    "chainId": 1337,
                    "from": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
                    "gas": 291661,
                    "maxPriorityFeePerGas": 3000000000,
                    "maxFeePerGas": 4000000000,
                    "to": "0x68FCdF52066CcE5612827E872c45767E5a1f6551",
                    "data": "",
                },
                raise_on_try=True,
            )
