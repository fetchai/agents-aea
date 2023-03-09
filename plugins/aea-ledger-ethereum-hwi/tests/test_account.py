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

"""Test account module."""

from unittest import mock

import pytest
from aea_ledger_ethereum_hwi.account import HWIAccount, HWIErrorCodes
from aea_ledger_ethereum_hwi.exceptions import HWIError
from hexbytes import HexBytes
from ledgerwallet.client import CommException, LedgerClient


DEFAULT_ACCOUNT_RESPONSE = b"A\x01\xfb\x02\xc3\x7f\xdc7B\xd8\x975b[*0\xc4\xb0c-\x1f:P|\xc2}+0\x08\x94\x9f\xf9\xc3?\x9bihO\x03~c\xaekn\xda\xdd\xfaQMo\xcd\xa8\xa0\xb16T\x9c*\x8f\x8e\xc9d\x90F\xf0\xcc(2a5f50C28F04A04B4b9671c02B2fBd757cb51d23\x97\x01nA<e\x08\xd9\x84\x1b\x9a\xbf<My\\E\xb2h\x93\x82$\xf4t\x83\xe2'\xa1a|R\x90"
DEFAULT_TX_RESPONSE = b"\x00\x0e\x14a\n\xf5\x13\xdf\x91\xf0\xbaE\x80\xbb9\x87k:\xd2\x01\xbc\x87\x8a-4\xf9eDT\"$\x01\xda\x0b\xf6\x94\xeb\x1a->Z\xca\xa0\\e\x9e\xe9\xef\x82\xb9\xf8+\xac\xf5\xc6\x0b\x06P\xb2\xd9\xf03\xe7'\x13"
CHAIN_ID = 0
NONCE = 1
ETH_ACCOUNT = "0xe81DE7001292e482D4d1851FF7eD50c56093F8bb"
ETH_PUBLIC_KEY = "0xfb02c37fdc3742d89735625b2a30c4b0632d1f3a507cc27d2b3008949ff9c33f9b69684f037e63ae6b6edaddfa514d6fcda8a0b136549c2a8f8ec9649046f0cc"

enumerate_devices_patch = mock.patch(
    "aea_ledger_ethereum_hwi.account.enumerate_devices",
    return_value=[
        mock.MagicMock(),
    ],
)


def test_get_account() -> None:
    """Test Account.get_account"""

    with mock.patch.object(
        LedgerClient,
        "apdu_exchange",
        return_value=DEFAULT_ACCOUNT_RESPONSE,
    ), enumerate_devices_patch:
        account = HWIAccount().get_account()

    assert account.address == ETH_ACCOUNT
    assert account.public_key == ETH_PUBLIC_KEY


def test_sign_transaction_legacy() -> None:
    """Test sign legacy transaction"""

    account = HWIAccount()
    tx = {
        "chainId": CHAIN_ID,
        "nonce": NONCE,
        "to": ETH_ACCOUNT,
        "value": 1,
        "data": b"",
        "gas": 21000,
        "gasPrice": 1000000000,
    }

    with mock.patch.object(
        LedgerClient,
        "apdu_exchange",
        side_effect=[DEFAULT_ACCOUNT_RESPONSE, DEFAULT_TX_RESPONSE],
    ), enumerate_devices_patch:
        signed_tx = account.sign_transaction(transaction_dict=tx)

    assert signed_tx.rawTransaction == HexBytes(
        "0x01f8658001843b9aca0082520894e81de7001292e482d4d1851ff7ed50c56093f8bb0180c080a00e14610af513df91f0ba4580bb39876b3ad201bc878a2d34f9654454222401daa00bf694eb1a2d3e5acaa05c659ee9ef82b9f82bacf5c60b0650b2d9f033e72713"
    )
    assert signed_tx.hash == HexBytes(
        "0x0c6d3de9e1546f28d17a643c5dab1beb0354d33c3a91f046d30eb805a926009b"
    )
    assert (
        signed_tx.r
        == 6368386586266089348722015307950154351326471210129235368274039816995756835290
    )
    assert (
        signed_tx.s
        == 5411113509154936310743584815502120361180052194242088038643232853217736337171
    )
    assert signed_tx.v == 0


def test_sign_transaction_eip1559() -> None:
    """Test sign eip1559 transaction"""

    account = HWIAccount()
    tx = {
        "chainId": 5,
        "nonce": 7,
        "to": "0xf33BB476529e93Bb862262f6C6D8Cc324741d7aA",
        "value": 1,
        "data": b"",
        "gas": 21000,
        "maxFeePerGas": 170000000000,
        "maxPriorityFeePerGas": 3000000000,
    }

    with mock.patch.object(
        LedgerClient,
        "apdu_exchange",
        side_effect=[DEFAULT_ACCOUNT_RESPONSE, DEFAULT_TX_RESPONSE],
    ), enumerate_devices_patch:
        signed_tx = account.sign_transaction(transaction_dict=tx)

    assert signed_tx.rawTransaction == HexBytes(
        "0x02f86b050784b2d05e00852794ca240082520894f33bb476529e93bb862262f6c6d8cc324741d7aa0180c080a00e14610af513df91f0ba4580bb39876b3ad201bc878a2d34f9654454222401daa00bf694eb1a2d3e5acaa05c659ee9ef82b9f82bacf5c60b0650b2d9f033e72713"
    )
    assert signed_tx.hash == HexBytes(
        "0x5a65b647eb97bd910e8c6ba573503731adaa47213eb02c0c63316e727a46e64e"
    )
    assert (
        signed_tx.r
        == 6368386586266089348722015307950154351326471210129235368274039816995756835290
    )
    assert (
        signed_tx.s
        == 5411113509154936310743584815502120361180052194242088038643232853217736337171
    )
    assert signed_tx.v == 0


def test_exceptions() -> None:
    """Test exceptions."""

    with mock.patch.object(
        LedgerClient,
        "apdu_exchange",
        side_effect=CommException(message="0", sw=HWIErrorCodes.DEVICE_LOCKED),
    ), pytest.raises(HWIError, match="Cannot find any ledger device"):
        HWIAccount().get_account()

    with mock.patch.object(
        LedgerClient,
        "apdu_exchange",
        side_effect=CommException(message="0", sw=HWIErrorCodes.DEVICE_LOCKED),
    ), pytest.raises(HWIError, match="Device is locked"), mock.patch(
        "aea_ledger_ethereum_hwi.account.enumerate_devices",
        return_value=[
            mock.MagicMock(),
        ],
    ):
        HWIAccount().get_account()

    with mock.patch.object(
        LedgerClient,
        "apdu_exchange",
        side_effect=CommException(message="0", sw=HWIErrorCodes.EHTEREUM_APP_NOT_OPEN),
    ), pytest.raises(
        HWIError, match="Please open ethereum app in your device"
    ), mock.patch(
        "aea_ledger_ethereum_hwi.account.enumerate_devices",
        return_value=[
            mock.MagicMock(),
        ],
    ):
        HWIAccount().get_account()
