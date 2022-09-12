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
"""Ledger TX generation and processing benchmark."""
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from typing import Dict, List, Optional, Tuple, Union, cast

from aea_cli_benchmark.case_tx_generate.dialogues import (
    FipaDialogues,
    FipaMessage,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogues,
)
from aea_cli_benchmark.case_tx_generate.ledger_utils import (
    DEFAULT_FETCH_LEDGER_ADDR,
    DEFAULT_FETCH_LEDGER_REST_PORT,
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_CHAIN_ID,
    DEFAULT_GANACHE_PORT,
    FETCHD_CONFIGURATION,
    FUNDED_ETH_PRIVATE_KEY_1,
    GANACHE_CONFIGURATION,
    GAS_PRICE_API_KEY,
    _fetchd_context,
    _ganache_context,
    fund_accounts_from_local_validator,
)
from aea_cli_benchmark.utils import make_agent, make_skill, wait_for_condition

from aea import AEA_DIR as _AEA_DIR
from aea.cli.generate_key import _generate_private_key
from aea.configurations.base import ConnectionConfig, ProtocolConfig
from aea.configurations.data_types import PublicId
from aea.crypto.ledger_apis import ETHEREUM_DEFAULT_CURRENCY_DENOM, LedgerApis
from aea.crypto.registries import make_crypto
from aea.crypto.wallet import Wallet
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Query,
    generate_data_model,
)
from aea.helpers.transaction.base import Terms
from aea.protocols.base import Message, Protocol
from aea.registries.resources import Resources
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.connections.ledger.connection import LedgerConnection
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.open_aea.protocols.signing.dialogues import SigningDialogue
from packages.open_aea.protocols.signing.message import SigningMessage


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)
AEA_DIR = Path(_AEA_DIR)
PACKAGES_DIR = AEA_DIR.parent / "packages"


