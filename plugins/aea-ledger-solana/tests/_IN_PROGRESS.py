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
"""This module contains the tests of the solana module."""

import logging
import platform
import time
from pathlib import Path
from typing import Optional, Tuple, Union, cast

import pytest


if platform.system() != "Linux":
    pytest.skip("Runs only on linux", allow_module_level=True)

from aea_ledger_solana import (
    LAMPORTS_PER_SOL,
    PublicKey,
    SolanaApi,
    SolanaCrypto,
    SolanaFaucetApi,
)
from nacl.signing import VerifyKey

from aea.common import JSONLike

from tests.conftest import AIRDROP_AMOUNT, MAX_FLAKY_RERUNS, ROOT_DIR


def retry_airdrop_if_result_none(faucet, address, amount=None):
    """Fund address with faucet."""
    cnt = 0
    tx = None
    while tx is None and cnt < 10:
        tx = faucet.get_wealth(address, amount)
        cnt += 1
        time.sleep(2)
    return tx


def test_get_hash():
    """Test the get hash functionality."""
    expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    hash_ = SolanaApi.get_hash(message=b"hello")
    assert expected_hash == hash_


def test_is_address_valid():
    """Test the get hash functionality."""
    wallet = SolanaCrypto()
    sa = SolanaApi()
    assert sa.is_valid_address(wallet.address)
    assert not sa.is_valid_address("123IamNotReal")


def test_sign_message():
    """Test message sign functionality."""
    wallet = SolanaCrypto()
    wallet2 = SolanaCrypto()
    msg = bytes("hello", "utf8")
    msg2 = bytes("hellooo", "utf8")

    sig = wallet.sign_message(msg)

    try:
        result = VerifyKey(bytes(wallet.public_key)).verify(
            smessage=msg2, signature=bytes(sig.to_bytes_array())
        )
    except Exception as e:
        assert e.args[0] == "Signature was forged or corrupt"

    try:
        result = VerifyKey(bytes(wallet2.public_key)).verify(
            smessage=msg, signature=bytes(sig.to_bytes_array())
        )
    except Exception as e:
        assert e.args[0] == "Signature was forged or corrupt"

    result = VerifyKey(bytes(wallet.public_key)).verify(
        smessage=msg, signature=bytes(sig.to_bytes_array())
    )

    assert result == msg, "Failed to sign message"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_load_contract_interface_from_program_id():
    """Test that you can load contract interface from onchain idl store."""
    solana_api = SolanaApi()
    idl_path = Path(
        ROOT_DIR, "tests", "data", "tic-tac-toe", "target", "idl", "tic_tac_toe.json"
    )
    contract_interface = solana_api.load_contract_interface(idl_file_path=idl_path)

    assert "name" in contract_interface["idl"], "idl has a name"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_tx(caplog, solana_private_key_file):
    """Test get tx from signature"""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.solana._default_logger"):
        sc = SolanaCrypto(private_key_path=solana_private_key_file)
        solana_api = SolanaApi()
        solana_faucet_api = SolanaFaucetApi()

        retries = 0
        tx_signature = None
        while retries < MAX_FLAKY_RERUNS and retries < 1:
            # the faucet almost never succeeds on the first try so a minimum of 1 retry is required.
            tx_signature = solana_faucet_api._try_get_wealth(
                sc.public_key, AIRDROP_AMOUNT
            )
            if tx_signature is None:
                retries += 1
                time.sleep(2)
            else:
                break

        assert tx_signature is not None
        tx, settled = solana_api.wait_get_receipt(tx_signature)
        assert settled is True
        contract_address = solana_api.get_contract_address(tx)
        assert contract_address == "11111111111111111111111111111111"


def test_load_contract_interface():
    """Test the load_contract_interface method."""
    path = Path(ROOT_DIR, "tests", "data", "dummy_contract", "build", "idl.json")
    result = SolanaApi.load_contract_interface(path)

    assert "name" in result["idl"]


def test_load_contract_instance():
    """Test the load_contract_interface method."""
    idl_path = Path(
        ROOT_DIR,
        "tests",
        "data",
        "spl-token-faucet",
        "target",
        "idl",
        "spl_token_faucet.json",
    )
    bytecode_path = Path(
        ROOT_DIR,
        "tests",
        "data",
        "spl-token-faucet",
        "target",
        "deploy",
        "spl_token_faucet.so",
    )
    sa = SolanaApi()
    result = sa.load_contract_interface(
        idl_file_path=idl_path, bytecode_path=bytecode_path
    )
    pid = "ZETAxsqBRek56DhiGXrn75yj2NHU3aYUnxvHXpkf3aD"
    instance = SolanaApi.get_contract_instance(
        SolanaApi, contract_interface=result, contract_address=pid
    )

    assert hasattr(instance["program"], "coder")


