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
        if (
            tx_msg_response is not None
            and tx_msg_response.performative
            == TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT
        ):
            logger.info(
                "[{}]: transaction was successful.".format(self.context.agent_name)
            )
            logger.info(tx_msg_response.tx_digest)
        else:
            logger.info(
                "[{}]: transaction was not successful.".format(self.context.agent_name)
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


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

    identity = Identity(
        name="my_aea",
        address=wallet_1.addresses.get(FETCHAI),
        default_address_key=FETCHAI,
    )

    # create the AEA

    my_aea = AEA(identity, [stub_connection], wallet_1, ledger_apis, resources)
    ledger_api = ledger_apis.apis[FETCHAI]
    tx_nonce = ledger_api.generate_tx_nonce(wallet_2.addresses.get(FETCHAI),
                                            wallet_1.addresses.get(FETCHAI))

    tx_msg = TransactionMessage(
        performative=TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT,
        skill_callback_ids=[PublicId("fetchai", "internal", "0.1.0")],
        tx_id="transaction0",
        tx_sender_addr=wallet_1.addresses.get(FETCHAI),
        tx_counterparty_addr=wallet_2.addresses.get(FETCHAI),
        tx_amount_by_currency_id={'FET': 1},
        tx_sender_fee=1,
        tx_counterparty_fee=0,
        tx_quantities_by_good_id={},
        ledger_id=FETCHAI,
        info={"some_info_key": "some_info_value"},
        tx_nonce=tx_nonce,
        )
    my_aea.context.decision_maker_message_queue.put_nowait(tx_msg)

    logger.info("Wallet 1 : {}".format(wallet_1.addresses.get(FETCHAI)))
    logger.info("Wallet 2 : {}".format(wallet_2.addresses.get(FETCHAI)))
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


if __name__ == "__main__":
    run()
