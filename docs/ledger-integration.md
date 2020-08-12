In this section, we show you how to integrate the AEA with the Fetch.ai and third-party ledgers.

The framework currently natively supports two ledgers:

- Fetch.ai
- Ethereum

However, support for additional ledgers can be added to the framework at runtime.

For a ledger to be considered `supported` in the framework, three abstract base classes need to be implemented:

- the <a href="../api/crypto/base#aea.crypto.base.LedgerApi">`LedgerApi`</a> class wraps the api to talk to the ledger and its helper methods
- the <a href="../api/crypto/base#aea.crypto.base.Crypto">`Crypto`</a> class wraps the api to perform cryptographic operations for the relevant ledger
- the <a href="../api/crypto/base#aea.crypto.base.FaucetApi">`FaucetApi`</a> class wraps the api to talk to a faucet on a testnet

These three classes have their own registries, which allow the developer to import the relevant object where needed:

- Examples of how to interact with the crypto registry:

``` python
from aea.crypto.registries import crypto_registry, make_crypto, register_crypto

# by default we can use the native cryptos
fetchai_crypto = make_crypto("fetchai")

# we can check what cryptos are registered
crypto_registry.supported_ids

# we can also add a new crypto to the registry
register_crypto(id_="my_ledger_id", entry_point="some.dotted.path:MyLedgerCrypto")

# and then make it anywhere
my_ledger_crypto = make_crypto("my_ledger_id")
```

- Examples of how to interact with the ledger api registry:

``` python
from aea.crypto.registries import ledger_apis_registry, make_ledger_api, register_ledger_api

# by default we can use the native ledger apis
CONFIG = {"network": "testnet"}
fetchai_ledger_api = make_ledger_api("fetchai", **CONFIG)

# we can check what ledger apis are registered
ledger_apis_registry.supported_ids

# we can also add a new ledger api to the registry
register_ledger_api(id_="my_ledger_id", entry_point="some.dotted.path:MyLedgerApi")

# and then make it anywhere
my_ledger_api = make_ledger_api("my_ledger_id")
```

- Examples of how to interact with the faucet api registry:

``` python
from aea.crypto.registries import faucet_apis_registry, make_faucet_api, register_faucet_api

# by default we can use the native faucet apis
CONFIG = {"network": "testnet"}
fetchai_faucet_api = make_faucet_api("fetchai", **CONFIG)

# we can check what faucet apis are registered
faucet_apis_registry.supported_ids

# we can also add a new faucet api to the registry
register_faucet_api(id_="my_ledger_id", entry_point="some.dotted.path:MyLedgerFaucetApi")

# and then make it anywhere
my_faucet_api = make_faucet_api("my_ledger_id")
```

The framework wraps all `LedgerApi` classes and exposes them in the <a href="../api/crypto/ledger_apis#aea.crypto.base.LedgerApis">`LedgerApis` classes. The framework also wraps the crypto APIs to create identities on both ledgers and exposes them in the `Wallet`.

The separation between the `Crypto` and `LedgerApi` is fundamental to the framework design. In particular, the object which holds the private key is separated from the object which interacts with the ledger. This design pattern is repeated throughout the framework: the decision maker is the only entity with access to the AEA's `Wallet` whilst `LedgerApis` are accessible by all skills.
