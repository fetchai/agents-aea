"""Tests to ensure the contracts work as expected."""
import anchorpy
import pytest
from pathlib import Path
from tests.conftest import MAX_FLAKY_RERUNS, ROOT_DIR
from aea_ledger_solana import SolanaApi, SolanaCrypto, SolanaFaucetApi
from solders.pubkey import Pubkey as PublicKey  # type: ignore

from pytest import fixture, mark
from solders.keypair import Keypair
from solders.system_program import ID as SYS_PROGRAM_ID

from anchorpy import Context, Program, workspace_fixture, WorkspaceType


PAYER_KEYPAIR_PATH_0 = Path(ROOT_DIR, "tests", "data", "solana_private_key0.txt")
PAYER_KEYPAIR_PATH_1 = Path(ROOT_DIR, "tests", "data", "solana_private_key1.txt")
PROGRAM_KEYPAIR_PATH = Path(
    ROOT_DIR, "tests", "data", "solana_private_key_program.txt"
)


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
        ROOT_DIR, "tests", "data", "spl-token-faucet", "target", "idl", "spl_token_faucet.json"
    )
    bytecode_path = Path(
        ROOT_DIR, "tests", "data", "spl-token-faucet", "target", "deploy", "spl_token_faucet.so"
    )
    program_key_pair = SolanaCrypto(str(PROGRAM_KEYPAIR_PATH))

    interface = solana_api.load_contract_interface(
        idl_file_path=idl_path, bytecode_path=bytecode_path
    )
    instance = solana_api.get_contract_instance(
        contract_interface=interface, contract_address="11111111111111111111111111111110"
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
        idl_file_path=idl_path, bytecode_path=bytecode_path, program_keypair=program_key_pair
    )
    instance = solana_api.get_contract_instance(
        contract_interface=interface,
        contract_address=str(PublicKey.from_bytes(program_key_pair.public_key))
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

@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_contract_method_setup(tic_tac_contract, payer_0, payer_2, solana_api, solana_faucet):
    """Test the deployment contract method."""

    instance, contract_address, program_kp = tic_tac_contract

    player_0, player_2 = payer_1, payer_2

    resp = solana_faucet.generate_wealth_if_needed(solana_api, player_0.address)
    assert resp != "failed", "Failed to generate wealth"

    # setup game
    program = instance["program"]
    program.provider.wallet = player_0.entity

    breakpoint()
    accounts = {
        "game": PublicKey.from_bytes(program_kp.public_key),
        "player_one": PublicKey.from_bytes(player_0.public_key),
        "system_program": PublicKey.from_string("11111111111111111111111111111110"),
    }

    tx = solana_api.build_transaction(
        program,
        "setup_game",
        method_args={
            "data": (player_1.public_key,),
            "accounts": accounts,
        },
        tx_args=None,
    )

    tx = solana_api.add_nonce(tx)

    signed_transaction = program_kp.sign_transaction(tx, [program_kp])

    solana_api.send_signed_transaction(signed_transaction)
    transaction_digest = player_1.send_signed_transaction(signed_transaction)
    assert transaction_digest is not None

    _, is_settled = player_1.wait_get_receipt(transaction_digest)
    assert is_settled is True

@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_contract_method_call(solana_faucet):
    """Test the deploy contract method."""

    idl_path = Path(
        ROOT_DIR, "tests", "data", "tic-tac-toe", "target", "idl", "tic_tac_toe.json"
    )
    bytecode_path = Path(
        ROOT_DIR, "tests", "data", "tic-tac-toe", "target", "deploy", "tic_tac_toe.so"
    )
    program_keypair_path = Path(
        ROOT_DIR, "tests", "data", "solana_private_key_program.txt"
    )
    payer_keypair_path = Path(ROOT_DIR, "tests", "data", "solana_private_key0.txt")

    sa = SolanaApi()
    payer = SolanaCrypto(str(payer_keypair_path))
    program_kp = SolanaCrypto(str(program_keypair_path))

    interface = sa.load_contract_interface(
        idl_file_path=idl_path, bytecode_path=bytecode_path, program_keypair=program_kp
    )

    instance = sa.get_contract_instance(
        contract_interface=interface,
        contract_address=str(PublicKey.from_bytes(program_kp.public_key)),
    )

    player1 = payer
    player2 = SolanaCrypto("./tests/data/solana_private_key2.txt")
    game = SolanaCrypto()

    resp = solana_faucet.generate_wealth_if_needed(sa, player1.address)
    assert resp != "failed", "Failed to generate wealth"

    resp = solana_faucet.generate_wealth_if_needed(sa, player2.address)
    assert resp != "failed", "Failed to generate wealth"

    # setup game
    program = instance["program"]
    program.provider.wallet = payer.entity
    breakpoint()

    accounts = {
        "game": PublicKey.from_bytes(game.public_key),
        "player_one": PublicKey.from_bytes(payer.public_key),
        "system_program": PublicKey.from_bytes(payer.entity.public_key,)
    }

    tx = sa.build_transaction(
        program,
        "setup_game",
        method_args={
            "data": (PublicKey.from_bytes(player2.public_key),),
            "accounts": accounts,
        },
        tx_args=None,
    )

    tx = sa.add_nonce(tx)

    signed_transaction = game.sign_transaction(tx, [player1])

    transaction_digest = sa.send_signed_transaction(signed_transaction)
    assert transaction_digest is not None

    _, is_settled = _wait_get_receipt(sa, transaction_digest)
    assert is_settled is True
    state = sa.get_state(game.public_key)
    decoded_state = program.coder.accounts.decode(state.data)

    player1 = payer
    player2 = player2
    column = 0

    # game loop
    while decoded_state.state.index == 0:

        active_player = player2 if decoded_state.turn % 2 == 0 else player1
        row = 0 if decoded_state.turn % 2 == 0 else 1
        accounts = {"game": game.public_key, "player": active_player.public_key}

        tile = program.type["Tile"](row=row, column=column)

        tx1 = sa.build_transaction(
            program,
            "play",
            method_args={
                "data": (tile,),
                "accounts": accounts,
            },
            tx_args=None,
        )

        tx1 = sa.add_nonce(tx1)

        signed_transaction = active_player.sign_transaction(
            tx1,
        )

        transaction_digest = sa.send_signed_transaction(signed_transaction)
        assert transaction_digest is not None
        _, is_settled = _wait_get_receipt(sa, transaction_digest)
        assert is_settled is True
        state = sa.get_state(game.public_key)
        decoded_state = program.coder.accounts.decode(state.data)

        if row == 0:
            column += 1

    assert decoded_state.state.winner == player1.public_key

    # game loop
#     while decoded_state.state.index == 0:
#         active_player = player2 if decoded_state.turn % 2 == 0 else player1
#         row = 0 if decoded_state.turn % 2 == 0 else 1
#         accounts = {
#             "game": PublicKey.from_bytes(game.public_key),
#             "player": PublicKey.from_bytes(active_player.public_key)}
#
#         tile = program.type["Tile"](row=row, column=column)
#
#         tx1 = sa.build_transaction(
#             program,
#             "play",
#             method_args={
#                 "data": (tile,),
#                 "accounts": accounts,
#             },
#             tx_args=None,
#         )
#
#         tx1 = sa.add_nonce(tx1)
#
#         signed_transaction = active_player.sign_transaction(
#             tx1,
#         )
#
#         transaction_digest = active_player.send_signed_transaction(signed_transaction)
#         assert transaction_digest is not None
#
#         _, is_settled = active_player.wait_get_receipt(transaction_digest)
#         assert is_settled is True
#
#         state = sa.get_state(str(PublicKey(game.public_key)))
#         assert state is not None
#         decoded_state = program.coder.accounts.decode(state.data)
#         column += 1
#
#     #     active_player = player2 if decoded_state.turn % 2 == 0 else player1
#     #     row = 0 if decoded_state.turn % 2 == 0 else 1
#     #     accounts = {
#     #         "game": PublicKey.from_bytes(game.public_key),
#     #         "player": PublicKey.from_bytes(active_player.public_key)}
#     #
#     #     tile = program.type["Tile"](row=row, column=column)
#     #
#     #     tx1 = sa.build_transaction(
#     #         program,
#     #         "play",
#     #         method_args={
#     #             "data": (tile,),
#     #             "accounts": accounts,
#     #         },
#     #         tx_args=None,
#     #     )
#     #
#     #     tx1 = sa.add_nonce(tx1)
#     #
#     #     signed_transaction = active_player.sign_transaction(
#     #         tx1,
#     #     )
#     #
#     #     transaction_digest = sa.send_signed_transaction(signed_transaction)
#     #     assert transaction_digest is not None
#     #     _, is_settled = sa.wait_get_receipt(transaction_digest)
#     #     assert is_settled is True
#     #     state = sa.get_state(game.public_key)
#     #     decoded_state = program.coder.accounts.decode(state.data)
#     #
#     #     if row == 0:
#     #         column += 1
#     #
#     # assert decoded_state.state.winner == player1.public_key
# #
# #
# # @pytest.mark.skip(".get_deploy_transaction not implemented!")
# # @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
# # @pytest.mark.integration
# # @pytest.mark.ledger
# # def test_deploy_program():
# #     """Test the deployment contract method."""
# #
# #     idl_path = Path(
# #         ROOT_DIR, "tests", "data", "tic-tac-toe", "target", "idl", "tic_tac_toe.json"
# #     )
# #     bytecode_path = Path(
# #         ROOT_DIR, "tests", "data", "tic-tac-toe", "target", "deploy", "tic_tac_toe.so"
# #     )
# #     program_keypair_path = Path(
# #         ROOT_DIR, "tests", "data", "solana_private_key_program.txt"
# #     )
# #     payer_keypair_path = Path(ROOT_DIR, "tests", "data", "solana_private_key0.txt")
# #
# #     sa = SolanaApi()
# #
# #     program = SolanaCrypto(str(program_keypair_path))
# #     payer = SolanaCrypto(str(payer_keypair_path))
# #
# #     interface = sa.load_contract_interface(
# #         idl_file_path=idl_path, bytecode_path=bytecode_path, program_keypair=program
# #     )
# #
# #     init = False
# #     if init:
# #         program.dump(str(program_keypair_path))
# #         payer.dump(str(payer_keypair_path))
# #
# #         faucet = SolanaFaucetApi()
# #         tx = retry_airdrop_if_result_none(faucet, payer.address, 1)
# #         assert tx is not None, "Generate wealth failed"
# #         _, is_settled = sa.wait_get_receipt(tx)
# #         assert is_settled is True
# #
# #         balance = sa.get_balance(payer.address)
# #         assert balance >= 2 * LAMPORTS_PER_SOL
# #         print("Payer Balance: " + str(balance / LAMPORTS_PER_SOL) + " SOL")
# #
# #     result = sa.get_deploy_transaction(interface, payer)
# #     assert result is not None, "Should not be none"
#
