"""Tests to ensure the contracts work as expected."""
from pathlib import Path

import anchorpy
import pytest
from aea_ledger_solana import SolanaApi, SolanaCrypto, SolanaFaucetApi
from anchorpy import Context, Program, WorkspaceType, workspace_fixture
from pytest import fixture, mark
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey  # type: ignore
from solders.system_program import ID as SYS_PROGRAM_ID

from tests.conftest import MAX_FLAKY_RERUNS, ROOT_DIR


PAYER_KEYPAIR_PATH_0 = Path(ROOT_DIR, "tests", "data", "solana_private_key0.txt")
PAYER_KEYPAIR_PATH_1 = Path(ROOT_DIR, "tests", "data", "solana_private_key1.txt")
PROGRAM_KEYPAIR_PATH = Path(ROOT_DIR, "tests", "data", "solana_private_key_program.txt")


@pytest.fixture
def solana_faucet():
    """Create a solana faucet."""
    sf = SolanaFaucetApi()
    return sf


@pytest.fixture
def payer_1():
    """Create a payer."""
    payer = SolanaCrypto(str(PAYER_KEYPAIR_PATH_0))
    return payer


@pytest.fixture
def payer_2():
    """Create a payer."""
    payer = SolanaCrypto(str(PAYER_KEYPAIR_PATH_1))
    return payer


@pytest.fixture
def solana_api():
    """Create a solana api."""
    sa = SolanaApi()
    return sa


def _get_token_contract(solana_api):
    """Create a contract."""
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
    program_key_pair = SolanaCrypto(str(PROGRAM_KEYPAIR_PATH))

    interface = solana_api.load_contract_interface(
        idl_file_path=idl_path, bytecode_path=bytecode_path
    )
    instance = solana_api.get_contract_instance(
        contract_interface=interface,
        contract_address="11111111111111111111111111111110",
    )

    return instance, interface, program_key_pair


def _get_tic_tac_contract(solana_api):
    """Create a contract."""
    idl_path = Path(
        ROOT_DIR, "tests", "data", "tic-tac-toe", "target", "idl", "tic_tac_toe.json"
    )
    bytecode_path = Path(
        ROOT_DIR, "tests", "data", "tic-tac-toe", "target", "deploy", "tic_tac_toe.so"
    )
    program_key_pair = SolanaCrypto(str(PROGRAM_KEYPAIR_PATH))

    interface = solana_api.load_contract_interface(
        idl_file_path=idl_path,
        bytecode_path=bytecode_path,
        program_keypair=program_key_pair,
    )
    instance = solana_api.get_contract_instance(
        contract_interface=interface,
        contract_address=program_key_pair.address,
    )

    return instance, interface, program_key_pair


def test_tic_tac_contract(solana_api):
    """Test the tic tac contract."""
    instance, interface, _ = _get_tic_tac_contract(solana_api)
    assert isinstance(instance["program"], anchorpy.program.core.Program)
    assert isinstance(instance["program"].provider, anchorpy.provider.Provider)
    assert isinstance(interface, dict)


@pytest.fixture
def tic_tac_contract(solana_api):
    """Create a contract."""
    return _get_tic_tac_contract(solana_api)
