# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Memory usage check."""
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Tuple, Union
from unittest.mock import patch

from aea_cli_benchmark.utils import get_mem_usage_in_mb

from aea.common import Address
from aea.configurations.data_types import PublicId
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import DecisionMakerHandler
from aea.helpers.transaction.base import RawTransaction, Terms
from aea.identity.base import Identity
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.open_aea.protocols.signing.dialogues import SigningDialogue
from packages.open_aea.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.open_aea.protocols.signing.message import SigningMessage


class SigningDialogues(BaseSigningDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, self_address: Address) -> None:  # pylint: disable=useless-return
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return SigningDialogue.Role.SKILL

        BaseSigningDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=SigningDialogue,
        )

        return None


def make_desc_maker_wallet(
    ledger_id: str, key_path: str
) -> Tuple[DecisionMaker, Wallet]:
    """Construct decision maker and wallet."""
    wallet = Wallet({ledger_id: key_path})
    agent_name = "test"
    identity = Identity(
        agent_name,
        addresses=wallet.addresses,
        default_address_key=ledger_id,
        public_keys=wallet.public_keys,
    )
    config = {}  # type: ignore
    decision_maker_handler = DecisionMakerHandler(
        identity=identity, wallet=wallet, config=config
    )
    decision_maker = DecisionMaker(decision_maker_handler)
    return decision_maker, wallet


def sign_txs(
    decision_maker: DecisionMaker, wallet: Wallet, num_runs: int, ledger_id: str
) -> float:
    """Sign txs sprcified amount fo runs and return time taken (seconds)."""

    amount = 10000
    fc2 = make_crypto(ledger_id)
    sender_address = wallet.addresses[ledger_id]
    ledger_api = make_ledger_api(ledger_id)

    if ledger_id == "fetchai":
        with patch(
            "aea_ledger_fetchai._cosmos._CosmosApi._try_get_account_number_and_sequence",
            return_value=(987, 0),
        ), patch(
            "aea_ledger_fetchai._cosmos._CosmosApi.get_balance", return_value=100000
        ):
            transfer_transaction = ledger_api.get_transfer_transaction(
                sender_address=sender_address,
                destination_address=fc2.address,
                amount=amount,
                tx_fee=1000,
                tx_nonce="something",
            )
    elif ledger_id == "cosmos":
        with patch(
            "aea_ledger_cosmos.cosmos._CosmosApi._try_get_account_number_and_sequence",
            return_value=(987, 0),
        ), patch(
            "aea_ledger_cosmos.cosmos._CosmosApi.get_balance", return_value=100000
        ):
            transfer_transaction = ledger_api.get_transfer_transaction(
                sender_address=sender_address,
                destination_address=fc2.address,
                amount=amount,
                tx_fee=1000,
                tx_nonce="something",
            )
    elif ledger_id == "ethereum":
        transfer_transaction = {"gasPrice": 30, "nonce": 1, "gas": 20000}
    else:
        raise ValueError("Ledger not supported!")

    signing_dialogues = SigningDialogues(str(PublicId("author", "a_skill", "0.1.0")))
    signing_msg = SigningMessage(
        performative=SigningMessage.Performative.SIGN_TRANSACTION,
        dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
        terms=Terms(
            ledger_id=ledger_id,
            sender_address="pk1",
            counterparty_address="pk2",
            amount_by_currency_id={"FET": -1},
            is_sender_payable_tx_fee=True,
            quantities_by_good_id={"good_id": 10},
            nonce="transaction nonce",
        ),
        raw_transaction=RawTransaction(ledger_id, transfer_transaction),  # type: ignore
    )
    start_time = time.time()
    for _ in range(num_runs):
        signing_msg._sender = None  # pylint: disable=protected-access
        signing_msg._to = None  # pylint: disable=protected-access
        signing_msg._slots.dialogue_reference = (  # type: ignore# pylint: disable=protected-access
            signing_dialogues.new_self_initiated_dialogue_reference()
        )
        signing_dialogue = signing_dialogues.create_with_message(
            "decision_maker", signing_msg
        )
        if signing_dialogue is None:
            raise ValueError("dialogue failure")
        decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = decision_maker.message_out_queue.get(timeout=2)
        if (
            signing_msg_response.performative
            != SigningMessage.Performative.SIGNED_TRANSACTION
        ):
            raise ValueError("Sign message error!")

    return time.time() - start_time


def run(ledger_id: str, amount_of_tx: int) -> List[Tuple[str, Union[int, float]]]:
    """Check memory usage."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    with TemporaryDirectory() as tmp_dir:
        key_file = str(Path(tmp_dir) / "key-file")
        crypto = make_crypto(ledger_id)
        crypto.dump(key_file)
        decision_maker, wallet = make_desc_maker_wallet(ledger_id, key_file)
        decision_maker.start()
        mem_usage = get_mem_usage_in_mb()

        running_time = sign_txs(decision_maker, wallet, amount_of_tx, ledger_id)
        mem_usage = get_mem_usage_in_mb() - mem_usage
        decision_maker.stop()
        rate = running_time / amount_of_tx

        return [
            ("run_time (seconds)", running_time),
            ("rate (envelopes/second)", rate),
            ("mem usage (Mb)", mem_usage),
        ]
