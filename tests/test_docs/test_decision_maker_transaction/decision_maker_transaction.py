# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

"""This module contains the tests for the code-blocks in the decision-maker-transaction.md file."""

import logging
import time
from threading import Thread
from typing import Optional, cast

from aea_ledger_fetchai import FetchAICrypto

from aea.aea_builder import AEABuilder
from aea.configurations.base import PublicId, SkillConfig
from aea.crypto.helpers import create_private_key
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.helpers.transaction.base import RawTransaction, Terms
from aea.identity.base import Identity
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue
from aea.skills.base import Handler, Model, Skill, SkillContext

from packages.fetchai.protocols.signing.dialogues import SigningDialogue
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.fetchai.protocols.signing.message import SigningMessage

from tests.conftest import get_wealth_if_needed


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fetchai_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fetchai_private_key_2.txt"


def run():
    """Run demo."""

    # Create a private key
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_1
    )

    # Instantiate the builder and build the AEA
    # By default, the default protocol, error skill and stub connection are added
    builder = AEABuilder()

    builder.set_name("my_aea")

    builder.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_1)

    # Create our AEA
    my_aea = builder.build()

    # add a simple skill with handler
    skill_context = SkillContext(my_aea.context)
    skill_config = SkillConfig(name="simple_skill", author="fetchai", version="0.1.0")
    signing_handler = SigningHandler(
        skill_context=skill_context, name="signing_handler"
    )
    signing_dialogues_model = SigningDialogues(
        skill_context=skill_context,
        name="signing_dialogues",
        self_address=str(skill_config.public_id),
    )

    simple_skill = Skill(
        skill_config,
        skill_context,
        handlers={signing_handler.name: signing_handler},
        models={signing_dialogues_model.name: signing_dialogues_model},
    )
    my_aea.resources.add_skill(simple_skill)

    # create a second identity
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_2
    )

    counterparty_wallet = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_2})
    get_wealth_if_needed(counterparty_wallet.addresses["fetchai"])

    counterparty_identity = Identity(
        name="counterparty_aea",
        addresses=counterparty_wallet.addresses,
        public_keys=counterparty_wallet.public_keys,
        default_address_key=FetchAICrypto.identifier,
    )

    # create signing message for decision maker to sign
    terms = Terms(
        ledger_id=FetchAICrypto.identifier,
        sender_address=my_aea.identity.address,
        counterparty_address=counterparty_identity.address,
        amount_by_currency_id={"FET": -1},
        quantities_by_good_id={"some_service": 1},
        nonce="some_nonce",
        fee_by_currency_id={"FET": 0},
    )
    get_wealth_if_needed(terms.sender_address)

    signing_dialogues = cast(SigningDialogues, skill_context.signing_dialogues)
    stub_transaction = LedgerApis.get_transfer_transaction(
        terms.ledger_id,
        terms.sender_address,
        terms.counterparty_address,
        terms.sender_payable_amount,
        terms.sender_fee,
        terms.nonce,
    )
    signing_msg = SigningMessage(
        performative=SigningMessage.Performative.SIGN_TRANSACTION,
        dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
        raw_transaction=RawTransaction(FetchAICrypto.identifier, stub_transaction),
        terms=terms,
    )
    signing_dialogue = cast(
        Optional[SigningDialogue],
        signing_dialogues.create_with_message("decision_maker", signing_msg),
    )
    assert signing_dialogue is not None
    my_aea.context.decision_maker_message_queue.put_nowait(signing_msg)

    # Set the AEA running in a different thread
    try:
        logger.info("STARTING AEA NOW!")
        t = Thread(target=my_aea.start)
        t.start()

        # Let it run long enough to interact with the decision maker
        time.sleep(1)
    finally:
        # Shut down the AEA
        logger.info("STOPPING AEA NOW!")
        my_aea.stop()
        t.join()


class SigningDialogues(Model, BaseSigningDialogues):
    """Signing dialogues model."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
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
        )


class SigningHandler(Handler):
    """Implement the signing handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
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
        """
        Implement the handler teardown.

        :return: None
        """

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
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
        Handle a signing message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info("transaction signing was successful.")
        logger.info(signing_msg.signed_transaction)

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
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
        :return: None
        """
        self.context.logger.warning(
            "cannot handle signing message of performative={} in dialogue={}.".format(
                signing_msg.performative, signing_dialogue
            )
        )


if __name__ == "__main__":
    run()
