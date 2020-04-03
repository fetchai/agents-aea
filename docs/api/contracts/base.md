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
 | __init__(config: ContractConfig, contract_interface: Dict[str, Any])
```

Initialize the contract.

**Arguments**:

- `config`: the contract configurations.
- `contract_interface`: the contract interface

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

<a name=".aea.contracts.base.Contract.from_dir"></a>
#### from`_`dir

```python
 | @classmethod
 | from_dir(cls, directory: str) -> "Contract"
```

Load the protocol from a directory.

**Arguments**:

- `directory`: the directory to the skill package.

**Returns**:

the contract object.

<a name=".aea.contracts.base.Contract.from_config"></a>
#### from`_`config

```python
 | @classmethod
 | from_config(cls, configuration: ContractConfig) -> "Contract"
```

Load contract from configuration

**Arguments**:

- `configuration`: the contract configuration.

**Returns**:

the contract object.

