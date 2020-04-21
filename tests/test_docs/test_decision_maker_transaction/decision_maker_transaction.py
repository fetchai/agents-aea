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

from aea.aea_builder import AEABuilder
from aea.configurations.base import ProtocolId, SkillConfig
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import _create_fetchai_private_key, _try_generate_testnet_wealth
from aea.crypto.wallet import Wallet
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.identity.base import Identity
from aea.protocols.base import Message
from aea.skills.base import Handler, Skill, SkillContext

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"


def run():
    # Create a private key
    _create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_1)

    # Instantiate the builder and build the AEA
    # By default, the default protocol, error skill and stub connection are added
    builder = AEABuilder()

    builder.set_name("my_aea")

    builder.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE_1)

    builder.add_ledger_api_config(FETCHAI, {"network": "testnet"})

    # Create our AEA
    my_aea = builder.build()

    # Generate some wealth for the default address
    _try_generate_testnet_wealth(FETCHAI, my_aea.identity.address)

    # add a simple skill with handler
    skill_context = SkillContext(my_aea.context)
    skill_config = SkillConfig(name="simple_skill", author="fetchai", version="0.1.0")
    tx_handler = TransactionHandler(
        skill_context=skill_context, name="transaction_handler"
    )
    simple_skill = Skill(
        skill_config, skill_context, handlers={tx_handler.name: tx_handler}
    )
    my_aea.resources.add_skill(simple_skill)

    # create a second identity
    _create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_2)

    counterparty_wallet = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})

    counterparty_identity = Identity(
        name="counterparty_aea",
        addresses=counterparty_wallet.addresses,
        default_address_key=FETCHAI,
    )

    # create tx message for decision maker to process
    fetchai_ledger_api = my_aea.context.ledger_apis.apis[FETCHAI]
    tx_nonce = fetchai_ledger_api.generate_tx_nonce(
        my_aea.identity.address, counterparty_identity.address
    )

    tx_msg = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[skill_config.public_id],
        tx_id="transaction0",
        tx_sender_addr=my_aea.identity.address,
        tx_counterparty_addr=counterparty_identity.address,
        tx_amount_by_currency_id={"FET": -1},
        tx_sender_fee=1,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={},
        ledger_id=FETCHAI,
        info={"some_info_key": "some_info_value"},
        tx_nonce=tx_nonce,
    )
    my_aea.context.decision_maker_message_queue.put_nowait(tx_msg)

    # Set the AEA running in a different thread
    try:
        logger.info("STARTING AEA NOW!")
        t = Thread(target=my_aea.start)
        t.start()

        # Let it run long enough to interact with the weather station
        time.sleep(20)
    finally:
        # Shut down the AEA
        logger.info("STOPPING AEA NOW!")
        my_aea.stop()
        t.join()


class TransactionHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        tx_msg_response = cast(TransactionMessage, message)
        logger.info(tx_msg_response)
        if (
            tx_msg_response is not None
            and tx_msg_response.performative
            == TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT
        ):
            logger.info("Transaction was successful.")
            logger.info(tx_msg_response.tx_digest)
        else:
            logger.info("Transaction was not successful.")

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


if __name__ == "__main__":
    run()
