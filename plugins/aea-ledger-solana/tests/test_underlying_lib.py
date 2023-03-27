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

#     # S6EA7XsNyxg4yx4DJRMm7fP21jgZb1fuzBAUGhgVtkP
#     signer_one = Keypair.from_seed(
#         bytes(
#             [
#                 216,
#                 214,
#                 184,
#                 213,
#                 199,
#                 75,
#                 129,
#                 160,
#                 237,
#                 96,
#                 96,
#                 228,
#                 46,
#                 251,
#                 146,
#                 3,
#                 71,
#                 162,
#                 37,
#                 117,
#                 121,
#                 70,
#                 143,
#                 16,
#                 128,
#                 78,
#                 53,
#                 189,
#                 222,
#                 230,
#                 165,
#                 249,
#             ]
#         )
#     )
#
#     # BKdt9U6V922P17ui81dzLoqgSY2B5ds1UD13rpwFB2zi
#     receiver_one = Keypair.from_seed(
#         bytes(
#             [
#                 3,
#                 140,
#                 94,
#                 243,
#                 0,
#                 38,
#                 92,
#                 138,
#                 52,
#                 79,
#                 153,
#                 83,
#                 42,
#                 236,
#                 220,
#                 82,
#                 227,
#                 187,
#                 101,
#                 104,
#                 126,
#                 159,
#                 103,
#                 100,
#                 29,
#                 183,
#                 242,
#                 68,
#                 144,
#                 184,
#                 114,
#                 211,
#             ]
#         )
#     )
#
#     # DtDZCnXEN69n5W6rN5SdJFgedrWdK8NV9bsMiJekNRyu
#     signer_two = Keypair.from_seed(
#         bytes(
#             [
#                 177,
#                 182,
#                 154,
#                 154,
#                 5,
#                 145,
#                 253,
#                 138,
#                 211,
#                 126,
#                 222,
#                 195,
#                 21,
#                 64,
#                 117,
#                 211,
#                 225,
#                 47,
#                 115,
#                 31,
#                 247,
#                 242,
#                 80,
#                 195,
#                 38,
#                 8,
#                 236,
#                 155,
#                 255,
#                 27,
#                 20,
#                 142,
#             ]
#         )
#     )
#
#     # FXgds3n6SNCoVVV4oELSumv8nKzAfqSgmeu7cNPikKFT
#     receiver_two = Keypair.from_seed(
#         bytes(
#             [
#                 180,
#                 204,
#                 139,
#                 131,
#                 244,
#                 6,
#                 180,
#                 121,
#                 191,
#                 193,
#                 45,
#                 109,
#                 198,
#                 50,
#                 163,
#                 140,
#                 34,
#                 4,
#                 172,
#                 76,
#                 129,
#                 45,
#                 194,
#                 83,
#                 192,
#                 112,
#                 76,
#                 58,
#                 32,
#                 174,
#                 49,
#                 248,
#             ]
#         )
#     )
#
#     # C2UwQHqJ3BmEJHSMVmrtZDQGS2fGv8fZrWYGi18nHF5k
#     signer_three = Keypair.from_seed(
#         bytes(
#             [
#                 29,
#                 79,
#                 73,
#                 16,
#                 137,
#                 117,
#                 183,
#                 2,
#                 131,
#                 0,
#                 209,
#                 142,
#                 134,
#                 100,
#                 190,
#                 35,
#                 95,
#                 220,
#                 200,
#                 163,
#                 247,
#                 237,
#                 161,
#                 70,
#                 226,
#                 223,
#                 100,
#                 148,
#                 49,
#                 202,
#                 154,
#                 180,
#             ]
#         )
#     )
#
#     # 8YPqwYXZtWPd31puVLEUPamS4wTv6F89n8nXDA5Ce2Bg
#     receiver_three = Keypair.from_seed(
#         bytes(
#             [
#                 167,
#                 102,
#                 49,
#                 166,
#                 202,
#                 0,
#                 132,
#                 182,
#                 239,
#                 182,
#                 252,
#                 59,
#                 25,
#                 103,
#                 76,
#                 217,
#                 65,
#                 215,
#                 210,
#                 159,
#                 168,
#                 50,
#                 10,
#                 229,
#                 144,
#                 231,
#                 221,
#                 74,
#                 182,
#                 161,
#                 52,
#                 193,
#             ]
#         )
#     )
#
#     fee_payer = signer_one
#     sorted_signers = sorted(
#         [x.pubkey() for x in [signer_one, signer_two, signer_three]], key=str
#     )
#     sorted_signers_excluding_fee_payer = [
#         x for x in sorted_signers if str(x) != str(fee_payer.pubkey())
#     ]
#     sorted_receivers = sorted(
#         [x.pubkey() for x in [receiver_one, receiver_two, receiver_three]], key=str
#     )
#
#     txn = txlib.Transaction(recent_blockhash=stubbed_blockhash)
#     txn.fee_payer = fee_payer.pubkey()
#
#     # Add three transfer transactions
#     txn.add(
#         sp.transfer(
#             sp.TransferParams(
#                 from_pubkey=signer_one.pubkey(),
#                 to_pubkey=receiver_one.pubkey(),
#                 lamports=2_000_000,
#             )
#         )
#     )
#     txn.add(
#         sp.transfer(
#             sp.TransferParams(
#                 from_pubkey=signer_two.pubkey(),
#                 to_pubkey=receiver_two.pubkey(),
#                 lamports=2_000_000,
#             )
#         )
#     )
#     txn.add(
#         sp.transfer(
#             sp.TransferParams(
#                 from_pubkey=signer_three.pubkey(),
#                 to_pubkey=receiver_three.pubkey(),
#                 lamports=2_000_000,
#             )
#         )
#     )
#
#     tx_msg = txn.compile_message()
#
#     js_msg_b64_check = b"AwABBwZtbiRMvgQjcE2kVx9yon8XqPSO5hwc2ApflnOZMu0Qo9G5/xbhB0sp8/03Rv9x4MKSkQ+k4LB6lNLvCgKZ/ju/aw+EyQpTObVa3Xm+NA1gSTzutgFCTfkDto/0KtuIHHAMpKRb92NImxKeWQJ2/291j6nTzFj1D6nW25p7TofHmVsGt8uFnTv7+8vsWZ0uN7azdxa+jCIIm4WzKK+4uKfX39t5UA7S1soBQaJkTGOQkSbBo39gIjDkbW0TrevslgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAxJrndgN4IFTxep3s6kO0ROug7bEsbx0xxuDkqEvwUusDBgIABAwCAAAAgIQeAAAAAAAGAgIFDAIAAACAhB4AAAAAAAYCAQMMAgAAAICEHgAAAAAA"  # noqa: E501 pylint: disable=line-too-long
#
#     assert b64encode(bytes(tx_msg)) == js_msg_b64_check
#
#     # Transaction should organize AccountMetas by pubkey
#     assert tx_msg.account_keys[0] == fee_payer.pubkey()
#     assert tx_msg.account_keys[1] == sorted_signers_excluding_fee_payer[0]
#     assert tx_msg.account_keys[2] == sorted_signers_excluding_fee_payer[1]
#     assert tx_msg.account_keys[3] == sorted_receivers[0]
#     assert tx_msg.account_keys[4] == sorted_receivers[1]
#     assert tx_msg.account_keys[5] == sorted_receivers[2]
#
#
# from aea_ledger_solana import SolanaApi, TransactionInstruction, SolanaCrypto
# from aea_ledger_solana import SolanaFaucetApi
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


