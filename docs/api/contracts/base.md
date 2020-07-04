<a name=".aea.contracts.base"></a>
# aea.contracts.base

The base contract.

<a name=".aea.contracts.base.Contract"></a>
## Contract Objects

```python
class Contract(Component,  ABC)
```

Abstract definition of a contract.

<a name=".aea.contracts.base.Contract.__init__"></a>
#### `__`init`__`

```python
 | __init__(contract_config: ContractConfig)
```

Initialize the contract.

**Arguments**:

- `contract_config`: the contract configurations.

<a name=".aea.contracts.base.Contract.id"></a>
#### id

```python
 | @property
 | id() -> ContractId
```

Get the name.

<a name=".aea.contracts.base.Contract.configuration"></a>
#### configuration

```python
 | @property
 | configuration() -> ContractConfig
```

Get the configuration.

<a name=".aea.contracts.base.Contract.get_instance"></a>
#### get`_`instance

```python
 | @classmethod
 | @abstractmethod
 | get_instance(cls, ledger_api: LedgerApi, contract_address: Optional[str] = None) -> Any
```

Get the instance.

**Arguments**:

- `ledger_api`: the ledger api we are using.
- `contract_address`: the contract address.

**Returns**:

the contract instance

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

Load contract from configuration.

**Arguments**:

- `configuration`: the contract configuration.

**Returns**:

the contract object.

