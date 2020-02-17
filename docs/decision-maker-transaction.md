This guide can be considered as a part 2 of the <a href="/standalone-transaction/">the stand-alone transaction demo </a> we did in a previous guide. After the completion of the transaction,
we get the transaction digest. With this we can search for the transaction on the <a href='https://explore-testnet.fetch.ai'>block explorer</a>. The main difference is that now we are going to use the decision-maker to settle the transaction.

## Create the private keys

Firstly, we will create the private key files.

```python
from aea.crypto.helpers import _create_fetchai_private_key

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"
# Create a private keys
_create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_1)
_create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_2)
```

## Create the wallets

Once we created the private keys we need to generate the wallets.

```python

from aea.crypto.fetchai import FETCHAI
from aea.crypto.wallet import Wallet

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"

# Set up the wallets
wallet_1 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_1})
wallet_2 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})
```

## Create LedgerApis

We need to create the LedgerApis object to be able to interact with the Fetch.ai `testnet`
```python
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.fetchai import FETCHAI

# Set up the LedgerApis
ledger_apis = LedgerApis({FETCHAI: {'network': 'testnet'}}, FETCHAI)
```

## Generate wealth

Since we want to send funds from `wallet_1` to `wallet_2`, we need to generate some wealth for the `wallet_1`. We can
do this with the following code
```python
from aea.crypto.helpers import _try_generate_testnet_wealth
from aea.crypto.fetchai import FETCHAI

# Generate some wealth
_try_generate_testnet_wealth(FETCHAI, wallet_1.addresses[FETCHAI])
```

## Create the aea

To have access to the decision-maker, we need to create an AEA. An AEA constructor needs some variables to be passed `AEA(Identity, Connection, Wallet, LedgerApis, Resources)`
So let's create these dependencies before we instantiate the AEA.

```python
from aea.identity.base import Identity

from aea.aea import AEA
from aea.configurations.base import PublicId
from aea.connections.stub.connection import StubConnection
from aea.crypto.fetchai import FETCHAI

from aea.registries.base import Resources

ROOT_DIR = "./"
INPUT_FILE = "input.txt"
OUTPUT_FILE = "output.txt"

 tx_handler = TransactionHandler(skill_context='skill_context', name="fake_skill")
 resources = Resources()
 resources.handler_registry.register(
    (PublicId.from_str("fetchai/fake_skill:0.1.0"), PublicId.from_str("fetchai/internal:0.1.0")), tx_handler)

 stub_connection = StubConnection(
    input_file_path=INPUT_FILE, output_file_path=OUTPUT_FILE
 )

 identity_1 = Identity(
    name="my_aea",
    address=wallet_1.addresses.get(FETCHAI),
    default_address_key=FETCHAI,
 )

 my_aea = AEA(identity_1, [stub_connection], wallet_1, ledger_apis, resources)
```

## Create an identity for counterparty
We need to create an identity for the counterparty since the only one who must have access to the wallet is the decision-maker.
```python
identity_2 = Identity(
                name="my_aea_2",
                address=wallet_2.addresses.get(FETCHAI),
                default_address_key=FETCHAI,
            )
```

## Create the transaction message

Next, we are creating the transaction message and we send it to the decision-maker.
```python
from aea.configurations.base import PublicId
from aea.crypto.fetchai import FETCHAI
from aea.decision_maker.messages.transaction import TransactionMessage

  tx_msg = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("fetchai", "fake_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr=identity_1.addresses.get(FETCHAI),
        tx_counterparty_addr=identity_2.addresses.get(FETCHAI),
        tx_amount_by_currency_id={'FET': -1},
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
```python
import logging
import time

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

# Set the AEA running in a different thread
logger.info("STARTING AEA NOW!")
t = Thread(target=my_aea.start)
t.start()

# Let it run long enough to interact with the weather station
time.sleep(25)

# Shut down the AEA
logger.info("STOPPING AEA NOW!")
my_aea.stop()
t.join()

```

## More details

To be able to register a handler that reads the internal messages, we have to create a class at the end of the file with the name TransactionHandler
```python
import logging
from typing import cast

from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message

from aea.skills.base import Handler


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

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
            logger.info(
                "Transaction was successful."
            )
            logger.info(tx_msg_response.tx_digest)
        else:
            logger.info(
                "Transaction was not successful."
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
```

<details><summary>Transaction via decision-maker full code</summary>

```
import logging
import time
from threading import Thread
from typing import Optional, cast, Dict, Any

from aea.identity.base import Identity
from aea.aea import AEA
from aea.configurations.base import PublicId, ProtocolId
from aea.connections.stub.connection import StubConnection
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import _create_fetchai_private_key, _try_generate_testnet_wealth
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message

from aea.registries.base import Resources
from aea.skills.base import Handler

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"

ROOT_DIR = "./"
INPUT_FILE = "input.txt"
OUTPUT_FILE = "output.txt"


def run():
    # Create a private keys
    _create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_1)
    _create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_2)

    # Set up the wallets
    wallet_1 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_1})
    wallet_2 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})

    # Generate some wealth
    _try_generate_testnet_wealth(FETCHAI, wallet_1.addresses[FETCHAI])

    # Set up the LedgerApis
    ledger_apis = LedgerApis({FETCHAI: {'network': 'testnet'}}, FETCHAI)

    tx_handler = TransactionHandler(skill_context='skill_context', name="fake_skill")
    resources = Resources()
    resources.handler_registry.register(
        (PublicId.from_str("fetchai/fake_skill:0.1.0"), PublicId.from_str("fetchai/internal:0.1.0")), tx_handler)

    stub_connection = StubConnection(
        input_file_path=INPUT_FILE, output_file_path=OUTPUT_FILE
    )

    identity_1 = Identity(
        name="my_aea",
        address=wallet_1.addresses.get(FETCHAI),
        default_address_key=FETCHAI,
    )

    identity_2 = Identity(
        name="my_aea_2",
        address=wallet_2.addresses.get(FETCHAI),
        default_address_key=FETCHAI,
    )

    # create the AEA

    my_aea = AEA(identity_1, [stub_connection], wallet_1, ledger_apis, resources)
    ledger_api = ledger_apis.apis[FETCHAI]
    tx_nonce = ledger_api.generate_tx_nonce(identity_1.addresses.get(FETCHAI),
                                            identity_2.addresses.get(FETCHAI))

    tx_msg = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("fetchai", "fake_skill", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr=identity_1.addresses.get(FETCHAI),
        tx_counterparty_addr=identity_2.addresses.get(FETCHAI),
        tx_amount_by_currency_id={'FET': -1},
        tx_sender_fee=1,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={},
        ledger_id=FETCHAI,
        info={"some_info_key": "some_info_value"},
        tx_nonce=tx_nonce,
        )
    my_aea.context.decision_maker_message_queue.put_nowait(tx_msg)

    # Set the AEA running in a different thread
    logger.info("STARTING AEA NOW!")
    t = Thread(target=my_aea.start)
    t.start()

    # Let it run long enough to interact with the weather station
    time.sleep(5)

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
            logger.info(
                "Transaction was successful."
            )
            logger.info(tx_msg_response.tx_digest)
        else:
            logger.info(
                "Transaction was not successful."
            )

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
