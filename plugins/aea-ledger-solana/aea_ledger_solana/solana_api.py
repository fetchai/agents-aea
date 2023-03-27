import json
from dataclasses import dataclass
from random import randint
from typing import NewType

import solders.system_program as sp
from anchorpy import Program
from solana.blockhash import BlockhashCache  # type: ignore
from solana.rpc.api import Client as ApiClient
from solders.instruction import AccountMeta
from solders.null_signer import NullSigner
from solders.pubkey import Pubkey
from solders.pubkey import Pubkey as PublicKey
from solders.system_program import CreateAccountParams
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.system_program import TransferParams, create_account, transfer
from spl.token.client import Token as SplClient
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID
from spl.token.core import AccountInfo


class HashNotProvided:
    """"""


@dataclass
class SolanaApiClient(ApiClient):
    """Class to interact with the Solana ledger APIs."""

    def __init__(self, *args, **kwargs):
        """Instantiate the client."""
        super().__init__(*args, **kwargs)

    def transfer(self, *args, **kwargs):
        """Transfer tokens."""

    def get_create_account_instructions(
        self,
        sender_address,
        destination_address,
        lamports: int = 100000,
        space: int = 1,
    ):
        """Create a new account."""
        required_balance = SplClient.get_min_balance_rent_for_exempt_for_account(self)

        seed = str(randint(0, 1000000000))
        acc = Pubkey.create_with_seed(
            Pubkey.from_string(sender_address),
            seed,
            SYS_PROGRAM_ID,
        )
        params = sp.CreateAccountWithSeedParams(
            from_pubkey=Pubkey.from_string(sender_address),
            to_pubkey=acc,
            base=Pubkey.from_string(sender_address),
            seed=seed,
            lamports=max([lamports, required_balance]),
            space=space,
            owner=SYS_PROGRAM_ID,
        )
        ix_create_pda = sp.create_account_with_seed(params)
        ix_create_pda_json = json.loads(ix_create_pda.to_json())
        return ix_create_pda_json

    def get_transfer_tx(self, from_account, to_account, amount):
        """Create a transfer tx."""
        params = TransferParams(
            from_pubkey=PublicKey.from_string(from_account),
            to_pubkey=PublicKey.from_string(to_account),
            lamports=amount,
        )
        return transfer(params)

    def get_account_state(self, account_address: str):
        """Get account state."""
        account_object = self.get_account_info_json_parsed(
            PublicKey.from_string(account_address)
        )
        account_info_val = account_object.value
        # note we dont currently parse this back as json.
        return account_info_val
