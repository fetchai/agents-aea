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
"""Solana module wrapping the public and private key cryptography and ledger api."""
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from aea_ledger_solana.constants import (
    DEFAULT_ADDRESS,
    DEFAULT_CHAIN_ID,
    _SOLANA,
    _VERSION,
)
from aea_ledger_solana.crypto import SolanaCrypto
from aea_ledger_solana.faucet import SolanaFaucetApi  # noqa: F401
from aea_ledger_solana.helper import SolanaHelper
from aea_ledger_solana.solana_api import SolanaApiClient
from aea_ledger_solana.transaction import SolanaTransaction
from aea_ledger_solana.transaction_instruction import TransactionInstruction
from anchorpy import Context, Idl, Program  # type: ignore
from solana.blockhash import BlockhashCache
from solana.transaction import Transaction  # type: ignore
from solders import system_program as ssp  # type: ignore
from solders.instruction import Instruction
from solders.pubkey import Pubkey as PublicKey  # type: ignore
from solders.signature import Signature  # type: ignore
from solders.system_program import (  # type: ignore; SYS_PROGRAM_ID,
    CreateAccountParams,
    CreateAccountWithSeedParams,
)
from solders.system_program import ID as SYS_PROGRAM_ID  # type: ignore
from solders.system_program import (  # type: ignore; SYS_PROGRAM_ID,
    TransferParams,
    create_account,
    transfer,
)

from aea.common import Address, JSONLike
from aea.crypto.base import LedgerApi
from aea.helpers.base import try_decorator


