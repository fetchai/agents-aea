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
"""This module contains the tests of the fetchai module."""
import base64
import json
import logging
import shutil
import tempfile
import time
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest
from aea_ledger_fetchai import FetchAIApi, FetchAICrypto, FetchAIFaucetApi
from cosmpy.protos.cosmos.bank.v1beta1.tx_pb2 import MsgSend
from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin
from google.protobuf.any_pb2 import Any as ProtoAny

from aea.crypto.helpers import KeyIsIncorrect

from tests.conftest import FETCHAI_TESTNET_CONFIG, MAX_FLAKY_RERUNS, ROOT_DIR


@pytest.fixture
def fetchai_private_key_file():
    """Pytest fixture to create a temporary FetchAI private key file."""
    crypto = FetchAICrypto()
    temp_dir = Path(tempfile.mkdtemp())
    try:
        temp_file = temp_dir / "private.key"
        temp_file.write_text(crypto.private_key)
        yield str(temp_file)
    finally:
        shutil.rmtree(temp_dir)


class MockRequestsResponse:
    """Mock of request response."""

    def __init__(self, data, status_code=None):
        """Initialize mock of request response."""
        self._data = data
        self._status_code = status_code or 200

    @property
    def status_code(self):
        """Get status code."""
        return 200

    def json(self):
        """Get json."""
        return self._data


def test_creation(fetchai_private_key_file):
    """Test the creation of the crypto_objects."""
    assert FetchAICrypto(), "Did not manage to initialise the crypto module"
    assert FetchAICrypto(
        fetchai_private_key_file
    ), "Did not manage to load the cosmos private key"


def test_key_file_encryption_decryption(fetchai_private_key_file):
    """Test fetchai private key encrypted and decrypted correctly."""
    fetchai = FetchAICrypto(fetchai_private_key_file)
    pk_data = Path(fetchai_private_key_file).read_text()
    password = uuid4().hex
    encrypted_data = fetchai.encrypt(password)
    decrypted_data = fetchai.decrypt(encrypted_data, password)
    assert encrypted_data != pk_data
    assert pk_data == decrypted_data

    with pytest.raises(ValueError, match="Decrypt error! Bad password?"):
        fetchai.decrypt(encrypted_data, "BaD_PassWord")

    with pytest.raises(ValueError, match="Bad encrypted key format!"):
        fetchai.decrypt("some_data" * 16, "BaD_PassWord")


def test_initialization():
    """Test the initialisation of the variables."""
    account = FetchAICrypto()
    assert account.entity is not None, "The property must return the account."
    assert (
        account.address is not None
    ), "After creation the display address must not be None"
    assert account.address.startswith("fetch")
    assert (
        account.public_key is not None
    ), "After creation the public key must no be None"


def test_sign_and_recover_message(fetchai_private_key_file):
    """Test the signing and the recovery of a message."""
    account = FetchAICrypto(fetchai_private_key_file)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = FetchAIApi.recover_message(
        message=b"hello", signature=sign_bytes
    )
    assert (
        account.address in recovered_addresses
    ), "Failed to recover the correct address."


def test_get_hash():
    """Test the get hash functionality."""
    expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    hash_ = FetchAIApi.get_hash(message=b"hello")
    assert expected_hash == hash_


def test_dump_positive(fetchai_private_key_file):
    """Test dump."""
    account = FetchAICrypto(fetchai_private_key_file)
    account.dump(MagicMock())


def test_api_creation():
    """Test api instantiation."""
    assert FetchAIApi(**FETCHAI_TESTNET_CONFIG), "Failed to initialise the api"


