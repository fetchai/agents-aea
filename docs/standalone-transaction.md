In this guide, we will generate some wealth for the Fetch.ai testnet and create a standalone transaction. After the completion of the transaction, we get the transaction digest. With this we can search for the transaction on the <a href='https://explore-testnet.fetch.ai'>block explorer</a>

First, import the python and application specific libraries and set the static variables.

``` python
import logging

from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import create_private_key, try_generate_testnet_wealth
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"
```

## Create the private keys

``` python
    # Create a private keys
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_1
    )
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_2
    )
```

## Create the wallets

Once we created the private keys we need to generate the wallets.

``` python
    # Set up the wallets
    wallet_1 = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_1})
    wallet_2 = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_2})
```

## Create LedgerApis

We need to create the LedgerApis object in order to be able to interact with the Fetch.ai `testnet`
``` python
    # Set up the LedgerApis
    ledger_apis = LedgerApis(
        {FetchAICrypto.identifier: {"network": "testnet"}}, FetchAICrypto.identifier
    )
```

## Generate wealth

Since we want to send funds from `wallet_1` to `wallet_2`, we need to generate some wealth for the `wallet_1`. We can
do this with the following code
``` python
    # Generate some wealth
    try_generate_testnet_wealth(
        FetchAICrypto.identifier, wallet_1.addresses[FetchAICrypto.identifier]
    )
```

## Send transaction

Finally, we create a transaction that sends the funds to the `wallet_2`

``` python
    # Create the transaction and send it to the ledger.
    ledger_api = ledger_apis.apis[FetchAICrypto.identifier]
    tx_nonce = ledger_api.generate_tx_nonce(
        wallet_2.addresses.get(FetchAICrypto.identifier),
        wallet_1.addresses.get(FetchAICrypto.identifier),
    )
    tx_digest = ledger_api.transfer(
        crypto=wallet_1.crypto_objects.get(FetchAICrypto.identifier),
        destination_address=wallet_2.addresses.get(FetchAICrypto.identifier),
        amount=1,
        tx_fee=1,
        tx_nonce=tx_nonce,
    )
    logger.info("Transaction complete.")
    logger.info("The transaction digest is {}".format(tx_digest))
```

<details><summary>Stand-alone transaction full code</summary>

``` python
import logging

from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import create_private_key, try_generate_testnet_wealth
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"


def run():
    # Create a private keys
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_1
    )
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_2
    )

    # Set up the wallets
    wallet_1 = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_1})
    wallet_2 = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_2})

    # Set up the LedgerApis
    ledger_apis = LedgerApis(
        {FetchAICrypto.identifier: {"network": "testnet"}}, FetchAICrypto.identifier
    )

    # Generate some wealth
    try_generate_testnet_wealth(
        FetchAICrypto.identifier, wallet_1.addresses[FetchAICrypto.identifier]
    )

    logger.info(
        "Sending amount to {}".format(wallet_2.addresses.get(FetchAICrypto.identifier))
    )

    # Create the transaction and send it to the ledger.
    ledger_api = ledger_apis.apis[FetchAICrypto.identifier]
    tx_nonce = ledger_api.generate_tx_nonce(
        wallet_2.addresses.get(FetchAICrypto.identifier),
        wallet_1.addresses.get(FetchAICrypto.identifier),
    )
    tx_digest = ledger_api.transfer(
        crypto=wallet_1.crypto_objects.get(FetchAICrypto.identifier),
        destination_address=wallet_2.addresses.get(FetchAICrypto.identifier),
        amount=1,
        tx_fee=1,
        tx_nonce=tx_nonce,
    )
    logger.info("Transaction complete.")
    logger.info("The transaction digest is {}".format(tx_digest))


if __name__ == "__main__":
    run()
```
</details>
