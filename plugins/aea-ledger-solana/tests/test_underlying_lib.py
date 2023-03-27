"""Unit tests for SPL-token instructions."""
import spl.token.instructions as spl_token
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID


"""Fixtures for pytest."""
import asyncio
import time
from typing import NamedTuple

import pytest
from aea_ledger_solana import SolanaApi, SolanaCrypto, SolanaFaucetApi
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solana.transaction import Transaction
from solders import system_program as sp
from solders.hash import Hash as Blockhash
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import CreateAccountParams, CreateAccountWithSeedParams
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.system_program import (
    TransferParams,
    create_account,
    create_account_with_seed,
    transfer,
)

@pytest.fixture
def test_client():
    """Create a client for testing."""
    return SolanaApi()


#
#
@pytest.mark.integration
def test_send_transaction_and_get_balance(
    test_client,
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer 1m lamports from sender to receiver

    sender = SolanaCrypto()
    receiver = SolanaCrypto()
    # we need to fund the new sender
    faucet = SolanaFaucetApi()
    faucet.generate_wealth_if_needed(test_client, sender.address)
    # we need to interact with the SPL token program so that we can transfer lamports
    transfer_ix = transfer(
        TransferParams(
            from_pubkey=sender.entity.pubkey(),
            to_pubkey=receiver.entity.pubkey(),
            lamports=1_000_000,
        )
    )
    txn = Transaction().add(transfer_ix)
    resp = test_client.api.send_transaction(
        txn, Keypair.from_base58_string(sender.private_key)
    )
    tx_digest = str(resp.value)
    test_client.wait_get_receipt(tx_digest)
    # check balance
    balance = test_client.api.get_balance(receiver.entity.pubkey()).value
    assert balance == 1_000_000


#


@pytest.mark.integration
def test_create_program_account(
    test_client,
):
    """Test sending a transaction to localnet."""
    # Create transfer tx to transfer 1m lamports from sender to receiver

    sender = SolanaCrypto()
    receiver = SolanaCrypto()
    # we need to fund the new sender
    faucet = SolanaFaucetApi()
    faucet.generate_wealth_if_needed(test_client, sender.address)
    # we need to interact with the SPL token program so that we can transfer lamports
    transfer_ix = transfer(
        TransferParams(
            from_pubkey=sender.entity.pubkey(),
            to_pubkey=receiver.entity.pubkey(),
            lamports=1_000_000,
        )
    )
    txn = Transaction().add(transfer_ix)
    resp = test_client.api.send_transaction(
        txn, Keypair.from_base58_string(sender.private_key)
    )
    tx_digest = str(resp.value)
    test_client.wait_get_receipt(tx_digest)
    # check balance
    balance = test_client.api.get_balance(receiver.entity.pubkey()).value
    assert balance == 1_000_000


@pytest.mark.unit
def test_create_account():
    """Test the create_account function."""
    params = sp.CreateAccountParams(
        from_pubkey=Keypair().pubkey(),
        to_pubkey=Keypair().pubkey(),
        lamports=123,
        space=1,
        owner=Pubkey.default(),
    )
    assert sp.decode_create_account(sp.create_account(params)) == params


@pytest.mark.integration
def test_submit_create_account(test_client):
    """Test the create_account function."""

    sender = SolanaCrypto()
    sender_kp = Keypair.from_base58_string(sender.private_key)
    faucet = SolanaFaucetApi()
    solana_api = SolanaApi()
    seed = "12123123"
    acc = Pubkey.create_with_seed(
        sender.entity.pubkey(),
        seed,
        SYS_PROGRAM_ID,
    )
    amount = 1000023
    params = CreateAccountWithSeedParams(
        from_pubkey=Pubkey.from_string(sender.address),
        to_pubkey=acc,
        base=Pubkey.from_string(sender.address),
        seed=seed,
        lamports=amount,
        space=0,
        owner=SYS_PROGRAM_ID,
    )
    ix_create_pda = sp.create_account_with_seed(params)
    txn = Transaction(fee_payer=Pubkey.from_string(sender.address)).add(ix_create_pda)
    faucet.generate_wealth_if_needed(solana_api, sender.address)
    resp = test_client.api.send_transaction(txn, sender_kp)
    tx_digest = str(resp.value)
    result = test_client.wait_get_receipt(tx_digest)
    assert result[1]
