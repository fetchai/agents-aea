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

import pytest
from aea_ledger_solana import SolanaApi, SolanaCrypto, SolanaFaucetApi

from tests.conftest import AIRDROP_AMOUNT


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
    sc = SolanaCrypto()
    pre_balance = solana_api.get_balance(sc.address)
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.solana._default_logger"):
        resp = solana_faucet.generate_wealth_if_needed(
            solana_api, sc.address, AIRDROP_AMOUNT
        )
        assert resp != "failed", "Failed to generate wealth"
    assert solana_api.get_balance(sc.address) > pre_balance