class LedgerApiHandler(Handler):
    """Dummy handler to handle messages."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id

    def setup(self) -> None:
        """Noop setup."""
        self.context.ledger_api_dialogues = LedgerApiDialogues(
            name=self.skill_id, skill_context=self.context
        )
        self.tx_settled_counter = 0

        self.context.signing_dialogues = SigningDialogues(str(self.skill_id))
        self.event = threading.Event()

    def teardown(self) -> None:
        """Noop teardown."""

    def handle(self, ledger_api_msg: Message) -> None:
        """Handle incoming message."""
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue],
            self.context.ledger_api_dialogues.update(ledger_api_msg),
        )
        if ledger_api_msg.performative is LedgerApiMessage.Performative.RAW_TRANSACTION:
            self._handle_raw_transaction(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            is LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self._handle_transaction_digest(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        ):
            self._handle_transaction_receipt(ledger_api_msg, ledger_api_dialogue)
        else:
            raise Exception("BAD ENVELOPE", ledger_api_msg)

    def _handle_raw_transaction(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info("received raw transaction={}".format(ledger_api_msg))
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=ledger_api_msg.raw_transaction,
            terms=ledger_api_dialogue.associated_fipa_dialogue.terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
        )

    def _handle_transaction_digest(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_digest performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "transaction was successfully submitted. Transaction digest={}".format(
                ledger_api_msg.transaction_digest
            )
        )
        ledger_api_msg_ = ledger_api_dialogue.reply(
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            target_message=ledger_api_msg,
            transaction_digest=ledger_api_msg.transaction_digest,
        )
        self.context.logger.info("checking transaction is settled.")
        self.context.outbox.put_message(message=ledger_api_msg_)

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_receipt performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        fipa_dialogue = ledger_api_dialogue.associated_fipa_dialogue
        is_settled = LedgerApis.is_transaction_settled(
            fipa_dialogue.terms.ledger_id, ledger_api_msg.transaction_receipt.receipt
        )
        if is_settled:
            self.tx_settled_counter += 1

        self.event.set()


class GenericSigningHandler(Handler):
    """Implement the signing handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        signing_msg = cast(SigningMessage, message)

        # recover dialogue
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        if signing_dialogue is None:
            self._handle_unidentified_dialogue(signing_msg)
            return

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_TRANSACTION:
            self._handle_signed_transaction(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param signing_msg: the message
        """
        self.context.logger.info(
            "received invalid signing message={}, unidentified dialogue.".format(
                signing_msg
            )
        )

    def _handle_signed_transaction(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.info("transaction signing was successful.")
        ledger_api_dialogue = signing_dialogue.associated_ledger_api_dialogue
        last_ledger_api_msg = ledger_api_dialogue.last_incoming_message
        if last_ledger_api_msg is None:
            raise ValueError("Could not retrieve last message in ledger api dialogue")
        ledger_api_msg = ledger_api_dialogue.reply(
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            target_message=last_ledger_api_msg,
            signed_transaction=signing_msg.signed_transaction,
        )
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info("sending transaction to ledger.")

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.info(
            "transaction signing was not successful. Error_code={} in dialogue={}".format(
                signing_msg.error_code, signing_dialogue
            )
        )

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.warning(
            "cannot handle signing message of performative={} in dialogue={}.".format(
                signing_msg.performative, signing_dialogue
            )
        )


class Case:
    """TBenchmark case implementation."""

    LEDGER_TX_SETTLE_TIMEOUT = 20
    QUERY = Query(
        [Constraint("author", ConstraintType("==", "Stephen King"))],
        model=generate_data_model("book_author", {"author": "author of the book"}),
    )

    def __init__(self, ledger_id: str, ledger_api_config: Dict, private_keys: Dict):
        """
        Init case.

        :param ledger_id: str, ledger id, one of fetchai, ethereum
        :param ledger_api_config: config for ledger connection
        :param private_keys: private keys dict to use for wallet contruction
        """
        self.ledger_id = ledger_id
        self.ledger_api_config = ledger_api_config
        self.agent_name = "Agent"
        self.skill_public_id = PublicId.from_str("benchmark/test_skill:0.1.0")
        self.private_keys = private_keys

    @property
    def ledger_handler(self) -> LedgerApiHandler:
        """Get ledger api handler instance."""
        return self.skill.handlers["ledger_handler"]

    @property
    def tx_settled_counter(self) -> int:
        """Get amount of txs settled."""
        return self.ledger_handler.tx_settled_counter

    def wait_tx_settled(self) -> None:
        """Wait for tx settled."""
        self.ledger_handler.event.wait(self.LEDGER_TX_SETTLE_TIMEOUT)
        self.ledger_handler.event.clear()

    @property
    def ledger_api_dialogues(self) -> LedgerApiDialogues:
        """Get ledger api dialogues."""
        return self.skill.skill_context.ledger_api_dialogues

    @property
    def my_addr(self) -> str:
        """Get my agent address."""
        return self.skill.skill_context.agent_address

    def make_ledger_msg(
        self, sender_address: str, counterparty_address: str
    ) -> LedgerApiMessage:
        """Make ledger api message to be signed and published over ledger netework."""
        _, dialogue = self.fipa_dialogues.create(
            counterparty="some",
            performative=FipaMessage.Performative.CFP,
            query=self.QUERY,
        )
        dialogue.terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=sender_address,
            counterparty_address=counterparty_address,
            amount_by_currency_id={"FET": -2},
            quantities_by_good_id={"test": 10},
            is_sender_payable_tx_fee=True,
            nonce="",
            fee_by_currency_id={"FET": 45000},
        )

        ledger_api_msg, ledger_api_dialogue = self.ledger_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
            terms=dialogue.terms,
        )
        ledger_api_dialogue.associated_fipa_dialogue = dialogue
        return ledger_api_msg

    def start_agent(self) -> None:
        """Construct and start agent."""
        wallet = Wallet(self.private_keys, self.private_keys)
        resources = Resources()
        pconfig = ProtocolConfig(
            name=LedgerApiMessage.protocol_id.name,
            author=LedgerApiMessage.protocol_id.author,
            version=LedgerApiMessage.protocol_id.version,
            protocol_specification_id=LedgerApiMessage.protocol_specification_id,
        )

        resources.add_protocol(
            Protocol(
                pconfig,
                message_class=LedgerApiMessage,
            )
        )

        connection = LedgerConnection(
            data_dir="./",
            configuration=ConnectionConfig(
                connection_id=LedgerConnection.connection_id,
                **{"ledger_apis": self.ledger_api_config},
            ),
            identity=None,
        )
        resources.add_connection(connection)

        self.agent = make_agent(
            agent_name=self.agent_name,
            resources=resources,
            wallet=wallet,
            packages_dir=str(PACKAGES_DIR),
        )

        skill = make_skill(
            self.agent,
            handlers={
                "ledger_handler": LedgerApiHandler,
                "sign_handler": GenericSigningHandler,
            },
            skill_id=self.skill_public_id,
        )
        self.skill = skill
        self.fipa_dialogues = FipaDialogues(
            name=skill.public_id, skill_context=skill.skill_context
        )
        skill.skill_context.agent_address
        self.agent.resources.add_skill(skill)
        self.thread = Thread(target=self.agent.start, daemon=True)
        self.thread.start()
        wait_for_condition(lambda: self.agent.is_running, timeout=5)

    def stop_agent(self) -> None:
        """Stop agent."""
        self.agent.runtime.stop()
        wait_for_condition(lambda: not self.agent.is_running, timeout=20)
        self.thread.join(60)

    def put_message_and_wait(self, msg: Message) -> None:
        """Put ledger api message and wait tx constructed, signed and settled."""
        self.agent.outbox.put_message(msg)
        self.wait_tx_settled()

    def run(self, time_in_seconds: float) -> Tuple[int, float]:
        """Run a test case."""
        self.start_agent()

        if self.ledger_id == "fetchai":
            fund_accounts_from_local_validator([self.my_addr], 10000000000000000000)

        target_addr = make_crypto(self.ledger_id).address
        start_time = time.time()
        execution_time = 0

        while execution_time < time_in_seconds:
            msg = self.make_ledger_msg(self.my_addr, target_addr)
            self.put_message_and_wait(msg)
            counted = self.tx_settled_counter
            execution_time = time.time() - start_time

        return counted, execution_time


def run(ledger_id: str, running_time: float) -> List[Tuple[str, Union[int, float]]]:
    """Check tx processing speed."""
    # pylint: disable=import-outside-toplevel,unused-import
    # import manually due to some lazy imports in decision_maker
    import aea.decision_maker.default  # noqa: F401

    with TemporaryDirectory() as tmp_dir:
        private_key_path = Path(tmp_dir) / "priv.key"

        if ledger_id == "fetchai":
            ctx = _fetchd_context(FETCHD_CONFIGURATION, timeout=5)
            ledger_api_config = {
                "fetchai": {
                    "address": f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}",
                    "chain_id": FETCHD_CONFIGURATION["chain_id"],
                    "denom": FETCHD_CONFIGURATION["denom"],
                }
            }
            private_keys = private_keys = _generate_private_key(
                ledger_id, private_key_path
            )
        elif ledger_id == "ethereum":
            ctx = _ganache_context(
                GANACHE_CONFIGURATION,
                DEFAULT_GANACHE_ADDR,
                DEFAULT_GANACHE_PORT,
                timeout=5,
            )
            ledger_api_config = {
                "ethereum": {
                    "address": f"{DEFAULT_GANACHE_ADDR}:{DEFAULT_GANACHE_PORT}",
                    "chain_id": DEFAULT_GANACHE_CHAIN_ID,
                    "denom": ETHEREUM_DEFAULT_CURRENCY_DENOM,
                    "gas_price_api_key": GAS_PRICE_API_KEY,
                }
            }
            with open(private_key_path, "w") as f:
                f.write(FUNDED_ETH_PRIVATE_KEY_1)
            private_keys = {"ethereum": private_key_path}
        else:
            raise ValueError(f"Bad ledger id {ledger_id}")

        with ctx:
            case = Case(
                ledger_id=ledger_id,
                ledger_api_config=ledger_api_config,
                private_keys=private_keys,
            )

            tx_processed, execution_time = case.run(
                time_in_seconds=running_time,
            )

        return [
            ("run_time (seconds)", execution_time),
            ("tx process speed (seconds)", execution_time / tx_processed),
            ("tx processed", tx_processed),
        ]
