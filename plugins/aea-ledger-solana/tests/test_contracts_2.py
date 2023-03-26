
import anchorpy
import pytest
from pathlib import Path
from tests.conftest import MAX_FLAKY_RERUNS, ROOT_DIR
from aea_ledger_solana import SolanaApi, SolanaCrypto, SolanaFaucetApi
from solders.pubkey import Pubkey as PublicKey  # type: ignore

PAYER_KEYPAIR_PATH_0 = Path(ROOT_DIR, "tests", "data", "solana_private_key0.txt")
PAYER_KEYPAIR_PATH_1 = Path(ROOT_DIR, "tests", "data", "solana_private_key1.txt")
PROGRAM_KEYPAIR_PATH = Path(
    ROOT_DIR, "tests", "data", "solana_private_key_program.txt"
)

# we first need to ensure we can load up a program

