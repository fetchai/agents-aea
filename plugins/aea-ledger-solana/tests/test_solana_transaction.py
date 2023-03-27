"""Class to test the solana transaction."""
from typing import Tuple

from aea_ledger_solana import SolanaTransaction
from copy import deepcopy
from aea_ledger_solana import SolanaApi

BLANK_TRANSACTION = {
    "signatures": [[0]],
    "message": {
        "header": {
            "numRequiredSignatures": 0,
            "numReadonlySignedAccounts": 0,
            "numReadonlyUnsignedAccounts": 0,
        },
        "accountKeys": [[0]],
        "recentBlockhash": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
        "instructions": [[0]],
    },
}


def test_solana_transaction():
    """Test the solana transaction."""
    transaction = SolanaTransaction()
    assert transaction is not None


def test_from_json():
    """Test the from_json method."""
    # we first create a json transaction

    transaction = SolanaTransaction.from_json(BLANK_TRANSACTION)
    assert transaction is not None


def test_to_json():
    """Test the to_json method."""
    # we first create a json transaction
    transaction = SolanaTransaction()
    assert transaction.to_json() is not None


def test_from_json_matches_to_json():
    """Test the transaction_matches_transaction method."""
    # we first create a json transaction
    transaction = SolanaTransaction()
    json_string = transaction.to_json()
    transaction2 = SolanaTransaction.from_json(json_string)
    assert transaction2.to_json() == json_string


def test_from_json_matches_to_json_signers():
    """Test the transaction_matches_transaction method."""
    # we first create a json transaction
    new_tx = deepcopy(BLANK_TRANSACTION)
    assert new_tx["message"]["header"]["numReadonlySignedAccounts"] == 0
    solana_api = SolanaApi()
    tx_1 = solana_api.add_nonce(new_tx)
    assert tx_1["message"]["header"]["numReadonlySignedAccounts"] == 0