class SolanaApi(LedgerApi, SolanaHelper):
    """Class to interact with the Solana Web3 APIs."""

    identifier = _SOLANA

    def __init__(self, **kwargs: Any):
        """
        Initialize the Solana ledger APIs.

        :param kwargs: keyword arguments
        """

        """Type for commitment."""

        self._api = SolanaApiClient(
            endpoint=kwargs.pop("address", DEFAULT_ADDRESS),
        )

        self._chain_id = kwargs.pop("chain_id", DEFAULT_CHAIN_ID)
        self._version = _VERSION
        self.BlockhashCache = BlockhashCache(ttl=10)
        self._get_latest_hash()

    def _get_latest_hash(self):
        """Get the latest block hash."""
        result = self._api.get_latest_blockhash()
        blockhash_json = result.value.to_json()
        blockhash = json.loads(blockhash_json)
        self._hash = blockhash["blockhash"]
        self.BlockhashCache.set(blockhash=self._hash, slot=result.context.slot)

    @property
    def latest_hash(self):
        """Get the latest hash."""
        self._get_latest_hash()
        return self._hash

    def wait_get_receipt(
        self, transaction_digest: str
    ) -> Tuple[Optional[JSONLike], bool]:
        """Wait for the transaction to be settled and return the receipt."""
        transaction_receipt = None
        not_settled = True
        elapsed_time = 0
        time_to_wait = 40
        sleep_time = 0.25
        while not_settled and elapsed_time < time_to_wait:
            elapsed_time += sleep_time
            time.sleep(sleep_time)
            transaction_receipt = self.get_transaction_receipt(transaction_digest)
            if transaction_receipt is None:
                continue
            is_settled = self.is_transaction_settled(transaction_receipt)
            not_settled = not is_settled

        return transaction_receipt, not not_settled

    def construct_and_settle_tx(
        self,
        account1: SolanaCrypto,
        account2: SolanaCrypto,
        tx_params: dict,
    ) -> Tuple[str, JSONLike, bool]:
        """Construct and settle a transaction."""
        transfer_transaction = self.get_transfer_transaction(
            **tx_params, tx_fee=0, tx_nonce=""
        )
        # add nonce
        transfer_transaction = self.add_nonce(transfer_transaction)

        signed_transaction = account1.sign_transaction(transfer_transaction)

        transaction_digest = self.send_signed_transaction(signed_transaction)
        if transaction_digest is None:
            raise Exception("Failed to submit transfer transaction!")

        transaction_receipt, is_settled = self.wait_get_receipt(transaction_digest)

        if transaction_receipt is None:
            raise Exception("Failed to settle transfer transaction!")

        return transaction_digest, transaction_receipt, is_settled

    @property
    def api(self) -> SolanaApiClient:
        """Get the underlying API object."""
        return self._api

    def update_with_gas_estimate(self, transaction: JSONLike) -> JSONLike:
        """
        Attempts to update the transaction with a gas estimate

        **NOT APPLICABLE**

        :param transaction: the transaction
        :return: the updated transaction
        """

        return transaction

    def get_balance(
        self, address: Address, raise_on_try: bool = False
    ) -> Optional[int]:
        """Get the balance of a given account."""
        return self._try_get_balance(address, raise_on_try=raise_on_try)

    @try_decorator("Unable to retrieve balance: {}", logger_method="warning")
    def _try_get_balance(self, address: Address, **_kwargs: Any) -> Optional[int]:
        """Get the balance of a given account."""
        response = self._api.get_balance(
            PublicKey.from_string(address), commitment="processed"
        )  # pylint: disable=no-member
        return response.value

    def get_state(
        self, callable_name: str, *args: Any, raise_on_try: bool = False, **kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Call a specified function on the underlying ledger API.

        This usually takes the form of a web request to be waited synchronously.

        :param callable_name: the name of the API function to be called.
        :param args: the positional arguments for the API function.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: the keyword arguments for the API function.
        :return: the ledger API response.
        """
        return self._get_account_state(
            address=callable_name, *args, raise_on_try=raise_on_try, **kwargs
        )

    @try_decorator("Unable to get state: {}", logger_method="warning")
    def _get_account_state(  # pylint: disable=unused-argument
        self, address: str, *args: Any, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Try to get account state.."""

        if "raise_on_try" in kwargs:
            logging.info(
                f"popping `raise_on_try` from {self.__class__.__name__}.get_state kwargs"  # pylint: disable=protected-access
            )
            kwargs.pop("raise_on_try")

        return self._api.get_account_state(address)

    def get_transfer_transaction(  # pylint: disable=arguments-differ
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param tx_nonce: verifies the authenticity of the tx
        :param kwargs: the keyword arguments.
        :return: the transfer transaction
        """
        chain_id = kwargs.get("kwargs", None)
        chain_id = chain_id if chain_id is not None else self._chain_id

        state = self.get_state(destination_address)
        # this is if there is no account yet at the destination address

        if state is None:
            # we need to create the account we first get the tx
            # to create the account
            # then we get the tx to transfer the funds
            # then we combine the two txs
            # then we sign the combined tx
            # then we return the combined tx

            create_account_ixn = self._api.get_create_account_instructions(
                sender_address, destination_address
            )

            transfer_ixn = self._api.get_transfer_tx(
                sender_address, destination_address, amount
            )

            txn = Transaction(
                fee_payer=PublicKey.from_string(sender_address),
            )

            ixn_1 = Instruction.from_json(json.dumps(create_account_ixn))
            ixn_2 = Instruction.from_json(transfer_ixn.to_json())

            # in solana we first create the account then we transfer the funds
            txn.add(ixn_1).add(ixn_2)

        else:
            txn = Transaction(fee_payer=PublicKey.from_string(sender_address)).add(
                transfer(
                    TransferParams(
                        from_pubkey=PublicKey.from_string(sender_address),
                        to_pubkey=PublicKey.from_string(destination_address),
                        lamports=amount,
                    )
                )
            )

        tx = txn.to_solders().to_json()  # pylint: disable=protected-access
        return json.loads(tx)

    def send_signed_transaction(
        self, tx_signed: JSONLike, raise_on_try: bool = False
    ) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :param raise_on_try: whether the method will raise or log on error
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(tx_signed, raise_on_try=True)
        tx = json.loads(tx_digest)
        return tx["result"]

    @try_decorator("Unable to send transaction: {}", logger_method="warning")
    def _try_send_signed_transaction(
        self, tx_signed: JSONLike, **_kwargs: Any
    ) -> Optional[str]:
        """
        Try send a signed transaction.

        :param tx_signed: the signed transaction
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: tx_digest, if present
        """

        stxn = SolanaTransaction.from_json(tx_signed)
        txn_resp = self._api.send_raw_transaction(bytes(stxn.serialize()))
        retries = 2
        while True and retries > 0:
            try:
                tx_digest = str(txn_resp.value)
                self.get_transaction_receipt(tx_digest)
                break
            except ValueError:
                time.sleep(1)
            retries -= 1

        return txn_resp.to_json()

    def send_signed_transactions(
        self,
        signed_transactions: List[JSONLike],
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[List[str]]:
        """
        Atomically send multiple of transactions.

        :param signed_transactions: the signed transactions to bundle together and send.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: the keyword arguments.
        """
        raise NotImplementedError

    def get_transaction_receipt(
        self, tx_digest: str, raise_on_try: bool = False
    ) -> Optional[JSONLike]:
        """
        Get the transaction receipt for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :param raise_on_try: whether the method will raise or log on error
        :return: the tx receipt, if present
        """
        tx_receipt = self._try_get_transaction_receipt(
            tx_digest,
            raise_on_try=raise_on_try,
        )

        return tx_receipt

    @try_decorator(
        "Error when attempting getting tx receipt: {}", logger_method="debug"
    )
    def _try_get_transaction_receipt(
        self, tx_digest: str, **_kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Try get the transaction receipt.

        :param tx_digest: the digest associated to the transaction.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: the tx receipt, if present
        """

        tx_receipt = self._api.get_transaction(
            Signature.from_string(tx_digest)
        )  # pylint: disable=no-member

        tx = json.loads(tx_receipt.to_json())
        return tx["result"]

    def get_transaction(
        self,
        tx_digest: str,
        raise_on_try: bool = False,
    ) -> Optional[JSONLike]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :param raise_on_try: whether the method will raise or log on error
        :return: the tx, if present
        """
        tx = self._try_get_transaction(tx_digest, raise_on_try=raise_on_try)
        return tx

    @try_decorator("Error when attempting getting tx: {}", logger_method="debug")
    def _try_get_transaction(
        self, tx_digest: str, **_kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Get the transaction.

        :param tx_digest: the transaction digest.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: the tx, if found
        """
        tx = self._api.get_transaction(Signature.from_string(tx_digest))

        # pylint: disable=no-member
        return json.loads(tx.value.to_json())

    @staticmethod
    def create_default_account(
        from_address: str,
        new_account_address: str,
        lamports: int,
        space: int,
        program_id: Optional[str] = SYS_PROGRAM_ID,
    ):
        """
        Build a create account transaction.

        :param from_address: the sender public key
        :param new_account_address: the new account public key
        :param lamports: the amount of lamports to send
        :param space: the space to allocate
        :param program_id: the program id
        :return: the tx, if present
        """
        params = CreateAccountParams(
            PublicKey(from_address),
            PublicKey(new_account_address),
            lamports,
            space,
            PublicKey(program_id),
        )
        createAccountInstruction = create_account(params)
        txn = Transaction(fee_payer=from_address).add(createAccountInstruction)
        tx = txn._solders.to_json()  # pylint: disable=protected-access
        return json.loads(tx)

    @staticmethod
    def create_pda(
        from_address: str,
        new_account_address: str,
        base_address: str,
        seed: str,
        lamports: int,
        space: int,
        program_id: str,
    ):
        """
        Build a create pda transaction.

        :param from_address: the sender public key
        :param new_account_address: the new account public key
        :param base_address: base address
        :param seed: seed
        :param lamports: the amount of lamports to send
        :param space: the space to allocate
        :param program_id: the program id
        :return: the tx, if present
        """
        params = CreateAccountWithSeedParams(
            PublicKey(from_address),
            PublicKey(new_account_address),
            PublicKey(base_address),
            seed,
            lamports,
            space,
            PublicKey(program_id),
        )
        createPDAInstruction = TransactionInstruction.from_solders(
            ssp.create_account_with_seed(params.to_solders())
        )
        txn = Transaction().add(createPDAInstruction)
        tx = txn._solders.to_json()  # pylint: disable=protected-access
        return json.loads(tx)

    def get_contract_instance(
        self, contract_interface: Dict[str, str], contract_address: Optional[str] = None
    ) -> Any:
        """
        Get the instance of a contract.

        :param contract_interface: the contract interface.
        :param contract_address: the contract address.
        :return: the contract instance
        """
        bytecode_path = None  # bytecode is not provided for the moment
        program_id = PublicKey.from_string(contract_address)
        idl = Idl.from_json(json.dumps(contract_interface["idl"]))
        pg = Program(idl, program_id)

        pg.provider.connection = self.api

        if bytecode_path is not None:
            # opening for [r]eading as [b]inary
            in_file = open(bytecode_path, "rb")
            bytecode = in_file.read()
        else:
            bytecode = None
        return {"program": pg, "bytecode": bytecode}

    def get_deploy_transaction(
        self,
        contract_interface: Dict[str, str],
        deployer_address: Address,
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Get the transaction to deploy the smart contract.

        :param contract_interface: the contract interface.
        :param deployer_address: The address that will deploy the contract.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: the keyword arguments.
        :returns tx: the transaction dictionary.
        """

        """
        if contract_interface["bytecode"] is None or contract_interface["program_keypair"] is None:
            raise ValueError("Bytecode or program_keypair is required")

        # check if solana cli is installed
        result = subprocess.run(
            ["solana --version"], capture_output=True, text=True, shell=True)
        if result.stderr != "":
            raise ValueError(result.stderr)

        # save keys in uint8 array temp
        value = struct.unpack('64B', payer_keypair.entity.secret_key)
        uint8_array = array.array('B', value)
        payer_uint8 = uint8_array.tolist()
        temp_dir_payer = Path(tempfile.mkdtemp())
        temp_file_payer = temp_dir_payer / "payer.json"
        temp_file_payer.write_text(str(payer_uint8))

        value = struct.unpack(
            '64B', contract_interface["program_keypair"].entity.secret_key)
        uint8_array = array.array('B', value)
        program_uint8 = uint8_array.tolist()
        temp_dir_program = Path(tempfile.mkdtemp())
        temp_file_program = temp_dir_program / "program.json"
        temp_file_program.write_text(str(program_uint8))

        t = SolanaCrypto(temp_file_payer)
        temp_dir_bytecode = Path(tempfile.mkdtemp())
        temp_file_bytecode = temp_dir_bytecode / "bytecode.so"
        temp_file_bytecode.write_bytes(contract_interface["bytecode"])

        cmd = f'''solana program deploy --url {DEFAULT_ADDRESS} -v --keypair {str(temp_file_payer)} --program-id {str(temp_file_program)} {str(temp_file_bytecode)}'''

        result = subprocess.run(
            [cmd], capture_output=True, text=True, shell=True)

        if result.stderr != "":
            raise ValueError(result.stderr)

        return result.stdout
        """
        raise NotImplementedError

    def contract_method_call(
        self,
        contract_instance: Any,
        method_name: str,
        **method_args: Any,
    ) -> Optional[JSONLike]:
        """
        Call a contract's method

        **TOBEIMPLEMENTED**

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract call parameters

        # noqa: DAR202

        :return: the call result
        """
        raise NotImplementedError

    def build_transaction(  # pylint: disable=too-many-arguments
        self,
        contract_instance: Any,
        method_name: str,
        method_args: Optional[Dict[Any, Any]],
        tx_args: Optional[Dict[Any, Any]],
        raise_on_try: bool = False,
    ) -> Optional[JSONLike]:
        """Prepare a transaction

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract parameters
        :param tx_args: the transaction parameters
        :param raise_on_try: whether the method will raise or log on error
        :return: the transaction
        """
        if method_args is None:
            raise ValueError("`method_args` can not be None")

        if method_args["data"] is None:
            raise ValueError("Data is required")
        if method_args["accounts"] is None:
            raise ValueError("Accounts are required")
        if "remaining_accounts" not in method_args:
            method_args["remaining_accounts"] = None

        data = method_args["data"]
        accounts = method_args["accounts"]
        remaining_accounts = method_args["remaining_accounts"]

        txn = contract_instance.transaction[method_name](
            *data, ctx=Context(accounts=accounts, remaining_accounts=remaining_accounts)
        )
        return json.loads(txn.to_solders().to_json())

    def get_transaction_transfer_logs(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        contract_instance: Any,
        tx_hash: str,
        target_address: Optional[str] = None,
    ) -> Optional[JSONLike]:
        """
        Get all transfer events derived from a transaction.

        :param contract_instance: contract instance
        :param tx_hash: the transaction hash
        :param target_address: optional address to filter tranfer events to just those that affect it
        :return: the transfer logs
        """
        try:
            tx_receipt = self.get_transaction_receipt(tx_hash)
            if tx_receipt is None:
                raise ValueError  # pragma: nocover

        except (  # pragma: nocover # pylint: disable=broad-except
            Exception,
            ValueError,
        ):
            return dict()

        keys = tx_receipt["transaction"]["message"]["accountKeys"]  # type: ignore
        if target_address:
            transfers = {
                "preBalances": [
                    {"address": keys[idx], "balance": balance}
                    for idx, balance in enumerate(tx_receipt["meta"]["preBalances"])  # type: ignore
                    if keys[idx] == target_address
                ],
                "postBalances": [
                    {"address": keys[idx], "balance": balance}
                    for idx, balance in enumerate(tx_receipt["meta"]["postBalances"])  # type: ignore
                    if keys[idx] == target_address
                ],
            }
        else:
            transfers = {
                "preBalances": [
                    {"address": keys[idx], "balance": balance}
                    for idx, balance in enumerate(tx_receipt["meta"]["preBalances"])  # type: ignore
                ],
                "postBalances": [
                    {"address": keys[idx], "balance": balance}
                    for idx, balance in enumerate(tx_receipt["meta"]["postBalances"])  # type: ignore
                ],
            }

        return transfers  # type: ignore  # actually ok
