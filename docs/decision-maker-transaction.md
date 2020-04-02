This guide can be considered as a part 2 of the <a href="/standalone-transaction/">the stand-alone transaction demo </a> we did in a previous guide. After the completion of the transaction,
we get the transaction digest. With this we can search for the transaction on the <a href='https://explore-testnet.fetch.ai'>block explorer</a>. The main difference is that now we are going to use the decision-maker to settle the transaction.

First, import the libraries and the set the constant values.

``` python
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
```

## Create a private key and an AEA

To have access to the decision-maker, which is responsible for signing transactions, we need to create an AEA. We can create a an AEA with the builder, providing it with a private key we generate first.

``` python
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
```

## Generate wealth

Since we want to send funds from our AEA's `wallet`, we need to generate some wealth for the `wallet`. We can do this with the following code where we use the default address

``` python
    # Generate some wealth for the default address
    _try_generate_testnet_wealth(FETCHAI, my_aea.identity.address)
```

## Add a simple skill

Add a simple skill with a transaction handler.

``` python
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
```

## Create a second identity
``` python
    _create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_2)

    counterparty_wallet = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})

    counterparty_identity = Identity(
        name="counterparty_aea",
        addresses=counterparty_wallet.addresses,
        default_address_key=FETCHAI,
    )
```

## Create the transaction message

Next, we are creating the transaction message and we send it to the decision-maker.
``` python
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
```

## Run the agent

Finally, we are running the agent and we expect the transaction digest to be printed in the terminal.
``` python
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
```

## More details

To be able to register a handler that reads the internal messages, we have to create a class at the end of the file with the name TransactionHandler
``` python
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
```

You can find the full code for this example below:

<details><summary>Transaction via decision-maker full code</summary>

``` python
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
```
</details>
