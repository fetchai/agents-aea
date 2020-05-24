<a name=".aea.contracts.ethereum"></a>
## aea.contracts.ethereum

The base ethereum contract.

<a name=".aea.contracts.ethereum.Contract"></a>
### Contract

```python
class Contract(BaseContract)
```

Definition of an ethereum contract.

<a name=".aea.contracts.ethereum.Contract.__init__"></a>
#### `__`init`__`

```python
 | __init__(config: ContractConfig, contract_interface: Dict[str, Any])
```

Initialize the contract.

**Arguments**:

- `config`: the contract configurations.
- `contract_interface`: the contract interface.

<a name=".aea.contracts.ethereum.Contract.set_instance"></a>
#### set`_`instance

```python
 | set_instance(ledger_api: LedgerApi) -> None
```

Set the instance.

**Arguments**:

- `ledger_api`: the ledger api we are using.

**Returns**:

None

<a name=".aea.contracts.ethereum.Contract.set_address"></a>
#### set`_`address

```python
 | set_address(ledger_api: LedgerApi, contract_address: str) -> None
```

Set the contract address.

**Arguments**:

- `ledger_api`: the ledger_api we are using.
- `contract_address`: the contract address

**Returns**:

None

<a name=".aea.contracts.ethereum.Contract.set_deployed_instance"></a>
#### set`_`deployed`_`instance

```python
 | set_deployed_instance(ledger_api: LedgerApi, contract_address: str) -> None
```

Set the contract address.

**Arguments**:

- `ledger_api`: the ledger_api we are using.
- `contract_address`: the contract address

**Returns**:

None

