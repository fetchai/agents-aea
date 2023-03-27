"""Test the solana faucet."""
import pytest
import logging
from aea_ledger_solana import SolanaApi, SolanaCrypto, SolanaFaucetApi
from tests.conftest import AIRDROP_AMOUNT, MAX_FLAKY_RERUNS, ROOT_DIR


@pytest.mark.ledger
@pytest.mark.integration
def test_get_wealth_succeeds(caplog, solana_private_key_file):
    """Test the faucet request succeeds."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.solana._default_logger"):
        solana_api = SolanaApi()
        solana_faucet = SolanaFaucetApi()
        sc = SolanaCrypto(solana_private_key_file)
        resp = solana_faucet.generate_wealth_if_needed(
            solana_api, sc.address, AIRDROP_AMOUNT
        )
        assert resp != "failed", "Failed to generate wealth"


@pytest.mark.ledger
@pytest.mark.integration
def test_get_wealth_increments_native_balance(caplog, solana_private_key_file):
    """Test the balance increases after faucet request."""
    solana_api = SolanaApi()
    solana_faucet = SolanaFaucetApi()
    sc = SolanaCrypto(solana_private_key_file)
    pre_balance = solana_api.get_balance(sc.address)
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.solana._default_logger"):
        resp = solana_faucet.generate_wealth_if_needed(
            solana_api, sc.address, AIRDROP_AMOUNT
        )
        assert resp != "failed", "Failed to generate wealth"
    assert solana_api.get_balance(sc.address) > pre_balance
