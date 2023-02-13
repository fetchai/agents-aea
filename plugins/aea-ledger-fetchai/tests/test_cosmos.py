# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
"""This module contains the tests of the fetchai._cosmos module."""
from unittest.mock import Mock, patch

import pytest
from aea_ledger_fetchai import CosmosHelper, FetchAIApi, FetchAICrypto
from aea_ledger_fetchai.fetchai import MAXIMUM_GAS_AMOUNT
from cosmpy.auth.rest_client import QueryAccountResponse

from tests.conftest import MAX_FLAKY_RERUNS


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_is_tx_settled() -> None:
    """Test is_tx_settled."""
    assert FetchAIApi.is_transaction_settled({"code": None})
    assert FetchAIApi.is_transaction_settled({})
    assert not FetchAIApi.is_transaction_settled({"code": False})


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_is_transaction_valid() -> None:
    """Test is_transaction_valid."""
    assert not CosmosHelper.is_transaction_valid(None, 1, 2, 3, 4)
    tx_good = {
        "tx": {
            "body": {
                "messages": [
                    {"fromAddress": 1, "toAddress": 2, "amount": [{"amount": 4}]}
                ]
            }
        }
    }
    assert CosmosHelper.is_transaction_valid(tx_good, 2, 1, 3, 4)
    assert not CosmosHelper.is_transaction_valid(tx_good, 2, 2, 3, 4)


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_transfer_transaction() -> None:
    """Test get_transfer_transaction."""
    fetchai_api = FetchAIApi()
    with patch.object(
        fetchai_api, "_try_get_account_number_and_sequence", return_value=[100, 200]
    ):
        transfer_tx = fetchai_api.get_transfer_transaction(
            "2", "1", 4, 6, 5, gas=MAXIMUM_GAS_AMOUNT + 1
        )
    assert transfer_tx["tx"]["authInfo"]["fee"]["gasLimit"] == f"{MAXIMUM_GAS_AMOUNT}"
    assert CosmosHelper.is_transaction_valid(transfer_tx, "1", "2", 3, 4)


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_packed_send_msg() -> None:
    """Test get_packed_send_msg."""
    assert (
        "cosmos.bank.v1beta1.MsgSend"
        in FetchAIApi().get_packed_send_msg(1, 2, 3, b"4").type_url
    )


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_multi_transaction() -> None:
    """Test get_multi_transaction."""
    crypto = FetchAICrypto()
    fetchai_api = FetchAIApi()

    with patch.object(
        fetchai_api, "_try_get_account_number_and_sequence", return_value=[100, 200]
    ):
        result = fetchai_api.get_multi_transaction(
            from_addresses=[crypto.address],
            pub_keys=[bytes.fromhex(crypto.public_key)],
            msgs=[],
            gas=12,
        )
        assert "tx" in result


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_packed_exec_msg() -> None:
    """Test get_packed_exec_msg."""
    crypto = FetchAICrypto()
    fetchai_api = FetchAIApi()

    with patch.object(
        fetchai_api, "_try_get_account_number_and_sequence", return_value=[100, 200]
    ):
        result = fetchai_api.get_packed_exec_msg(
            contract_address=crypto.address,
            sender_address=crypto.address,
            msg={"some": 12},
        )
        assert "MsgExecuteContract" in result.type_url


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_try_get_account_number_and_sequence() -> None:
    """Test _try_get_account_number_and_sequence."""
    fetchai_api = FetchAIApi()
    resp = b"\nV\n /cosmos.auth.v1beta1.BaseAccount\x122\n,fetch1k9dns2fd74644g0q9mfpsmfeqg0h2ym2cm6wdh\x18\xfc\x80\x04"
    msg = QueryAccountResponse()
    msg.ParseFromString(resp)
    with patch.object(fetchai_api.auth_client, "Account", return_value=msg):
        assert fetchai_api._try_get_account_number_and_sequence(
            address="fetch1k9dns2fd74644g0q9mfpsmfeqg0h2ym2cm6wdh"
        ) == (65660, 0)


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_transaction() -> None:
    """Test get_transaction."""
    fetchai_api = FetchAIApi(address="https://rest-fetchhub.fetch.ai:443")
    assert "tx" in fetchai_api.get_transaction(
        "A17E2EEA507D00081826031565F9870771733BBFB62F31FBC356D8AAAC8CBAC8"
    )


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_send_signed_transaction() -> None:
    """Test send_signed_transaction."""
    fetchai_api = FetchAIApi()
    resp_mock = Mock()
    resp_mock.tx_response.code = -1
    with patch.object(fetchai_api.tx_client, "BroadcastTx", return_value=resp_mock):
        assert fetchai_api.send_signed_transaction({"tx": {"body": {}}}) is None

    resp_mock.tx_response.code = 0
    with patch.object(fetchai_api.tx_client, "BroadcastTx", return_value=resp_mock):
        assert fetchai_api.send_signed_transaction({"tx": {"body": {}}}) is not None


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_transaction_receipt() -> None:
    """Test get_transaction_receipt."""
    fetchai_api = FetchAIApi(address="https://rest-fetchhub.fetch.ai:443")
    assert "tx" in fetchai_api.get_transaction_receipt(
        "A17E2EEA507D00081826031565F9870771733BBFB62F31FBC356D8AAAC8CBAC8"
    )


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_handle_transaction() -> None:
    """Test get_handle_transaction."""
    fetchai_api = FetchAIApi()
    with patch.object(
        fetchai_api, "_try_get_account_number_and_sequence", return_value=[100, 200]
    ):
        result = fetchai_api.get_handle_transaction(
            sender_address="1", contract_address="2", handle_msg="", amount=3, tx_fee=4
        )

        assert "tx" in result


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
def test_get_deploy_transaction() -> None:
    """Test get_deploy_transaction."""
    fetchai_api = FetchAIApi()
    with patch.object(
        fetchai_api, "_try_get_account_number_and_sequence", return_value=[100, 200]
    ):
        result = fetchai_api.get_deploy_transaction(
            contract_interface={"wasm_byte_code": "some"},
            deployer_address="Address",
        )

        assert "tx" in result
