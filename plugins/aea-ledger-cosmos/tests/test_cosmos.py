# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest  # type:ignore
from aea_ledger_cosmos import CosmosApi, CosmosCrypto, CosmosHelper
from aea_ledger_cosmos.cosmos import _default_logger as cosmos_logger

from tests.conftest import COSMOS_TESTNET_CONFIG, ROOT_DIR


@pytest.fixture(scope="session")
def cosmos_private_key_file():
    """Pytest fixture to create a temporary Cosmos private key file."""
    crypto = CosmosCrypto()
    temp_dir = Path(tempfile.mkdtemp())
    try:
        temp_file = temp_dir / "private.key"
        temp_file.write_text(crypto.private_key)
        yield str(temp_file)
    finally:
        shutil.rmtree(temp_dir)


def test_creation(cosmos_private_key_file):
    """Test the creation of the crypto_objects."""
    assert CosmosCrypto(), "Did not manage to initialise the crypto module"
    assert CosmosCrypto(
        cosmos_private_key_file
    ), "Did not manage to load the cosmos private key"


def test_key_file_encryption_decryption(cosmos_private_key_file):
    """Test cosmos private key encrypted and decrypted correctly."""
    cosmos = CosmosCrypto(cosmos_private_key_file)
    pk_data = Path(cosmos_private_key_file).read_text()
    password = uuid4().hex
    encrypted_data = cosmos.encrypt(password)
    decrypted_data = cosmos.decrypt(encrypted_data, password)
    assert encrypted_data != pk_data
    assert pk_data == decrypted_data

    with pytest.raises(ValueError, match="Decrypt error! Bad password?"):
        cosmos.decrypt(encrypted_data, "BaD_PassWord")

    with pytest.raises(ValueError, match="Bad encrypted key format!"):
        cosmos.decrypt("some_data" * 16, "BaD_PassWord")


def test_initialization():
    """Test the initialisation of the variables."""
    account = CosmosCrypto()
    assert account.entity is not None, "The property must return the account."
    assert (
        account.address is not None
    ), "After creation the display address must not be None"
    assert account.address.startswith("cosmos")
    assert (
        account.public_key is not None
    ), "After creation the public key must no be None"


def test_sign_and_recover_message(cosmos_private_key_file):
    """Test the signing and the recovery of a message."""
    account = CosmosCrypto(cosmos_private_key_file)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = CosmosApi.recover_message(
        message=b"hello", signature=sign_bytes
    )
    assert (
        account.address in recovered_addresses
    ), "Failed to recover the correct address."


def test_sign_and_recover_message_public_key(cosmos_private_key_file):
    """Test the signing and the recovery function for the eth_crypto."""
    COSMOS_PRIVATE_KEY_PATH = os.path.join(
        ROOT_DIR, "tests", "data", "cosmos_private_key.txt"
    )
    account = CosmosCrypto(COSMOS_PRIVATE_KEY_PATH)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_public_keys = CosmosApi.recover_public_keys_from_message(
        message=b"hello", signature=sign_bytes
    )
    assert len(recovered_public_keys) == 2, "Wrong number of public keys recovered."
    assert (
        CosmosApi.get_address_from_public_key(recovered_public_keys[0])
        == account.address
    ), "Failed to recover the correct address."


def test_get_hash():
    """Test the get hash functionality."""
    expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    hash_ = CosmosApi.get_hash(message=b"hello")
    assert expected_hash == hash_


def test_dump_positive(cosmos_private_key_file):
    """Test dump."""
    account = CosmosCrypto(cosmos_private_key_file)
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


def test_validate_address():
    """Test the is_valid_address functionality."""
    account = CosmosCrypto()
    assert CosmosApi.is_valid_address(account.address)
    assert not CosmosApi.is_valid_address(account.address + "wrong")


def test_load_contract_interface():
    """Test the load_contract_interface method."""
    path = Path(ROOT_DIR, "tests", "data", "dummy_contract", "build", "some.wasm")
    result = CosmosApi.load_contract_interface(path)
    assert "wasm_byte_code" in result


def test_helper_is_settled():
    """Test CosmosHelper.is_transaction_settled."""
    assert CosmosHelper.is_transaction_settled({"code": None}) is True
    with patch.object(cosmos_logger, "warning") as warning_mock:
        assert CosmosHelper.is_transaction_settled({"code": "some value"}) is False
        warning_mock.assert_called_once()


def test_helper_get_code_id():
    """Test CosmosHelper.is_transaction_settled."""
    assert (
        CosmosHelper.get_code_id(
            {
                "logs": [
                    {
                        "msg_index": 0,
                        "log": "",
                        "events": [
                            {
                                "type": "message",
                                "attributes": [
                                    {"key": "action", "value": "store-code"},
                                    {"key": "module", "value": "wasm"},
                                    {
                                        "key": "signer",
                                        "value": "fetch1pa7q6urt98dfe2rsvfaefj8zhh792sdfuzym2t",
                                    },
                                    {"key": "code_id", "value": "631"},
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        == 631
    )


def test_helper_get_contract_address():
    """Test CosmosHelper.is_transaction_settled."""
    assert (
        CosmosHelper.get_contract_address(
            {
                "logs": [
                    {
                        "msg_index": 0,
                        "log": "",
                        "events": [
                            {
                                "type": "message",
                                "attributes": [
                                    {"key": "action", "value": "instantiate"},
                                    {"key": "module", "value": "wasm"},
                                    {
                                        "key": "signer",
                                        "value": "fetch1pa7q6urt98dfe2rsvfaefj8zhh792sdfuzym2t",
                                    },
                                    {"key": "code_id", "value": "631"},
                                    {
                                        "key": "_contract_address",
                                        "value": "fetch1lhd5t8jdjn0n4q27hsah6c0907nxrswcp5l4nw",
                                    },
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        == "fetch1lhd5t8jdjn0n4q27hsah6c0907nxrswcp5l4nw"
    )


@patch.object(
    CosmosApi, "_try_get_account_number_and_sequence", return_value=(None, None)
)
def test_cosmos_api_get_deploy_transaction(*args):
    """Test CosmosApi._get_deploy_transaction."""
    cosmos_api = CosmosApi()
    assert cosmos_api.get_deploy_transaction(*[Mock()] * 2) is None


@patch.object(
    CosmosApi, "_try_get_account_number_and_sequence", return_value=(None, None)
)
def test_cosmos_api_get_handle_transaction(*args):
    """Test CosmosApi.get_handle_transaction."""
    cosmos_api = CosmosApi()
    assert cosmos_api.get_handle_transaction(*[Mock()] * 7) is None


@patch.object(
    CosmosApi, "_try_get_account_number_and_sequence", return_value=(None, None)
)
def test_cosmos_api_get_transfer_transaction(*args):
    """Test CosmosApi.get_transfer_transaction."""
    cosmos_api = CosmosApi()
    assert cosmos_api.get_transfer_transaction(*[Mock()] * 7) is None
