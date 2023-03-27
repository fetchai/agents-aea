"""Test the solana ledger transactions."""

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
from tests.conftest import PROGRAM_KEYPAIR_PATH
from tests.conftest import PLAYER1_KEYPAIR_PATH
from tests.conftest import PLAYER2_KEYPAIR_PATH


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.skip(reason="TODO: fix this test")
def test_funded_transfer_transaction(solana_private_key_file):
    """Test the construction, signing and submitting of a transfer transaction."""
    account1 = SolanaCrypto(PLAYER1_KEYPAIR_PATH)
    account2 = SolanaCrypto(PLAYER2_KEYPAIR_PATH)

    solana_api = SolanaApi()
    solana_faucet_api = SolanaFaucetApi()
    solana_faucet_api.get_wealth(account1.address)
    solana_faucet_api.get_wealth(account2.address)

    balance1 = solana_api.get_balance(account1.public_key)
    balance2 = solana_api.get_balance(account2.public_key)
    assert balance1 >= solana_faucet_api.DEFAULT_AMOUNT
    assert balance2 >= solana_faucet_api.DEFAULT_AMOUNT

    AMOUNT = 2222

    tx_params = {
        "sender_address": account1.public_key,
        "destination_address": account2.public_key,
        "amount": AMOUNT,
    }

    (
        transaction_digest,
        transaction_receipt,
        is_settled,
    ) = solana_api.construct_and_settle_tx(
        account1,
        account2,
        tx_params,
    )
    assert is_settled, "Failed to verify tx!"

    tx = solana_api.get_transaction(transaction_digest)

    assert tx["blockTime"] == transaction_receipt["blockTime"], "Should be same"
    assert balance2 + AMOUNT == solana_api.get_balance(account2.public_key)


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_sol_balance(caplog, solana_private_key_file):
    """Test the balance is zero for a new account."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.solana._default_logger"):
        sc = SolanaCrypto(PLAYER1_KEYPAIR_PATH)
        sa = SolanaApi()

        balance = sa.get_balance(sc.address)
        assert isinstance(balance, int)


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_ledger_state(solana_private_key_file):
    """Test the get_address_from_public_key method"""

    solana_api = SolanaApi()
    account_state = solana_api.get_state("11111111111111111111111111111111")
    assert account_state is not None, "No state retrieved!"
    assert hasattr(account_state, "lamports"), "State not in correct format"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_unfunded_transfer_transaction(
    solana_private_key_file,
):
    """Test the construction, signing and submitting of a transfer transaction."""
    account1 = SolanaCrypto(solana_private_key_file)
    account2 = SolanaCrypto()
    solana_api = SolanaApi()
    faucet = SolanaFaucetApi()

    faucet.generate_wealth_if_needed(
        solana_api, account1.address, faucet.DEFAULT_AMOUNT
    )

    assert solana_api.get_balance(account1.address) >= SolanaFaucetApi.DEFAULT_AMOUNT

    AMOUNT = 1232323
    balance1 = solana_api.get_balance(account1.address)
    balance2 = solana_api.get_balance(account2.address)

    tx_params = {
        "sender_address": PublicKey.from_bytes(account1.public_key),
        "destination_address": PublicKey.from_bytes(account2.public_key),
        "amount": AMOUNT,
    }

    (
        transaction_digest,
        transaction_receipt,
        is_settled,
    ) = solana_api.construct_and_settle_tx(
        account1,
        account2,
        tx_params,
    )
    assert is_settled, "Failed to verify tx!"
    tx = solana_api.get_transaction(transaction_digest)
    assert tx["blockTime"] == transaction_receipt["blockTime"], "Should be same"
    balance3 = solana_api.get_balance(account2.address)
    assert AMOUNT == balance3, "Should be the same balance"


@pytest.mark.skip
def test_get_transaction_transfer_logs(solana_private_key_file):
    """Test SolanaApi.get_transaction_transfer_logs."""
    solana_api = SolanaApi()

    account1 = SolanaCrypto(PLAYER1_KEYPAIR_PATH)

    solana_faucet = SolanaFaucetApi()

    resp = solana_faucet.generate_wealth_if_needed(solana_api, account1.address)
    assert resp != "failed", "Failed to generate wealth"

    account2 = SolanaCrypto()

    balance1 = solana_api.get_balance(account1.public_key)
    balance2 = solana_api.get_balance(account2.public_key)
    assert balance1 > 0
    assert balance2 >= 0

    AMOUNT = 1232323
    tx_params = {
        "sender_address": account1.public_key,
        "destination_address": account2.public_key,
        "amount": AMOUNT,
        "unfunded_account": True,
    }
    import spl

    transaction = solana_api.get_transfer_transaction(
        account1.public_key,
        account2.public_key,
        tx_params,
        tx_fee=1,
        tx_nonce="asdas",
    )

    token = spl.token.client.Token(
        conn=solana_api._api,
        pubkey=PublicKey.from_bytes(account1.public_key),
        program_id=PublicKey.from_bytes(account1.public_key),
        payer=PublicKey.from_bytes(account1.public_key),
    )

    token.transfer(
        source=PublicKey.from_bytes(account1.public_key),
        dest=PublicKey.from_bytes(account2.public_key),
        amount=AMOUNT,
        owner=PublicKey.from_bytes(bytes(account1.public_key)),
    )

    (
        transaction_digest,
        transaction_receipt,
        is_settled,
    ) = solana_api.construct_and_settle_tx(
        account1,
        account2,
        tx_params,
    )
    assert is_settled, "Failed to verify tx!"

    tx = solana_api.get_transaction(transaction_digest)

    assert tx["blockTime"] == transaction_receipt["blockTime"], "Should be same"

    logs = solana_api.get_transaction_transfer_logs(
        contract_instance=None, tx_hash=transaction_digest
    )
    assert "preBalances" in logs
    assert "postBalances" in logs
