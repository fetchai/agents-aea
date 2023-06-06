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
# pylint: disable=redefined-outer-name,import-error,protected-access
# flake8: noqa: B009

"""Tests for the aea_ledger_ethereum_flashbots package."""
from typing import Tuple
from unittest.mock import ANY, MagicMock, patch

import pytest
from aea_ledger_ethereum_flashbots.ethereum_flashbots import EthereumFlashbotApi
from eth_account import Account
from flashbots.types import FlashbotsBundleRawTx
from hexbytes import HexBytes
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt


_DUMMY_FLASHBOTS_BUILDERS = [
    ["dummy", "dummy_uri1"],
    ["builder0x69", "dummy_uri2"],
]


@pytest.fixture
def ethereum_flashbot_api() -> EthereumFlashbotApi:
    """Get the ethereum flashbot API."""

    return EthereumFlashbotApi(flashbots_builders=_DUMMY_FLASHBOTS_BUILDERS)


def test_init_with_signature_private_key() -> None:
    """Test init with signature private key."""
    signature_private_key = "my private key"
    with patch.object(
        Account, "from_key", side_effect=lambda private_key: MagicMock()
    ) as account_from_key_mock:
        EthereumFlashbotApi(
            signature_private_key=signature_private_key,
            flashbots_builders=_DUMMY_FLASHBOTS_BUILDERS,
        )
        assert account_from_key_mock.called_once_with(signature_private_key)


def test_init_without_signature_private_key() -> None:
    """Test init without signature private key."""
    with patch.object(
        Account, "create", side_effect=MagicMock()
    ) as account_create_mock:
        EthereumFlashbotApi(flashbots_builders=_DUMMY_FLASHBOTS_BUILDERS)
        assert account_create_mock.called_once_with()


@pytest.mark.parametrize("signed_txs", (("0x1234", "0x0000", "0x5232"), ("0x1234",)))
def test_bundle_transactions(ethereum_flashbot_api, signed_txs: Tuple[str]) -> None:
    """Test bundle transactions."""
    dummy_signed_transactions = [
        dict(raw_transaction=signed_tx) for signed_tx in signed_txs
    ]
    bundle = ethereum_flashbot_api.bundle_transactions(dummy_signed_transactions)
    actual_bundle = [tx.get("signed_transaction", None) for tx in bundle]
    expected_bundle = [
        HexBytes(tx.get("raw_transaction", None)) for tx in dummy_signed_transactions
    ]
    assert expected_bundle == actual_bundle


def test_simulate_with_successful_simulation(
    ethereum_flashbot_api,
) -> None:
    """Test simulate with successful simulation."""
    # mock
    response_mock = MagicMock()
    default_builder = _DUMMY_FLASHBOTS_BUILDERS[0][0]
    flashbots_module = getattr(
        ethereum_flashbot_api._builder_to_web3[default_builder], "flashbots"
    )
    flashbots_module.simulate = MagicMock(return_value=response_mock)

    # run
    bundle = [FlashbotsBundleRawTx(signed_transaction=HexBytes("0x1234"))]
    success = ethereum_flashbot_api.simulate(bundle, 123)

    # check
    flashbots_module.simulate.assert_called_once_with(bundle, 123)
    assert success


def test_simulate_with_failed_simulation(ethereum_flashbot_api) -> None:
    """Test simulate with failed simulation."""
    # mock
    response_mock = MagicMock(side_effect=Exception)
    ethereum_flashbot_api.flashbots.simulate = MagicMock(side_effect=response_mock)

    # run
    bundle = FlashbotsBundleRawTx[{"signed_transaction": "0x1234"}]
    success = ethereum_flashbot_api.simulate(bundle, 123)

    # check
    ethereum_flashbot_api.flashbots.simulate.assert_called_once_with(bundle, 123)
    assert not success


def test_send_bundle_with_successful_transaction(ethereum_flashbot_api) -> None:
    """Test send bundle with successful transaction."""
    current_block = 122
    send_bundle = [FlashbotsBundleRawTx(signed_transaction=HexBytes("0x1234"))]
    res_bundle = [{"hash": b"0x1234"}]
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.receipts = MagicMock(return_value=[TxReceipt(blockNumber=1)])
    response_mock.bundle = res_bundle
    ethereum_flashbot_api.api.eth.get_block_number = MagicMock(
        return_value=current_block
    )
    ethereum_flashbot_api.flashbots.simulate = MagicMock(return_value=True)
    ethereum_flashbot_api.flashbots.send_bundle = MagicMock(return_value=response_mock)

    # run
    target_blocks = [123]
    tx_hashes = ethereum_flashbot_api.send_bundle(send_bundle, target_blocks)

    # check
    ethereum_flashbot_api.flashbots.simulate.assert_called_once_with(
        send_bundle, current_block
    )
    ethereum_flashbot_api.flashbots.send_bundle.assert_called_once_with(
        send_bundle, target_blocks[0], opts={"replacementUuid": ANY}
    )
    assert response_mock.wait.called
    assert tx_hashes == [tx["hash"].hex() for tx in response_mock.bundle]


def test_bundle_transactions_with_empty_list(ethereum_flashbot_api) -> None:
    """Test bundle transactions with an empty list of signed transactions."""
    signed_transactions = []
    bundle = ethereum_flashbot_api.bundle_transactions(signed_transactions)
    assert len(bundle) == 0


