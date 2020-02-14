import logging
import os
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import _create_fetchai_private_key
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.crypto.helpers import _try_generate_testnet_wealth

ROOT_DIR = os.getcwd()

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"

def run():
    # Create a private key
    _create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_1)
    _create_fetchai_private_key(private_key_file=FETCHAI_PRIVATE_KEY_FILE_2)

    # Set up the wallet, identity, oef connection, ledger and (empty) resources
    wallet_1 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_1})
    wallet_2 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})

    ledger_apis = LedgerApis({FETCHAI: {'network': 'testnet'}}, FETCHAI)
    _try_generate_testnet_wealth(FETCHAI, wallet_1.addresses[FETCHAI])

    logger.info("Sending amount to {}".format(wallet_2.addresses.get(FETCHAI)))
    tx_digest = ledger_apis.apis[FETCHAI].send_transaction(crypto=wallet_1.crypto_objects.get(FETCHAI),
                                                             destination_address=wallet_2.addresses.get(FETCHAI),
                                                             amount=1,
                                                             tx_fee=1,
                                                             tx_nonce=ledger_apis.apis.get(FETCHAI).generate_tx_nonce(wallet_2.addresses.get(FETCHAI),
                                                                                                                      wallet_1.addresses.get(FETCHAI)),
                                                             )
    logger.info("The transaction digest is {}".format(tx_digest))


if __name__ == "__main__":
    run()
