<a name=".aea.contracts.ethereum"></a>
## aea.contracts.ethereum

The base ethereum contract.

<a name=".aea.contracts.ethereum.Contract"></a>
### Contract

```python
class Contract(BaseContract)
```

Definition of an ethereum contract.

<a name=".aea.contracts.ethereum.Contract.load"></a>
#### load

```python
 | load() -> None
```

Load the contract.

<a name=".aea.contracts.ethereum.Contract.set_instance"></a>
#### set`_`instance

```python
 | set_instance(ledger_api: EthereumApi) -> None
```

Set the instance.

**Arguments**:

- `ledger_api`: the ethereum ledger api

<a name=".aea.contracts.ethereum.Contract.set_address"></a>
#### set`_`address

```python
 | set_address(ledger_api: EthereumApi, contract_address: str) -> None
```

Set the contract address.

**Arguments**:

- `ledger_api`: the ledger_api we are using.
- `contract_address`: the contract address

<a name=".aea.contracts.ethereum.Contract.set_deployed_instance"></a>
#### set`_`deployed`_`instance

```python
 | set_deployed_instance(ledger_api: EthereumApi, contract_address: str) -> None
```

Set the contract address.

**Arguments**:

- `ledger_api`: the ledger_api we are using.
- `contract_address`: the contract address

