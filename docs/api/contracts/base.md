<a name=".aea.contracts.base"></a>
## aea.contracts.base

The base contract.

<a name=".aea.contracts.base.Contract"></a>
### Contract

```python
class Contract(Component)
```

Abstract definition of a contract.

<a name=".aea.contracts.base.Contract.__init__"></a>
#### `__`init`__`

```python
 | __init__(config: ContractConfig)
```

Initialize the contract.

**Arguments**:

- `config`: the contract configurations.

<a name=".aea.contracts.base.Contract.id"></a>
#### id

```python
 | @property
 | id() -> ContractId
```

Get the name.

<a name=".aea.contracts.base.Contract.config"></a>
#### config

```python
 | @property
 | config() -> ContractConfig
```

Get the configuration.

<a name=".aea.contracts.base.Contract.contract_interface"></a>
#### contract`_`interface

```python
 | @property
 | contract_interface() -> Dict[str, Any]
```

Get the contract interface.

<a name=".aea.contracts.base.Contract.load"></a>
#### load

```python
 | load() -> None
```

Load the contract.

- load the contract interface, specified in the contract.yaml
  'path_to_contract_interface' field.

