In this section, we show you how to integrate the AEA with the Fetch.ai and third-party ledgers.

## Ledger support

For a ledger to be considered _supported_ in the framework, three abstract base classes need to be implemented:

- the <a href="../api/crypto/base#aea.crypto.base.LedgerApi">`LedgerApi`</a> class wraps the API to talk to the ledger and its helper methods
- the <a href="../api/crypto/base#aea.crypto.base.Crypto">`Crypto`</a> class wraps the API to perform cryptographic operations for the relevant ledger
- the <a href="../api/crypto/base#aea.crypto.base.FaucetApi">`FaucetApi`</a> class wraps the API to talk to a faucet on a testnet

These three classes have their own registries, which allow the developer to import the relevant object where needed.

## Ledger plug-in architecture

The AEA framework provides a plug-in mechanism to support ledger functionalities in 
an easily extendible way. At import time, the framework will load
all the crypto plug-ins available in the current Python environment.

A _crypto plug-in_ is a Python package which declares some specific
<a href="https://setuptools.pypa.io/en/latest/pkg_resources.html#entry-points" target="_blank">
`setuptools` "entry points"</a> in its `setup.py` script.
In particular, there are three types of entry points the framework looks up:

- `aea.ledger_apis`, which points to instantiable classes implementing the `LedgerApi` interface;
- `aea.cryptos`, which points to instantiable classes implementing the `Crypto` interface;
- `aea.faucet_apis`, which points to instantiable classes implementing the `FaucetApi` interface.

This is an example of `setup.py` script for a ledger plug-in `aea-ledger-myledger`:

```python
# sample ./setup.py file
from setuptools import setup

setup(
    name="aea-ledger-myledger",
    packages=["aea_ledger_myledger"],
    # plugins must depend on 'aea'  
    install_requires=["aea"], # add other dependencies...
    # the following makes a plugin available to aea
    entry_points={
        "aea.cryptos": ["myledger = aea_ledger_myledger:MyLedgerCrypto"],
        "aea.ledger_apis": ["myledger = aea_ledger_myledger:MyLedgerApi"],
        "aea.faucet_apis": ["myledger = aea_ledger_myledger:MyLedgerFaucetApi"],
    },
    # PyPI classifier for AEA plugins
    classifiers=["Framework :: AEA"],
)
```

By convention, such plug-in packages should be named `aea-ledger-${LEDGER_ID}`,
and the importable package name `aea_ledger_${LEDGER_ID}`.
In the example above, the package name is `aea-ledger-myledger`,
and the importable package name is `aea_ledger_myledger`.

You can search for AEA ledger plug-ins on PyPI:
<a href="https://pypi.org/search/?q=aea-ledger" target="_blank">https://pypi.org/search/?q=aea-ledger</a>

## Maintained plug-ins

At the moment, the framework natively supports the following three ledgers:

- Fetch.ai: <a href="https://pypi.org/project/aea-ledger-fetchai/" target="_blank">PyPI package: `aea-ledger-fetchai`</a>, and <a href="https://github.com/fetchai/agents-aea/tree/main/plugins/aea-ledger-fetchai" target="_blank">source code</a>.
- Ethereum: <a href="https://pypi.org/project/aea-ledger-ethereum/" target="_blank">PyPI package: `aea-ledger-ethereum`</a>, and <a href="https://github.com/fetchai/agents-aea/tree/main/plugins/aea-ledger-ethereum" target="_blank">source code</a>.
- Cosmos: <a href="https://pypi.org/project/aea-ledger-cosmos/" target="_blank">PyPI package: `aea-ledger-cosmos`</a>, and <a href="https://github.com/fetchai/agents-aea/tree/main/plugins/aea-ledger-cosmos" target="_blank">source code</a>.

However, support for additional ledgers can be added to the framework at runtime.


## Examples

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

- Examples of how to interact with the ledger API registry:

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

- Examples of how to interact with the faucet API registry:

``` python
from aea.crypto.registries import faucet_apis_registry, make_faucet_api, register_faucet_api

# by default we can use the native faucet apis
CONFIG = dict(poll_interval=1.0)
fetchai_faucet_api = make_faucet_api("fetchai", **CONFIG)

# we can check what faucet apis are registered
faucet_apis_registry.supported_ids

# we can also add a new faucet api to the registry
register_faucet_api(id_="my_ledger_id", entry_point="some.dotted.path:MyLedgerFaucetApi")

# and then make it anywhere
my_faucet_api = make_faucet_api("my_ledger_id")
```

The framework wraps all `LedgerApi` classes and exposes them in the <a href="../api/crypto/ledger_apis#aea.crypto.base.LedgerApis">`LedgerApis`</a> classes. The framework also wraps the crypto APIs to create identities on both ledgers and exposes them in the `Wallet`.

The separation between the `Crypto` and `LedgerApi` is fundamental to the framework design. In particular, the object which holds the private key is separated from the object which interacts with the ledger. This design pattern is repeated throughout the framework: the decision maker is the only entity with access to the AEA's `Wallet` whilst `LedgerApis` are accessible by all skills.

## Stargate World - Fetch.ai testnet for agents

Stargate World is our stable, public testnet for the Fetch Ledger v2. As such, most developers will be interacting with this testnet. This is specifically designed and supported for AEA development.


| Parameter      | Value                                                                      |
| -------------- | -------------------------------------------------------------------------- |
| Chain ID       | stargateworld-3                                                            |
| Denomination   | atestfet                                                                   |
| Decimals       | 18                                                                         |
| Version        | v0.8.x                                                                     |
| RPC Endpoint   | https://rpc-stargateworld.fetch.ai:443                                     |
| REST Endpoint  | https://rest-stargateworld.fetch.ai:443                                    |
| Block Explorer | <a href="https://explore-stargateworld.fetch.ai" target="_blank">https://explore-stargateworld.fetch.ai</a> |
| Token Faucet   | Use block explorer                                                         |

You can access more details on <a href="https://github.com/fetchai/networks-stargateworld" target="_blank">GitHub</a>.

The configurations can be specified for the `fetchai/ledger:0.19.0` connection.

## CosmWasm supporting chains

The Fetch.ai networks use <a href="https://docs.cosmwasm.com" target="_blank">CosmWasm</a> for smart contract support.

