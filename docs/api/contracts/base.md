<a name="aea.contracts.base"></a>
# aea.contracts.base

The base contract.

<a name="aea.contracts.base.Contract"></a>
## Contract Objects

```python
class Contract(Component)
```

Abstract definition of a contract.

<a name="aea.contracts.base.Contract.__init__"></a>
#### `__`init`__`

```python
 | __init__(contract_config: ContractConfig, **kwargs: Any) -> None
```

Initialize the contract.

**Arguments**:

- `contract_config`: the contract configurations.
- `kwargs`: the keyword arguments.

<a name="aea.contracts.base.Contract.id"></a>
#### id

```python
 | @property
 | id() -> PublicId
```

Get the name.

<a name="aea.contracts.base.Contract.configuration"></a>
#### configuration

```python
 | @property
 | configuration() -> ContractConfig
```

Get the configuration.

<a name="aea.contracts.base.Contract.get_instance"></a>
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

<a name="aea.contracts.base.Contract.from_dir"></a>
#### from`_`dir

```python
 | @classmethod
 | from_dir(cls, directory: str, **kwargs: Any) -> "Contract"
```

Load the protocol from a directory.

**Arguments**:

- `directory`: the directory to the skill package.
- `kwargs`: the keyword arguments.

**Returns**:

the contract object.

<a name="aea.contracts.base.Contract.from_config"></a>
#### from`_`config

```python
 | @classmethod
 | from_config(cls, configuration: ContractConfig, **kwargs: Any) -> "Contract"
```

Load contract from configuration.

**Arguments**:

- `configuration`: the contract configuration.
- `kwargs`: the keyword arguments.

**Returns**:

the contract object.

<a name="aea.contracts.base.Contract.get_deploy_transaction"></a>
#### get`_`deploy`_`transaction

```python
 | @classmethod
 | get_deploy_transaction(cls, ledger_api: LedgerApi, deployer_address: str, **kwargs: Any) -> Optional[JSONLike]
```

Handler method for the 'GET_DEPLOY_TRANSACTION' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `deployer_address`: The address that will deploy the contract.
- `kwargs`: keyword arguments.

**Returns**:

the tx

<a name="aea.contracts.base.Contract.get_raw_transaction"></a>
#### get`_`raw`_`transaction

```python
 | @classmethod
 | get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any) -> Optional[JSONLike]
```

Handler method for the 'GET_RAW_TRANSACTION' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a name="aea.contracts.base.Contract.get_raw_message"></a>
#### get`_`raw`_`message

```python
 | @classmethod
 | get_raw_message(cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any) -> Optional[bytes]
```

Handler method for the 'GET_RAW_MESSAGE' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

<a name="aea.contracts.base.Contract.get_state"></a>
#### get`_`state

```python
 | @classmethod
 | get_state(cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any) -> Optional[JSONLike]
```

Handler method for the 'GET_STATE' requests.

Implement this method in the sub class if you want
to handle the contract requests manually.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `kwargs`: the keyword arguments.

**Returns**:

the tx  # noqa: DAR202

