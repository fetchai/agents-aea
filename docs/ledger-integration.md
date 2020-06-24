In this section, we show you how to integrate the AEA with the Fetch.ai and third-party ledgers.

The framework currently natively supports two ledgers:

- Fetch.ai
- Ethereum

To this end, the framework wraps APIs to interact with the two ledgers and exposes them in the `LedgerApis` class. The framework also wraps the account APIs to create identities on both ledgers and exposes them in the `Wallet`.

The `Wallet` holds instantiation of the abstract `Crypto` base class, in particular `FetchaiCrypto` and `EthereumCrypto`.

The `LedgerApis` holds instantiation of the abstract `LedgerApi` base class, in particular `FetchaiLedgerApi` and `EthereumLedgerApi`.
You can think the concrete implementations of the base class `LedgerApi` as wrappers of the blockchain specific python SDK. 

