<a name=".aea.contracts.ethereum"></a>
# aea.contracts.ethereum

The base ethereum contract.

<a name=".aea.contracts.ethereum.Contract"></a>
## Contract Objects

```python
class Contract(BaseContract)
```

Definition of an ethereum contract.

<a name=".aea.contracts.ethereum.Contract.get_instance"></a>
#### get`_`instance

```python
 | @classmethod
 | get_instance(cls, ledger_api: LedgerApi, contract_address: Optional[str] = None) -> Any
```

Get the instance.

**Arguments**:

- `ledger_api`: the ledger api we are using.
- `contract_address`: the contract address.

**Returns**:

the contract instance