def test_simulate_with_empty_bundle(ethereum_flashbot_api) -> None:
    """Test simulate with an empty bundle."""
    bundle = []
    success = ethereum_flashbot_api.simulate(bundle, 123)
    assert not success


def test_simulate_with_invalid_target_blocks(ethereum_flashbot_api) -> None:
    """Test simulate with invalid target blocks."""
    bundle = [FlashbotsBundleRawTx(signed_transaction=HexBytes("0x1234"))]
    success = ethereum_flashbot_api.simulate(bundle, -1)
    assert not success


def test_bundle_and_send_with_successful_transaction(ethereum_flashbot_api) -> None:
    """Test bundle and send with successful transaction."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.receipts = MagicMock(
        return_value=[TxReceipt(blockNumber=1), TxReceipt(blockNumber=2)]
    )
    response_mock.bundle = [{"hash": b"0x1234"}, {"hash": b"0x5678"}]
    ethereum_flashbot_api._get_next_blocks = MagicMock(return_value=1)
    ethereum_flashbot_api.api.eth.get_block_number = MagicMock(return_value=1)
    ethereum_flashbot_api.flashbots.simulate = MagicMock(return_value=True)
    ethereum_flashbot_api.flashbots.send_bundle = MagicMock(return_value=response_mock)

    # run
    signed_transactions = [
        dict(raw_transaction="0x1234"),
        dict(raw_transaction="0x5678"),
    ]
    target_blocks = [123]

    # check
    tx_hashes = ethereum_flashbot_api.send_signed_transactions(
        signed_transactions,
        target_blocks=target_blocks,
    )
    ethereum_flashbot_api.flashbots.simulate.assert_called_once()
    ethereum_flashbot_api.flashbots.send_bundle.assert_called_once()
    assert response_mock.wait.called
    assert tx_hashes == [tx["hash"].hex() for tx in response_mock.bundle]


def test_bundle_and_send_with_failed_simulation(ethereum_flashbot_api) -> None:
    """Test bundle and send with failed simulation."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.bundle_hash = MagicMock()
    response_mock.receipts = MagicMock(side_effect=TransactionNotFound)
    ethereum_flashbot_api._get_next_blocks = MagicMock(return_value=1)
    ethereum_flashbot_api.api.eth.get_block_number = MagicMock(return_value=1)
    ethereum_flashbot_api.flashbots.simulate = MagicMock(return_value=True)
    ethereum_flashbot_api.flashbots.send_bundle = MagicMock(return_value=response_mock)
    ethereum_flashbot_api.flashbots.cancel_bundles = MagicMock()
    ethereum_flashbot_api.api.toHex = MagicMock()
    ethereum_flashbot_api.flashbots.get_bundle_stats_v2 = MagicMock(
        return_value=response_mock
    )

    # run
    signed_transactions = [
        dict(raw_transaction="0x1234"),
        dict(raw_transaction="0x5678"),
    ]
    target_blocks = [123]
    tx_hashes = ethereum_flashbot_api.send_signed_transactions(
        signed_transactions,
        target_blocks=target_blocks,
    )

    # check
    ethereum_flashbot_api.flashbots.simulate.assert_called_once()
    ethereum_flashbot_api.flashbots.send_bundle.assert_called_once()
    ethereum_flashbot_api.flashbots.cancel_bundles.assert_called_once()
    assert tx_hashes is None


def test_send_bundle_with_failed_simulation(ethereum_flashbot_api) -> None:
    """Test send bundle with failed simulation."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.bundle_hash = MagicMock()
    response_mock.receipts = MagicMock(side_effect=TransactionNotFound)
    ethereum_flashbot_api.api.eth.get_block_number = MagicMock(return_value=1)
    ethereum_flashbot_api.simulate = MagicMock(return_value=False)
    target_blocks = [0]

    # run
    tx_hashes = ethereum_flashbot_api.send_bundle(MagicMock(), target_blocks)

    # check
    assert tx_hashes is None


def test_send_bundle_with_failed_simulation_and_raise(ethereum_flashbot_api) -> None:
    """Test send bundle with failed simulation and should raise."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.bundle_hash = MagicMock()
    response_mock.receipts = MagicMock(side_effect=TransactionNotFound)
    ethereum_flashbot_api.api.eth.get_block_number = MagicMock(return_value=0)
    ethereum_flashbot_api.simulate = MagicMock(return_value=False)
    raise_on_failed_simulation = True
    target_blocks = [1]

    # run
    with pytest.raises(ValueError):
        ethereum_flashbot_api.send_bundle(
            MagicMock(), target_blocks, raise_on_failed_simulation
        )


def test_send_bundle_with_bad_target_block(ethereum_flashbot_api) -> None:
    """Test send bundle with an old target block should return None."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.bundle_hash = MagicMock()
    response_mock.receipts = MagicMock(side_effect=TransactionNotFound)
    ethereum_flashbot_api.api.eth.get_block_number = MagicMock(return_value=1)
    ethereum_flashbot_api.simulate = MagicMock(return_value=True)
    raise_on_failed_simulation = True
    target_blocks = [0]

    # run
    res = ethereum_flashbot_api.send_bundle(
        MagicMock(), target_blocks, raise_on_failed_simulation
    )
    assert res is None, "Should return None if target block is old"
