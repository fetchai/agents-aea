"""Tests for the crypto functionalities."""
from aea_ledger_solana import SolanaApi, SolanaCrypto
import pytest
import logging
from tests.conftest import (
    AIRDROP_AMOUNT,
    MAX_FLAKY_RERUNS,
    ROOT_DIR,
    SOLANA_PRIVATE_KEY_FILE,
)


def test_creation(solana_private_key_file):
    """Test the creation of the crypto_objects."""
    assert SolanaCrypto(), "Managed to initialise the solana_keypair"
    assert SolanaCrypto(solana_private_key_file), "Managed to load the sol private key"


def test_derive_address():
    """Test the get_address_from_public_key method"""
    account = SolanaCrypto()
    address = SolanaApi.get_address_from_public_key(account.public_key)
    assert account.address == address, "Address derivation incorrect"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_encrypt_decrypt_privatekey(caplog, solana_private_key_file):
    """Test the balance is zero for a new account."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.solana._default_logger"):
        sc = SolanaCrypto(private_key_path=solana_private_key_file)
        privKey = sc.private_key

        encrypted = sc.encrypt("test123456788")

        decrypted = sc.decrypt(encrypted, "test123456788")
        assert privKey == decrypted, "Private keys match"


def test_can_sign_message():
    """Test the signing of a message."""
    account = SolanaCrypto()
    message = b"hello"
    signature = account.sign_message(message)
    assert signature, "Managed to sign the message"


def test_is_address_string():
    """Test the is_address string method."""
    account = SolanaCrypto()
    assert isinstance(account.address, str)
