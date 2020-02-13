In this guide, we will generate some wealth for the `Fetch.ai testnet` and create a standalone transaction. After the completion of the transaction,
we get the transaction digest. With this we can search the transaction it in the <a href='https://explore-testnet.fetch.ai'>block explorer</a>

## Create the wallets

We will need to create two different addresses for this demo. To do this we instantiate two different wallets 

```python
    wallet_1 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE})
    wallet_2 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})
```

Since we want to send funds from `wallet_1` to `wallet_2`, we need to generate some wealth for the `wallet_1`. We can
do this with the following code
```python
    _try_generate_testnet_wealth('fetchai', wallet_1.addresses['fetchai'])
```

Finally, we create a transaction that sends the funds to the `wallet_2`

```python
  ledger_apis.apis['fetchai'].send_transaction(crypto=wallet_1.crypto_objects.get(FETCHAI),
                                                 destination_address=wallet_2.addresses.get(FETCHAI),
                                                 amount=1,
                                                 tx_fee=1,
                                                 tx_nonce="this_is_a_transaction_nonce",
                                                 )
```

<details><summary>Stand-alone transaction full code</summary>

```
import logging
import os
from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import FETCHAI_PRIVATE_KEY_FILE, _create_fetchai_private_key
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.crypto.helpers import _try_generate_testnet_wealth

ROOT_DIR = os.getcwd()

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"

def run():
    # Create a private key
    _create_fetchai_private_key()

    # Set up the wallet, identity, oef connection, ledger and (empty) resources
    wallet_1 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE})
    wallet_2 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})
    ledger_apis = LedgerApis({'fetchai': {'network': 'testnet'}}, 'fetchai')
    _try_generate_testnet_wealth('fetchai', wallet_1.addresses['fetchai'])

    logger.info("Sending amount to {}".format(wallet_2.addresses.get(FETCHAI)))
    ledger_apis.apis['fetchai'].send_transaction(crypto=wallet_1.crypto_objects.get(FETCHAI),
                                                 destination_address=wallet_2.addresses.get(FETCHAI),
                                                 amount=1,
                                                 tx_fee=1,
                                                 tx_nonce="this_is_a_transaction_nonce",
                                                 )

if __name__ == "__main__":
    run()
```
</details>