def test_api_none():
    """Test the "api" of the cryptoApi is none."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    assert fetchai_api.api is None, "The api property is not None."


def test_generate_nonce():
    """Test generate nonce."""
    nonce = FetchAIApi.generate_tx_nonce(
        seller="some_seller_addr", client="some_buyer_addr"
    )
    assert len(nonce) > 0 and int(
        nonce, 16
    ), "The len(nonce) must not be 0 and must be hex"


def test_get_address_from_public_key():
    """Test the address from public key."""
    fet_crypto = FetchAICrypto()
    address = FetchAIApi.get_address_from_public_key(fet_crypto.public_key)
    assert address == fet_crypto.address, "The address must be the same."


def test_validate_address():
    """Test the is_valid_address functionality."""
    account = FetchAICrypto()
    assert FetchAIApi.is_valid_address(account.address)
    assert not FetchAIApi.is_valid_address(account.address + "wrong")


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_construct_sign_and_submit_transfer_transaction():
    """Test the construction, signing and submitting of a transfer transaction."""
    account = FetchAICrypto()
    balance = get_wealth(account.address)
    assert balance > 0, "Failed to fund account."
    fc2 = FetchAICrypto()
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    amount = 10000
    assert amount < balance, "Not enough funds."
    transfer_transaction = fetchai_api.get_transfer_transaction(
        sender_address=account.address,
        destination_address=fc2.address,
        amount=amount,
        tx_fee=1000,
        tx_nonce="something",
    )
    assert (
        isinstance(transfer_transaction, dict) and len(transfer_transaction) == 2
    ), "Incorrect transfer_transaction constructed."

    signed_transaction = account.sign_transaction(transfer_transaction)
    assert (
        isinstance(signed_transaction, dict)
        and len(signed_transaction["tx"]) == 3
        and isinstance(signed_transaction["tx"]["signatures"], list)
    ), "Incorrect signed_transaction constructed."

    transaction_digest = fetchai_api.send_signed_transaction(signed_transaction)
    assert transaction_digest is not None, "Failed to submit transfer transaction!"

    not_settled = True
    elapsed_time = 0
    while not_settled and elapsed_time < 20:
        elapsed_time += 1
        time.sleep(2)
        transaction_receipt = fetchai_api.get_transaction_receipt(transaction_digest)
        if transaction_receipt is None:
            continue
        is_settled = fetchai_api.is_transaction_settled(transaction_receipt)
        not_settled = not is_settled
    assert transaction_receipt is not None, "Failed to retrieve transaction receipt."
    assert is_settled, "Failed to verify tx!"

    tx = fetchai_api.get_transaction(transaction_digest)
    is_valid = fetchai_api.is_transaction_valid(
        tx, fc2.address, account.address, "", amount
    )
    assert is_valid, "Failed to settle tx correctly!"


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_balance():
    """Test the balance is zero for a new account."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    fc = FetchAICrypto()
    balance = fetchai_api.get_balance(fc.address)
    assert balance == 0, "New account has a positive balance."
    balance = get_wealth(fc.address)
    assert balance > 0, "Existing account has no balance."


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_state():
    """Test that get_state() with 'blocks' function returns something containing the block height."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    callable_name = "blocks"
    args = ("latest",)
    block = fetchai_api.get_state(callable_name, *args)
    assert block is not None, "No response to 'blocks/latest' query."
    assert (
        block["block"]["header"]["height"] is not None
    ), "Block height not found in response."


def get_wealth(address: str):
    """Get wealth for test."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    FetchAIFaucetApi().get_wealth(address)
    balance = 0
    timeout = 0
    while timeout < 40 and balance == 0:
        time.sleep(1)
        timeout += 1
        _balance = fetchai_api.get_balance(address)
        balance = _balance if _balance is not None else 0
    return balance


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_wealth_positive(caplog):
    """Test the balance is zero for a new account."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.fetchai._default_logger"):
        fetchai_faucet_api = FetchAIFaucetApi()
        fc = FetchAICrypto()
        fetchai_faucet_api.get_wealth(fc.address)


@pytest.mark.ledger
@mock.patch("aea_ledger_fetchai._cosmos.requests.get")
@mock.patch("aea_ledger_fetchai._cosmos.requests.post")
def test_successful_faucet_operation(mock_post, mock_get):
    """Test successful faucet operation."""
    address = "a normal cosmos address would be here"
    mock_post.return_value = MockRequestsResponse({"uuid": "a-uuid-v4-would-be-here"})

    mock_get.return_value = MockRequestsResponse(
        {
            "status": "ok",
            "claim": {
                "createdAt": "2021-08-13T15:18:50.420Z",
                "updatedAt": "2021-08-13T15:18:58.249Z",
                "status": FetchAIFaucetApi.FAUCET_STATUS_COMPLETED,
                "txStatus": {
                    "hash": "0x transaction hash would be here",
                    "height": 123456,
                },
            },
        }
    )

    faucet = FetchAIFaucetApi()
    faucet.get_wealth(address)

    mock_post.assert_has_calls(
        [
            call(
                url=f"{FetchAIFaucetApi.testnet_faucet_url}/api/v3/claims",
                json={"address": address},
            )
        ]
    )
    mock_get.assert_has_calls(
        [
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/api/v3/claims/a-uuid-v4-would-be-here"
            )
        ]
    )


@pytest.mark.ledger
@mock.patch("aea_ledger_fetchai._cosmos.requests.get")
@mock.patch("aea_ledger_fetchai._cosmos.requests.post")
def test_successful_realistic_faucet_operation(mock_post, mock_get):
    """Test successful realistic faucet operation."""
    address = "a normal cosmos address would be here"
    mock_post.return_value = MockRequestsResponse({"uuid": "a-uuid-v4-would-be-here"})

    mock_get.side_effect = [
        MockRequestsResponse(
            {
                "status": "ok",
                "claim": {
                    "createdAt": "2021-08-13T15:18:50.420Z",
                    "updatedAt": "2021-08-13T15:18:58.249Z",
                    "status": FetchAIFaucetApi.FAUCET_STATUS_PENDING,
                },
            }
        ),
        MockRequestsResponse(
            {
                "status": "ok",
                "claim": {
                    "createdAt": "2021-08-13T15:18:50.420Z",
                    "updatedAt": "2021-08-13T15:18:58.249Z",
                    "status": FetchAIFaucetApi.FAUCET_STATUS_PENDING,
                },
            }
        ),
        MockRequestsResponse(
            {
                "status": "ok",
                "claim": {
                    "createdAt": "2021-08-13T15:18:50.420Z",
                    "updatedAt": "2021-08-13T15:18:58.249Z",
                    "status": FetchAIFaucetApi.FAUCET_STATUS_COMPLETED,
                    "txStatus": {
                        "hash": "0x transaction hash would be here",
                        "height": 123456,
                    },
                },
            }
        ),
    ]

    faucet = FetchAIFaucetApi(poll_interval=0)
    faucet.get_wealth(address)

    mock_post.assert_has_calls(
        [
            call(
                url=f"{FetchAIFaucetApi.testnet_faucet_url}/api/v3/claims",
                json={"address": address},
            )
        ]
    )
    mock_get.assert_has_calls(
        [
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/api/v3/claims/a-uuid-v4-would-be-here"
            ),
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/api/v3/claims/a-uuid-v4-would-be-here"
            ),
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/api/v3/claims/a-uuid-v4-would-be-here"
            ),
        ]
    )


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_format_default():
    """Test if default CosmosSDK transaction is correctly formatted."""
    account = FetchAICrypto()
    cc2 = FetchAICrypto()
    cosmos_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    amount = 10000

    transfer_transaction = cosmos_api.get_transfer_transaction(
        sender_address=account.address,
        destination_address=cc2.address,
        amount=amount,
        tx_fee=1000,
        tx_nonce="something",
        account_number=1,
        sequence=0,
    )

    signed_transaction = account.sign_transaction(transfer_transaction)

    assert "tx" in signed_transaction
    assert "signatures" in signed_transaction["tx"]
    assert len(signed_transaction["tx"]["signatures"]) == 1

    assert "publicKey" in signed_transaction["tx"]["authInfo"]["signerInfos"][0]
    assert "key" in signed_transaction["tx"]["authInfo"]["signerInfos"][0]["publicKey"]
    base64_pbk = signed_transaction["tx"]["authInfo"]["signerInfos"][0]["publicKey"][
        "key"
    ]

    pbk = base64.b64decode(base64_pbk)
    assert pbk == bytes.fromhex(account.public_key)
    assert len(signed_transaction["tx"]["signatures"][0]) == 88
    signature = base64.b64decode(signed_transaction["tx"]["signatures"][0])
    assert len(signature) == 64


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_storage_transaction_cosmwasm():
    """Test the get storage transaction method."""
    cc2 = FetchAICrypto()
    cosmos_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    contract_interface = {"wasm_byte_code": "1234"}
    deployer_address = cc2.address
    deploy_transaction = cosmos_api.get_deploy_transaction(
        contract_interface, deployer_address, account_number=1, sequence=0,
    )

    assert type(deploy_transaction) == dict and len(deploy_transaction) == 2
    # Check sign_data
    assert "account_number" in deploy_transaction["sign_data"][cc2.address]
    assert "chain_id" in deploy_transaction["sign_data"][cc2.address]

    # Check msg
    assert len(deploy_transaction["tx"]["body"]["messages"]) == 1
    msg = deploy_transaction["tx"]["body"]["messages"][0]
    assert "@type" in msg and msg["@type"] == "/cosmwasm.wasm.v1beta1.MsgStoreCode"

    assert msg["sender"] == deployer_address
    assert msg["wasmByteCode"] == contract_interface["wasm_byte_code"]


@pytest.mark.integration
@pytest.mark.ledger
def test_get_init_transaction_cosmwasm():
    """Test the get deploy transaction method."""
    cc2 = FetchAICrypto()
    cosmos_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    init_msg = "init_msg"
    code_id = 1
    deployer_address = cc2.address
    tx_fee = 1
    amount = 10
    gas_limit = 1234
    contract_interface = {}
    init_transaction = cosmos_api.get_deploy_transaction(
        contract_interface,
        deployer_address,
        code_id=code_id,
        init_msg=init_msg,
        amount=amount,
        tx_fee=tx_fee,
        label="",
        account_number=1,
        sequence=0,
        gas=gas_limit,
        denom="abc",
        tx_fee_denom="def",
    )

    assert type(init_transaction) == dict and len(init_transaction) == 2

    # Check sign_data
    assert "account_number" in init_transaction["sign_data"][cc2.address]
    assert "chain_id" in init_transaction["sign_data"][cc2.address]

    # Check tx
    assert init_transaction["tx"]["authInfo"]["fee"]["amount"] == [
        {"denom": "def", "amount": str(tx_fee)}
    ]

    # Check msg
    assert len(init_transaction["tx"]["body"]["messages"]) == 1
    msg = init_transaction["tx"]["body"]["messages"][0]
    assert (
        "@type" in msg
        and msg["@type"] == "/cosmwasm.wasm.v1beta1.MsgInstantiateContract"
    )
    assert msg["sender"] == deployer_address
    assert msg["codeId"] == str(code_id)
    assert base64.b64decode(msg["initMsg"]).decode() == f'"{init_msg}"'
    assert msg["funds"] == [{"denom": "abc", "amount": str(amount)}]


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_handle_transaction_cosmwasm():
    """Test the get deploy transaction method."""
    cc2 = FetchAICrypto()

    cosmos_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    handle_msg = "handle_msg"
    sender_address = cc2.address
    contract_address = "contract_address"
    tx_fee = 1
    amount = 10
    gas_limit = 1234
    handle_transaction = cosmos_api.get_handle_transaction(
        sender_address,
        contract_address,
        handle_msg,
        amount,
        tx_fee,
        gas=gas_limit,
        memo="memo",
        account_number=1,
        sequence=0,
        denom="abc",
        tx_fee_denom="def",
    )

    assert type(handle_transaction) == dict and len(handle_transaction) == 2

    # Check sign_data
    assert "account_number" in handle_transaction["sign_data"][cc2.address]
    assert "chain_id" in handle_transaction["sign_data"][cc2.address]

    # Check tx
    assert handle_transaction["tx"]["authInfo"]["fee"] == {
        "amount": [{"denom": "def", "amount": str(tx_fee)}],
        "gasLimit": str(gas_limit),
    }

    assert "memo" in handle_transaction["tx"]["body"]

    # Check msg
    assert len(handle_transaction["tx"]["body"]["messages"]) == 1
    msg = handle_transaction["tx"]["body"]["messages"][0]
    assert (
        "@type" in msg and msg["@type"] == "/cosmwasm.wasm.v1beta1.MsgExecuteContract"
    )
    assert msg["sender"] == sender_address
    assert msg["contract"] == contract_address
    assert base64.b64decode(msg["msg"]).decode() == f'"{handle_msg}"'
    assert msg["funds"] == [{"denom": "abc", "amount": str(amount)}]


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_try_execute_wasm_query():
    """Test the execute wasm query method."""
    cosmos_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    client_mock = mock.Mock()

    output_raw_mock = mock.Mock()
    output_raw_mock.data = '{"output": 1}'

    attrs = {"SmartContractState.return_value": output_raw_mock}
    client_mock.configure_mock(**attrs)
    cosmos_api.wasm_client = client_mock
    result = cosmos_api.execute_contract_query(
        contract_address="contract_address", query_msg={}
    )
    assert result == json.loads(output_raw_mock.data)


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_send_signed_transaction():
    """Test the send_signed_transaction method"""
    cosmos_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    tx_signed = cosmos_api.get_transfer_transaction(
        sender_address="addr1",
        destination_address="addr2",
        amount=123,
        tx_fee=1000,
        tx_nonce="something",
        account_number=1,
        sequence=0,
    )

    # Mock version of protobuf Tx response
    mock_return_value = mock.Mock()
    mock_tx_response = mock.Mock()
    mock_tx_response.code = 0
    mock_tx_response.txhash = "digest"
    mock_return_value.tx_response = mock_tx_response

    with mock.patch.object(
        cosmos_api.tx_client, "BroadcastTx", return_value=mock_return_value
    ):
        result = cosmos_api.send_signed_transaction(tx_signed=tx_signed)
    assert result == "digest"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_contract_instance():
    """Test the get contract instance method."""
    cosmos_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    assert cosmos_api.get_contract_instance("interface") is None


def test_helper_get_code_id():
    """Test CosmosHelper.is_transaction_settled."""
    assert (
        FetchAIApi.get_code_id(
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
        FetchAIApi.get_contract_address(
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
                                        "key": "contract_address",
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


def test_load_contract_interface():
    """Test the load_contract_interface method."""
    path = Path(ROOT_DIR, "tests", "data", "dummy_contract", "build", "some.wasm")
    result = FetchAIApi.load_contract_interface(path)
    assert "wasm_byte_code" in result


@pytest.mark.integration
@pytest.mark.ledger
def test_construct_init_transaction():
    """Test the construction of a contract instantiate transaction"""
    account = FetchAICrypto()
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    init_transaction = fetchai_api._get_init_transaction(
        deployer_address=account.address,
        denom="atestfet",
        chain_id="cosmoshub-3",
        account_number=1,
        sequence=1,
        amount=0,
        code_id=200,
        init_msg={},
        label="something",
        tx_fee_denom="stake",
    )
    assert (
        isinstance(init_transaction, dict) and len(init_transaction) == 2
    ), "Incorrect transfer_transaction constructed."
    assert (
        init_transaction["tx"]["body"]["messages"][0]["@type"]
        == "/cosmwasm.wasm.v1beta1.MsgInstantiateContract"
    )


@pytest.mark.integration
@pytest.mark.ledger
def test_construct_handle_transaction():
    """Test the construction of a transfer transaction."""
    account = FetchAICrypto()
    account2 = FetchAICrypto()
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    transaction = fetchai_api.get_handle_transaction(
        sender_address=account.address,
        contract_address=account2.address,
        handle_msg={},
        amount=0,
        tx_fee=100,
        denom="atestfet",
        account_number=1,
        sequence=0,
    )
    assert (
        isinstance(transaction, dict) and len(transaction) == 2
    ), "Incorrect transfer_transaction constructed."
    assert (
        transaction["tx"]["body"]["messages"][0]["@type"]
        == "/cosmwasm.wasm.v1beta1.MsgExecuteContract"
    )


def test_load_errors():
    """Test load errors: bad password, no password specified."""
    ec = FetchAICrypto()
    with patch.object(FetchAICrypto, "load", return_value="bad sTring"):
        with pytest.raises(KeyIsIncorrect, match="Try to specify `password`"):
            ec.load_private_key_from_path("any path")

        with pytest.raises(KeyIsIncorrect, match="Wrong password?"):
            ec.load_private_key_from_path("any path", password="some")


def test_decrypt_error():
    """Test bad password error on decrypt."""
    ec = FetchAICrypto()
    ec._pritvate_key = FetchAICrypto.generate_private_key()
    password = "test"
    encrypted_data = ec.encrypt(password=password)
    with patch(
        "aea_ledger_fetchai._cosmos.DataEncrypt.decrypt",
        side_effect=UnicodeDecodeError("expected", b"", 2, 3, ""),
    ):
        with pytest.raises(ValueError, match="bad password?"):
            ec.decrypt(encrypted_data, password + "some")


@pytest.mark.integration
@pytest.mark.ledger
def test_multiple_signatures_transaction():
    """Test generating message with multiple signers"""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    coins = [Coin(denom="DENOM", amount="1234")]

    msg_send = MsgSend(from_address=str("from"), to_address=str("to"), amount=coins,)
    send_msg_packed = ProtoAny()
    send_msg_packed.Pack(msg_send, type_url_prefix="/")

    tx = fetchai_api._get_transaction(
        account_numbers=[1, 2],
        from_addresses=["adr1", "adr2"],
        pub_keys=[b"1", b"2"],
        chain_id="chain_id",
        tx_fee=coins,
        gas=1234,
        memo="MEMO",
        sequences=[1, 2],
        msgs=[send_msg_packed, send_msg_packed],
    )
    assert (
        isinstance(tx, dict) and len(tx) == 2
    ), "Incorrect transfer_transaction constructed."
    assert tx["tx"]["body"]["messages"][0]["@type"] == "/cosmos.bank.v1beta1.MsgSend"
    assert tx["tx"]["body"]["messages"][1]["@type"] == "/cosmos.bank.v1beta1.MsgSend"


@pytest.mark.integration
@pytest.mark.ledger
def test_multiple_signatures_transaction_missing_pubkeys():
    """Test if generating message with multiple signers without pubkeys fails"""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    coins = [Coin(denom="DENOM", amount="1234")]

    msg_send = MsgSend(from_address=str("from"), to_address=str("to"), amount=coins,)
    send_msg_packed = ProtoAny()
    send_msg_packed.Pack(msg_send, type_url_prefix="/")

    with pytest.raises(
        RuntimeError,
        match="Only transaction with one signer can be generated without pubkeys",
    ):
        fetchai_api._get_transaction(
            account_numbers=[1, 2],
            from_addresses=["adr1", "adr2"],
            chain_id="chain_id",
            tx_fee=coins,
            gas=1234,
            memo="MEMO",
            sequences=[1, 2],
            msgs=[send_msg_packed, send_msg_packed],
        )


@pytest.mark.integration
@pytest.mark.ledger
def test_multiple_signatures_transaction_wrong_number_of_params():
    """Test if generating message with wrong number of params fails"""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    coins = [Coin(denom="DENOM", amount="1234")]

    msg_send = MsgSend(from_address=str("from"), to_address=str("to"), amount=coins,)
    send_msg_packed = ProtoAny()
    send_msg_packed.Pack(msg_send, type_url_prefix="/")

    with pytest.raises(
        RuntimeError,
        match="Amount of provided from_addresses, sequences and account_numbers is not equal",
    ):
        fetchai_api._get_transaction(
            account_numbers=[1, 2],
            from_addresses=["adr1", "adr2"],
            chain_id="chain_id",
            tx_fee=coins,
            gas=1234,
            memo="MEMO",
            sequences=[1, 2, 3],
            pub_keys=[b"123"],
            msgs=[send_msg_packed],
        )
