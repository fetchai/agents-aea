<a href="../api/contracts/base#contract-objects">`Contracts`</a> wrap smart contracts for third-party decentralized ledgers. In particular, they provide wrappers around the API or ABI of a smart contract. They expose an API to abstract implementation specifics of the ABI from the skills.

Contracts usually contain the logic to create contract transactions. Contracts can be added as packages.

## Developing your own

The easiest way to get started developing your own contract is by using the <a href="../scaffolding">scaffold</a> command:

``` bash
aea scaffold contract my_new_contract
```

This will scaffold a contract package called `my_new_contract` with three files:

* `__init__.py` 
* `contract.py`, containing the scaffolded contract class
* `contract.yaml` containing the scaffolded configuration file
