<a id="aea.contracts.base"></a>

# aea.contracts.base

The base contract.

<a id="aea.contracts.base.snake_to_camel"></a>

#### snake`_`to`_`camel

```python
def snake_to_camel(string: str) -> str
```

Convert snake_case to camelCase

<a id="aea.contracts.base.Contract"></a>

## Contract Objects

```python
class Contract(Component)
```

Abstract definition of a contract.

<a id="aea.contracts.base.Contract.contract_id"></a>

#### contract`_`id

type: PublicId

<a id="aea.contracts.base.Contract.__init__"></a>

#### `__`init`__`

```python
def __init__(contract_config: ContractConfig, **kwargs: Any) -> None
```

Initialize the contract.

**Arguments**:

- `contract_config`: the contract configurations.
- `kwargs`: the keyword arguments.

<a id="aea.contracts.base.Contract.id"></a>

#### id

```python
@property
def id() -> PublicId
```

Get the name.

<a id="aea.contracts.base.Contract.configuration"></a>

#### configuration

```python
@property
def configuration() -> ContractConfig
```

Get the configuration.

<a id="aea.contracts.base.Contract.get_instance"></a>

#### get`_`instance

```python
@classmethod
def get_instance(cls,
                 ledger_api: LedgerApi,
                 contract_address: Optional[str] = None) -> Any
```

Get the instance.

**Arguments**:

- `ledger_api`: the ledger api we are using.
- `contract_address`: the contract address.

**Returns**:

the contract instance

<a id="aea.contracts.base.Contract.from_dir"></a>

#### from`_`dir

```python
@classmethod
def from_dir(cls, directory: str, **kwargs: Any) -> "Contract"
```

Load the protocol from a directory.

**Arguments**:

- `directory`: the directory to the skill package.
- `kwargs`: the keyword arguments.

**Returns**:

the contract object.

<a id="aea.contracts.base.Contract.from_config"></a>

#### from`_`config

```python
@classmethod
def from_config(cls, configuration: ContractConfig,
                **kwargs: Any) -> "Contract"
```

Load contract from configuration.

**Arguments**:

- `configuration`: the contract configuration.
- `kwargs`: the keyword arguments.

**Returns**:

the contract object.

<a id="aea.contracts.base.Contract.get_deploy_transaction"></a>

#### get`_`deploy`_`transaction

```python
@classmethod
def get_deploy_transaction(cls, ledger_api: LedgerApi, deployer_address: str,
                           **kwargs: Any) -> Optional[JSONLike]
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

<a id="aea.contracts.base.Contract.get_raw_transaction"></a>

#### get`_`raw`_`transaction

```python
@classmethod
def get_raw_transaction(cls, ledger_api: LedgerApi, contract_address: str,
                        **kwargs: Any) -> Optional[JSONLike]
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

<a id="aea.contracts.base.Contract.get_raw_message"></a>

#### get`_`raw`_`message

```python
@classmethod
def get_raw_message(cls, ledger_api: LedgerApi, contract_address: str,
                    **kwargs: Any) -> Optional[bytes]
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

<a id="aea.contracts.base.Contract.get_state"></a>

#### get`_`state

```python
@classmethod
def get_state(cls, ledger_api: LedgerApi, contract_address: str,
              **kwargs: Any) -> Optional[JSONLike]
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

<a id="aea.contracts.base.Contract.contract_method_call"></a>

#### contract`_`method`_`call

```python
@classmethod
def contract_method_call(cls, ledger_api: LedgerApi, method_name: str,
                         **kwargs: Any) -> Optional[JSONLike]
```

Make a contract call.

**Arguments**:

- `ledger_api`: the ledger apis.
- `method_name`: the contract method name.
- `kwargs`: keyword arguments.

**Returns**:

the call result

<a id="aea.contracts.base.Contract.build_transaction"></a>

#### build`_`transaction

```python
@classmethod
def build_transaction(cls, ledger_api: LedgerApi, method_name: str,
                      method_args: Optional[Dict],
                      tx_args: Optional[Dict]) -> Optional[JSONLike]
```

Build a transaction.

**Arguments**:

- `ledger_api`: the ledger apis.
- `method_name`: method name.
- `method_args`: method arguments.
- `tx_args`: transaction arguments.

**Returns**:

the transaction

<a id="aea.contracts.base.Contract.default_method_call"></a>

#### default`_`method`_`call

```python
@classmethod
def default_method_call(cls, ledger_api: LedgerApi, contract_address: str,
                        method_name: str, **kwargs: Any) -> Optional[JSONLike]
```

Make a contract call.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `method_name`: the method to call.
- `kwargs`: keyword arguments.

**Returns**:

the call result

<a id="aea.contracts.base.Contract.get_transaction_transfer_logs"></a>

#### get`_`transaction`_`transfer`_`logs

```python
@classmethod
def get_transaction_transfer_logs(
        cls,
        ledger_api: LedgerApi,
        tx_hash: str,
        target_address: Optional[str] = None) -> Optional[JSONLike]
```

Retrieve the logs from a transaction.

**Arguments**:

- `ledger_api`: the ledger apis.
- `tx_hash`: The transaction hash to check logs from.
- `target_address`: optional address to filter tranfer events to just those that affect it

**Returns**:

the tx logs

<a id="aea.contracts.base.Contract.get_method_data"></a>

#### get`_`method`_`data

```python
@classmethod
def get_method_data(cls, ledger_api: LedgerApi, contract_address: str,
                    method_name: str, **kwargs: Any) -> Optional[JSONLike]
```

Get a contract call encoded data.

**Arguments**:

- `ledger_api`: the ledger apis.
- `contract_address`: the contract address.
- `method_name`: the contract method name
- `kwargs`: the contract method args

**Returns**:

the tx  # noqa: DAR202