# class Clients(NamedTuple):
#     """Container for http clients."""
#
#     sync: Client
#     async_: AsyncClient
#     loop: asyncio.AbstractEventLoop
#
#
# @pytest.fixture(scope="session")
# def event_loop():
#     """Event loop for pytest-asyncio."""
#     try:
#         loop = asyncio.get_running_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#     yield loop
#     loop.close()
#
#
# @pytest.fixture(scope="session")
# def stubbed_blockhash() -> Blockhash:
#     """Arbitrary block hash."""
#     return Blockhash.from_string("EETubP5AKHgjPAhzPAFcb8BAY1hMH639CWCFTqi3hq1k")
#
#
# @pytest.fixture(scope="session")
# def stubbed_receiver() -> Pubkey:
#     """Arbitrary known public key to be used as receiver."""
#     return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i99")
#
#
# @pytest.fixture(scope="session")
# def stubbed_receiver_prefetched_blockhash() -> Pubkey:
#     """Arbitrary known public key to be used as receiver."""
#     return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i97")
#
#
# @pytest.fixture(scope="session")
# def stubbed_receiver_cached_blockhash() -> Pubkey:
#     """Arbitrary known public key to be used as receiver."""
#     return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i95")
#
#
# @pytest.fixture(scope="session")
# def async_stubbed_receiver() -> Pubkey:
#     """Arbitrary known public key to be used as receiver."""
#     return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i98")
#
#
# @pytest.fixture(scope="session")
# def async_stubbed_receiver_prefetched_blockhash() -> Pubkey:
#     """Arbitrary known public key to be used as receiver."""
#     return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i96")
#
#
# @pytest.fixture(scope="session")
# def async_stubbed_receiver_cached_blockhash() -> Pubkey:
#     """Arbitrary known public key to be used as receiver."""
#     return Pubkey.from_string("J3dxNj7nDRRqRRXuEMynDG57DkZK4jYRuv3Garmb1i94")
#
#
# @pytest.fixture(scope="session")
# def stubbed_sender() -> Keypair:
#     """Arbitrary known account to be used as sender."""
#     return Keypair.from_seed(bytes([8] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def stubbed_sender_prefetched_blockhash() -> Keypair:
#     """Arbitrary known account to be used as sender."""
#     return Keypair.from_seed(bytes([9] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def stubbed_sender_cached_blockhash() -> Keypair:
#     """Arbitrary known account to be used as sender."""
#     return Keypair.from_seed(bytes([4] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def stubbed_sender_for_token() -> Keypair:
#     """Arbitrary known account to be used as sender."""
#     return Keypair.from_seed(bytes([2] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def async_stubbed_sender() -> Keypair:
#     """Another arbitrary known account to be used as sender."""
#     return Keypair.from_seed(bytes([7] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def async_stubbed_sender_prefetched_blockhash() -> Keypair:
#     """Another arbitrary known account to be used as sender."""
#     return Keypair.from_seed(bytes([5] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def async_stubbed_sender_cached_blockhash() -> Keypair:
#     """Another arbitrary known account to be used as sender."""
#     return Keypair.from_seed(bytes([3] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def freeze_authority() -> Keypair:
#     """Arbitrary known account to be used as freeze authority."""
#     return Keypair.from_seed(bytes([6] * Pubkey.LENGTH))
#
#
# @pytest.fixture(scope="session")
# def unit_test_http_client() -> Client:
#     """Client to be used in unit tests."""
#     client = Client(commitment=Processed)
#     return client
#
#
# @pytest.fixture(scope="session")
# def unit_test_http_client_async() -> AsyncClient:
#     """Async client to be used in unit tests."""
#     client = AsyncClient(commitment=Processed)
#     return client
#
#
# @pytest.fixture(scope="session")
# def _sleep_for_first_blocks() -> None:
#     """Blocks 0 and 1 are unavailable so we sleep until they're done."""
#     time.sleep(20)
#
#
# @pytest.mark.integration
# @pytest.fixture(scope="session")
# def test_http_client(
#     docker_services, _sleep_for_first_blocks
# ) -> Client:  # pylint: disable=redefined-outer-name
#     """Test http_client.is_connected."""
#     http_client = Client(commitment=Processed)
#     docker_services.wait_until_responsive(
#         timeout=15, pause=1, check=http_client.is_connected
#     )
#     return http_client
#
#
# @pytest.mark.integration
# @pytest.fixture(scope="session")
# def test_http_client_cached_blockhash(
#     docker_services, _sleep_for_first_blocks  # pylint: disable=redefined-outer-name
# ) -> Client:
#     """Test http_client.is_connected."""
#     http_client = Client(commitment=Processed, blockhash_cache=True)
#     docker_services.wait_until_responsive(
#         timeout=15, pause=1, check=http_client.is_connected
#     )
#     return http_client
#
#
# @pytest.mark.integration
# @pytest.fixture(scope="session")
# def test_http_client_async(
#     docker_services,
#     event_loop,
#     _sleep_for_first_blocks,  # pylint: disable=redefined-outer-name
# ) -> AsyncClient:
#     """Test http_client.is_connected."""
#     http_client = AsyncClient(commitment=Processed)
#
#     def check() -> bool:
#         return event_loop.run_until_complete(http_client.is_connected())
#
#     docker_services.wait_until_responsive(timeout=15, pause=1, check=check)
#     yield http_client
#     event_loop.run_until_complete(http_client.close())
#
#
# @pytest.mark.integration
# @pytest.fixture(scope="session")
# def test_http_client_async_cached_blockhash(
#     docker_services,
#     event_loop,
#     _sleep_for_first_blocks,  # pylint: disable=redefined-outer-name
# ) -> AsyncClient:
#     """Test http_client.is_connected."""
#     http_client = AsyncClient(commitment=Processed, blockhash_cache=True)
#
#     def check() -> bool:
#         return event_loop.run_until_complete(http_client.is_connected())
#
#     docker_services.wait_until_responsive(timeout=15, pause=1, check=check)
#     yield http_client
#     event_loop.run_until_complete(http_client.close())
#
#
# @pytest.mark.integration
# @pytest.fixture(scope="function")
# def random_funded_keypair(test_http_client: Client) -> Keypair:
#     """A new keypair with some lamports."""
#     kp = Keypair()
#     resp = test_http_client.request_airdrop(kp.pubkey(), AIRDROP_AMOUNT)
#     assert_valid_response(resp)
#     test_http_client.confirm_transaction(resp.value)
#     balance = test_http_client.get_balance(kp.pubkey())
#     assert balance.value == AIRDROP_AMOUNT
#     return kp
#
#
# def test_initialize_mint(stubbed_sender):
#     """Test initialize mint."""
#     mint_authority, freeze_authority = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params_with_freeze = spl_token.InitializeMintParams(
#         decimals=18,
#         program_id=TOKEN_PROGRAM_ID,
#         mint=stubbed_sender.pubkey(),
#         mint_authority=mint_authority,
#         freeze_authority=freeze_authority,
#     )
#     instruction = spl_token.initialize_mint(params_with_freeze)
#     assert spl_token.decode_initialize_mint(instruction) == params_with_freeze
#
#     params_no_freeze = spl_token.InitializeMintParams(
#         decimals=18,
#         program_id=TOKEN_PROGRAM_ID,
#         mint=stubbed_sender.pubkey(),
#         mint_authority=mint_authority,
#     )
#     instruction = spl_token.initialize_mint(params_no_freeze)
#     decoded_params = spl_token.decode_initialize_mint(instruction)
#     assert not decoded_params.freeze_authority
#     assert decoded_params == params_no_freeze
#
#
# def test_initialize_account(stubbed_sender):
#     """Test initialize account."""
#     new_account, token_mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params = spl_token.InitializeAccountParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=new_account,
#         mint=token_mint,
#         owner=stubbed_sender.pubkey(),
#     )
#     instruction = spl_token.initialize_account(params)
#     assert spl_token.decode_initialize_account(instruction) == params
#
#
# def test_initialize_multisig():
#     """Test initialize multisig."""
#     new_multisig = Pubkey([0] * 31 + [0])
#     signers = [Pubkey([0] * 31 + [i + 1]) for i in range(3)]
#     params = spl_token.InitializeMultisigParams(
#         program_id=TOKEN_PROGRAM_ID,
#         multisig=new_multisig,
#         signers=signers,
#         m=len(signers),
#     )
#     instruction = spl_token.initialize_multisig(params)
#     assert spl_token.decode_initialize_multisig(instruction) == params
#
#
# def test_transfer(stubbed_receiver, stubbed_sender):
#     """Test transfer."""
#     params = spl_token.TransferParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         dest=stubbed_receiver,
#         owner=stubbed_sender.pubkey(),
#         amount=123,
#     )
#     instruction = spl_token.transfer(params)
#     assert spl_token.decode_transfer(instruction) == params
#
#     multisig_params = spl_token.TransferParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         dest=stubbed_receiver,
#         owner=stubbed_sender.pubkey(),
#         signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
#         amount=123,
#     )
#     instruction = spl_token.transfer(multisig_params)
#     assert spl_token.decode_transfer(instruction) == multisig_params
#
#
# def test_approve(stubbed_sender):
#     """Test approve."""
#     delegate_account = Pubkey([0] * 31 + [0])
#     params = spl_token.ApproveParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         delegate=delegate_account,
#         owner=stubbed_sender.pubkey(),
#         amount=123,
#     )
#     instruction = spl_token.approve(params)
#     assert spl_token.decode_approve(instruction) == params
#
#     multisig_params = spl_token.ApproveParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         delegate=delegate_account,
#         owner=stubbed_sender.pubkey(),
#         signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
#         amount=123,
#     )
#     instruction = spl_token.approve(multisig_params)
#     assert spl_token.decode_approve(instruction) == multisig_params
#
#
# def test_revoke(stubbed_sender):
#     """Test revoke."""
#     delegate_account = Pubkey([0] * 31 + [0])
#     params = spl_token.RevokeParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=delegate_account,
#         owner=stubbed_sender.pubkey(),
#     )
#     instruction = spl_token.revoke(params)
#     assert spl_token.decode_revoke(instruction) == params
#
#     multisig_params = spl_token.RevokeParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=delegate_account,
#         owner=stubbed_sender.pubkey(),
#         signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
#     )
#     instruction = spl_token.revoke(multisig_params)
#     assert spl_token.decode_revoke(instruction) == multisig_params
#
#
# def test_set_authority():
#     """Test set authority."""
#     account, new_authority, current_authority = (
#         Pubkey([0] * 31 + [0]),
#         Pubkey([0] * 31 + [1]),
#         Pubkey([0] * 31 + [2]),
#     )
#     params = spl_token.SetAuthorityParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=account,
#         authority=spl_token.AuthorityType.FREEZE_ACCOUNT,
#         new_authority=new_authority,
#         current_authority=current_authority,
#     )
#     instruction = spl_token.set_authority(params)
#     assert spl_token.decode_set_authority(instruction) == params
#
#     multisig_params = spl_token.SetAuthorityParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=account,
#         authority=spl_token.AuthorityType.FREEZE_ACCOUNT,
#         current_authority=current_authority,
#         signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
#     )
#     instruction = spl_token.set_authority(multisig_params)
#     decoded_params = spl_token.decode_set_authority(instruction)
#     assert not decoded_params.new_authority
#     assert decoded_params == multisig_params
#
#
# def test_mint_to(stubbed_receiver):
#     """Test mint to."""
#     mint, mint_authority = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params = spl_token.MintToParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         dest=stubbed_receiver,
#         mint_authority=mint_authority,
#         amount=123,
#     )
#     instruction = spl_token.mint_to(params)
#     assert spl_token.decode_mint_to(instruction) == params
#
#     multisig_params = spl_token.MintToParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         dest=stubbed_receiver,
#         mint_authority=mint_authority,
#         signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
#         amount=123,
#     )
#     instruction = spl_token.mint_to(multisig_params)
#     assert spl_token.decode_mint_to(instruction) == multisig_params
#
#
# def test_burn(stubbed_receiver):
#     """Test burn."""
#     mint, owner = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params = spl_token.BurnParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         account=stubbed_receiver,
#         owner=owner,
#         amount=123,
#     )
#     instruction = spl_token.burn(params)
#     assert spl_token.decode_burn(instruction) == params
#
#     multisig_params = spl_token.BurnParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         account=stubbed_receiver,
#         owner=owner,
#         signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
#         amount=123,
#     )
#     instruction = spl_token.burn(multisig_params)
#     assert spl_token.decode_burn(instruction) == multisig_params
#
#
# def test_close_account(stubbed_sender):
#     """Test close account."""
#     token_account = Pubkey([0] * 31 + [0])
#     params = spl_token.CloseAccountParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=token_account,
#         dest=stubbed_sender.pubkey(),
#         owner=stubbed_sender.pubkey(),
#     )
#     instruction = spl_token.close_account(params)
#     assert spl_token.decode_close_account(instruction) == params
#
#     multisig_params = spl_token.CloseAccountParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=token_account,
#         dest=stubbed_sender.pubkey(),
#         owner=stubbed_sender.pubkey(),
#         signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
#     )
#     instruction = spl_token.close_account(multisig_params)
#     assert spl_token.decode_close_account(instruction) == multisig_params
#
#
# def test_freeze_account(stubbed_sender):
#     """Test freeze account."""
#     token_account, mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params = spl_token.FreezeAccountParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=token_account,
#         mint=mint,
#         authority=stubbed_sender.pubkey(),
#     )
#     instruction = spl_token.freeze_account(params)
#     assert spl_token.decode_freeze_account(instruction) == params
#
#     multisig_params = spl_token.FreezeAccountParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=token_account,
#         mint=mint,
#         authority=stubbed_sender.pubkey(),
#         multi_signers=[Pubkey([0] * 31 + [i]) for i in range(2, 10)],
#     )
#     instruction = spl_token.freeze_account(multisig_params)
#     assert spl_token.decode_freeze_account(instruction) == multisig_params
#
#
# def test_thaw_account(stubbed_sender):
#     """Test thaw account."""
#     token_account, mint = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params = spl_token.ThawAccountParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=token_account,
#         mint=mint,
#         authority=stubbed_sender.pubkey(),
#     )
#     instruction = spl_token.thaw_account(params)
#     assert spl_token.decode_thaw_account(instruction) == params
#
#     multisig_params = spl_token.ThawAccountParams(
#         program_id=TOKEN_PROGRAM_ID,
#         account=token_account,
#         mint=mint,
#         authority=stubbed_sender.pubkey(),
#         multi_signers=[Pubkey([0] * 31 + [i]) for i in range(2, 10)],
#     )
#     instruction = spl_token.thaw_account(multisig_params)
#     assert spl_token.decode_thaw_account(instruction) == multisig_params
#
#
# def test_transfer_checked(stubbed_receiver, stubbed_sender):
#     """Test transfer_checked."""
#     mint = Pubkey([0] * 31 + [0])
#     params = spl_token.TransferCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         mint=mint,
#         dest=stubbed_receiver,
#         owner=stubbed_sender.pubkey(),
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.transfer_checked(params)
#     assert spl_token.decode_transfer_checked(instruction) == params
#
#     multisig_params = spl_token.TransferCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         mint=mint,
#         dest=stubbed_receiver,
#         owner=stubbed_sender.pubkey(),
#         signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.transfer_checked(multisig_params)
#     assert spl_token.decode_transfer_checked(instruction) == multisig_params
#
#
# def test_approve_checked(stubbed_receiver, stubbed_sender):
#     """Test approve_checked."""
#     mint = Pubkey([0] * 31 + [0])
#     params = spl_token.ApproveCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         mint=mint,
#         delegate=stubbed_receiver,
#         owner=stubbed_sender.pubkey(),
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.approve_checked(params)
#     assert spl_token.decode_approve_checked(instruction) == params
#
#     multisig_params = spl_token.ApproveCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         source=stubbed_sender.pubkey(),
#         mint=mint,
#         delegate=stubbed_receiver,
#         owner=stubbed_sender.pubkey(),
#         signers=[Pubkey([0] * 31 + [i + 1]) for i in range(3)],
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.approve_checked(multisig_params)
#     assert spl_token.decode_approve_checked(instruction) == multisig_params
#
#
# def test_mint_to_checked(stubbed_receiver):
#     """Test mint_to_checked."""
#     mint, mint_authority = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params = spl_token.MintToCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         dest=stubbed_receiver,
#         mint_authority=mint_authority,
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.mint_to_checked(params)
#     assert spl_token.decode_mint_to_checked(instruction) == params
#
#     multisig_params = spl_token.MintToCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         dest=stubbed_receiver,
#         mint_authority=mint_authority,
#         signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.mint_to_checked(multisig_params)
#     assert spl_token.decode_mint_to_checked(instruction) == multisig_params
#
#
# def test_burn_checked(stubbed_receiver):
#     """Test burn_checked."""
#     mint, owner = Pubkey([0] * 31 + [0]), Pubkey([0] * 31 + [1])
#     params = spl_token.BurnCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         account=stubbed_receiver,
#         owner=owner,
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.burn_checked(params)
#     assert spl_token.decode_burn_checked(instruction) == params
#
#     multisig_params = spl_token.BurnCheckedParams(
#         program_id=TOKEN_PROGRAM_ID,
#         mint=mint,
#         account=stubbed_receiver,
#         owner=owner,
#         signers=[Pubkey([0] * 31 + [i]) for i in range(3, 10)],
#         amount=123,
#         decimals=6,
#     )
#     instruction = spl_token.burn_checked(multisig_params)
#     assert spl_token.decode_burn_checked(instruction) == multisig_params
#
#
# from base64 import b64decode, b64encode
#
# import pytest
# import solana.transaction as txlib
# import solders.system_program as sp
# from solders.hash import Hash as Blockhash
# from solders.instruction import AccountMeta, CompiledInstruction
# from solders.keypair import Keypair
# from solders.message import Message
# from solders.message import Message as SoldersMessage
# from solders.pubkey import Pubkey
# from solders.signature import Signature
# from solders.transaction import Transaction as SoldersTx
#
#
# def example_tx(
#     stubbed_blockhash, kp0: Keypair, kp1: Keypair, kp2: Keypair
# ) -> txlib.Transaction:
#     """Example tx for testing."""
#     ixn = txlib.Instruction(
#         program_id=Pubkey.default(),
#         data=bytes([0, 0, 0, 0]),
#         accounts=[
#             AccountMeta(kp0.pubkey(), True, True),
#             AccountMeta(kp1.pubkey(), True, True),
#             AccountMeta(kp2.pubkey(), True, True),
#         ],
#     )
#     return txlib.Transaction(
#         fee_payer=kp0.pubkey(), instructions=[ixn], recent_blockhash=stubbed_blockhash
#     )
#
#
# def test_to_solders(stubbed_blockhash: Blockhash) -> None:
#     """Test converting a Transaction to solders."""
#     kp1, kp2 = Keypair(), Keypair()
#     transfer = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123
#         )
#     )
#     solders_transfer = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123
#         )
#     )
#     assert transfer.data == solders_transfer.data
#     txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
#     solders_msg = SoldersMessage.new_with_blockhash(
#         [solders_transfer], None, stubbed_blockhash
#     )
#     solders_txn = SoldersTx.new_unsigned(solders_msg)
#     assert txn.to_solders() == solders_txn
#     assert txlib.Transaction.from_solders(solders_txn) == txn
#
#
# def test_sign_partial(stubbed_blockhash):
#     """Test partially sigining a transaction."""
#     keypair0 = Keypair()
#     keypair1 = Keypair()
#     keypair2 = Keypair()
#     ixn = txlib.Instruction(
#         program_id=Pubkey.default(),
#         data=bytes([0, 0, 0, 0]),
#         accounts=[
#             AccountMeta(keypair0.pubkey(), True, True),
#             AccountMeta(keypair1.pubkey(), True, True),
#             AccountMeta(keypair2.pubkey(), True, True),
#         ],
#     )
#     txn = txlib.Transaction(
#         fee_payer=keypair0.pubkey(),
#         instructions=[ixn],
#         recent_blockhash=stubbed_blockhash,
#     )
#     assert txn.to_solders().message.header.num_required_signatures == 3
#     txn.sign_partial(keypair0, keypair2)
#     assert not txn.to_solders().is_signed()
#     txn.sign_partial(keypair1)
#     assert txn.to_solders().is_signed()
#     expected_tx = txlib.Transaction(
#         fee_payer=keypair0.pubkey(),
#         instructions=[ixn],
#         recent_blockhash=stubbed_blockhash,
#     )
#     expected_tx.sign(keypair0, keypair1, keypair2)
#     assert txn == expected_tx
#
#
# def test_recent_blockhash_setter(stubbed_blockhash):
#     """Test the recent_blockhash setter property works."""
#     kp0, kp1, kp2 = Keypair(), Keypair(), Keypair()
#     tx0 = example_tx(stubbed_blockhash, kp0, kp1, kp2)
#     tx1 = example_tx(stubbed_blockhash, kp0, kp1, kp2)
#     tx1.recent_blockhash = tx0.recent_blockhash
#     assert tx0 == tx1
#
#
# def test_transfer_signatures(stubbed_blockhash):
#     """Test signing transfer transactions."""
#     kp1, kp2 = Keypair(), Keypair()
#     transfer1 = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123
#         )
#     )
#     transfer2 = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=kp2.pubkey(), to_pubkey=kp1.pubkey(), lamports=123
#         )
#     )
#     txn = txlib.Transaction(recent_blockhash=stubbed_blockhash)
#     txn.add(transfer1, transfer2)
#     txn.sign(kp1, kp2)
#
#     expected = txlib.Transaction.populate(txn.compile_message(), txn.signatures)
#     assert txn == expected
#
#
# def test_dedup_signatures(stubbed_blockhash):
#     """Test signature deduplication."""
#     kp1, kp2 = Keypair(), Keypair()
#     transfer1 = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123
#         )
#     )
#     transfer2 = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=kp1.pubkey(), to_pubkey=kp2.pubkey(), lamports=123
#         )
#     )
#     txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(
#         transfer1, transfer2
#     )
#     txn.sign(kp1)
#
#
# def test_wire_format_and_desrialize(
#     stubbed_blockhash, stubbed_receiver, stubbed_sender
# ):
#     """Test serialize/derialize transaction to/from wire format."""
#     transfer = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=stubbed_sender.pubkey(), to_pubkey=stubbed_receiver, lamports=49
#         )
#     )
#     expected_txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
#     expected_txn.sign(stubbed_sender)
#     wire_txn = b64decode(
#         b"AVuErQHaXv0SG0/PchunfxHKt8wMRfMZzqV0tkC5qO6owYxWU2v871AoWywGoFQr4z+q/7mE8lIufNl/kxj+nQ0BAAEDE5j2"
#         b"LG0aRXxRumpLXz29L2n8qTIWIY3ImX5Ba9F9k8r9Q5/Mtmcn8onFxt47xKj+XdXXd3C8j/FcPu7csUrz/AAAAAAAAAAAAAAA"
#         b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAxJrndgN4IFTxep3s6kO0ROug7bEsbx0xxuDkqEvwUusBAgIAAQwCAAAAMQAAAAAAAAA="
#     )
#     txn = txlib.Transaction.deserialize(wire_txn)
#     assert txn == expected_txn
#     assert wire_txn == expected_txn.serialize()
#
#
# def test_populate():
#     """Test populating transaction with a message and two signatures."""
#     account_keys = [Pubkey([0] * 31 + [i + 1]) for i in range(5)]
#     msg = Message.new_with_compiled_instructions(
#         num_required_signatures=2,
#         num_readonly_signed_accounts=0,
#         num_readonly_unsigned_accounts=3,
#         account_keys=account_keys,
#         instructions=[
#             CompiledInstruction(
#                 accounts=bytes([1, 2, 3]), data=bytes([9] * 5), program_id_index=4
#             )
#         ],
#         recent_blockhash=Blockhash.default(),
#     )
#     signatures = [
#         Signature(bytes([1] * Signature.LENGTH)),
#         Signature(bytes([2] * Signature.LENGTH)),
#     ]
#     transaction = txlib.Transaction.populate(msg, signatures)
#     assert len(transaction.instructions) == len(msg.instructions)
#     assert len(transaction.signatures) == len(signatures)
#     assert transaction.recent_blockhash == msg.recent_blockhash
#
#
# def test_serialize_unsigned_transaction(
#     stubbed_blockhash, stubbed_receiver, stubbed_sender
# ):
#     """Test to serialize an unsigned transaction."""
#     transfer = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=stubbed_sender.pubkey(), to_pubkey=stubbed_receiver, lamports=49
#         )
#     )
#     txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
#     assert txn.signatures == (Signature.default(),)
#     # Empty signature array fails
#     with pytest.raises(AttributeError):
#         txn.serialize()
#     assert txn.signatures == (Signature.default(),)
#
#     # Set fee payer
#     txn.fee_payer = stubbed_sender.pubkey()
#     # Serialize message
#     assert b64encode(txn.serialize_message()) == (
#         b"AQABAxOY9ixtGkV8UbpqS189vS9p/KkyFiGNyJl+QWvRfZPK/UOfzLZnJ/KJxcbeO8So/l3V13dwvI/xXD7u3LFK8/wAAAAAAAAA"
#         b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMSa53YDeCBU8Xqd7OpDtETroO2xLG8dMcbg5KhL8FLrAQICAAEMAgAAADEAAAAAAAAA"
#     )
#     assert len(txn.instructions) == 1
#     # Signature array populated with null signatures fails
#     with pytest.raises(AttributeError):
#         txn.serialize()
#     assert txn.signatures == (Signature.default(),)
#     # Properly signed transaction succeeds
#     txn.sign(stubbed_sender)
#     assert len(txn.instructions) == 1
#     expected_serialization = b64decode(
#         b"AVuErQHaXv0SG0/PchunfxHKt8wMRfMZzqV0tkC5qO6owYxWU2v871AoWywGoFQr4z+q/7mE8lIufNl/kxj+nQ0BAAEDE5j2"
#         b"LG0aRXxRumpLXz29L2n8qTIWIY3ImX5Ba9F9k8r9Q5/Mtmcn8onFxt47xKj+XdXXd3C8j/FcPu7csUrz/AAAAAAAAAAAAAAA"
#         b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAxJrndgN4IFTxep3s6kO0ROug7bEsbx0xxuDkqEvwUusBAgIAAQwCAAAAMQAAAAAAAAA="
#     )
#     assert txn.serialize() == expected_serialization
#     assert len(txn.signatures) == 1
#     assert txn.signatures != (Signature.default(),)
#
#
# def test_serialize_unsigned_transaction_without_verifying_signatures(
#     stubbed_blockhash, stubbed_receiver, stubbed_sender
# ):
#     """Test to serialize an unsigned transaction without verifying the signatures."""
#     transfer = sp.transfer(
#         sp.TransferParams(
#             from_pubkey=stubbed_sender.pubkey(), to_pubkey=stubbed_receiver, lamports=49
#         )
#     )
#     txn = txlib.Transaction(recent_blockhash=stubbed_blockhash).add(transfer)
#     assert txn.signatures == (Signature.default(),)
#
#     # empty signatures should not fail
#     txn.serialize(verify_signatures=False)
#     assert txn.signatures == (Signature.default(),)
#
#     # Set fee payer
#     txn.fee_payer = stubbed_sender.pubkey()
#     # Serialize message
#     assert b64encode(txn.serialize_message()) == (
#         b"AQABAxOY9ixtGkV8UbpqS189vS9p/KkyFiGNyJl+QWvRfZPK/UOfzLZnJ/KJxcbeO8So/l3V13dwvI/xXD7u3LFK8/wAAAAAAAAA"
#         b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMSa53YDeCBU8Xqd7OpDtETroO2xLG8dMcbg5KhL8FLrAQICAAEMAgAAADEAAAAAAAAA"
#     )
#     assert len(txn.instructions) == 1
#     # Signature array populated with null signatures should not fail
#     txn.serialize(verify_signatures=False)
#     assert txn.signatures == (Signature.default(),)
#
#
# def test_sort_account_metas(stubbed_blockhash):
#     """Test AccountMeta sorting after calling Transaction.compile_message()."""


#
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
