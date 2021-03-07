<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos"></a>
# plugins.aea-ledger-fetchai.aea`_`ledger`_`fetchai.`_`cosmos

Cosmos module wrapping the public and private key cryptography and ledger api.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper"></a>
## CosmosHelper Objects

```python
class CosmosHelper(Helper)
```

Helper class usable as Mixin for CosmosApi or as standalone class.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | @staticmethod
 | is_transaction_settled(tx_receipt: JSONLike) -> bool
```

Check whether a transaction is settled or not.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

True if the transaction has been settled, False o/w.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_code_id"></a>
#### get`_`code`_`id

```python
 | @staticmethod
 | get_code_id(tx_receipt: JSONLike) -> Optional[int]
```

Retrieve the `code_id` from a transaction receipt.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

the code id, if present

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_contract_address"></a>
#### get`_`contract`_`address

```python
 | @staticmethod
 | get_contract_address(tx_receipt: JSONLike) -> Optional[str]
```

Retrieve the `contract_address` from a transaction receipt.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

the contract address, if present

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.is_transaction_valid"></a>
#### is`_`transaction`_`valid

```python
 | @staticmethod
 | is_transaction_valid(tx: JSONLike, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Check whether a transaction is valid or not.

**Arguments**:

- `tx`: the transaction.
- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.

**Returns**:

True if the random_message is equals to tx['input']

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | @staticmethod
 | generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a unique hash to distinguish txs with the same terms.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_address_from_public_key"></a>
#### get`_`address`_`from`_`public`_`key

```python
 | @classmethod
 | get_address_from_public_key(cls, public_key: str) -> str
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.recover_message"></a>
#### recover`_`message

```python
 | @classmethod
 | recover_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered addresses

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.recover_public_keys_from_message"></a>
#### recover`_`public`_`keys`_`from`_`message

```python
 | @classmethod
 | recover_public_keys_from_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[str, ...]
```

Get the public key used to produce the `signature` of the `message`

**Arguments**:

- `message`: raw bytes used to produce signature
- `signature`: signature of the message
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered public keys

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_hash"></a>
#### get`_`hash

```python
 | @staticmethod
 | get_hash(message: bytes) -> str
```

Get the hash of a message.

**Arguments**:

- `message`: the message to be hashed.

**Returns**:

the hash of the message.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.is_valid_address"></a>
#### is`_`valid`_`address

```python
 | @classmethod
 | is_valid_address(cls, address: Address) -> bool
```

Check if the address is valid.

**Arguments**:

- `address`: the address to validate

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.load_contract_interface"></a>
#### load`_`contract`_`interface

```python
 | @classmethod
 | load_contract_interface(cls, file_path: Path) -> Dict[str, str]
```

Load contract interface.

**Arguments**:

- `file_path`: the file path to the interface

**Returns**:

the interface

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto"></a>
## CosmosCrypto Objects

```python
class CosmosCrypto(Crypto[SigningKey])
```

Class wrapping the Account Generation from Ethereum ledger.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.__init__"></a>
#### `__`init`__`

```python
 | __init__(private_key_path: Optional[str] = None) -> None
```

Instantiate an ethereum crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.private_key"></a>
#### private`_`key

```python
 | @property
 | private_key() -> str
```

Return a private key.

**Returns**:

a private key string

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.address"></a>
#### address

```python
 | @property
 | address() -> str
```

Return the address for the key pair.

**Returns**:

a display_address str

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.load_private_key_from_path"></a>
#### load`_`private`_`key`_`from`_`path

```python
 | @classmethod
 | load_private_key_from_path(cls, file_name: str) -> SigningKey
```

Load a private key in hex format from a file.

**Arguments**:

- `file_name`: the path to the hex file.

**Returns**:

the Entity.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.sign_message"></a>
#### sign`_`message

```python
 | sign_message(message: bytes, is_deprecated_mode: bool = False) -> str
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message to be signed
- `is_deprecated_mode`: if the deprecated signing is used

**Returns**:

signature of the message in string form

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.sign_transaction"></a>
#### sign`_`transaction

```python
 | sign_transaction(transaction: JSONLike) -> JSONLike
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed

**Returns**:

signed transaction

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.generate_private_key"></a>
#### generate`_`private`_`key

```python
 | @classmethod
 | generate_private_key(cls) -> SigningKey
```

Generate a key pair for cosmos network.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.dump"></a>
#### dump

```python
 | dump(fp: BinaryIO) -> None
```

Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

**Arguments**:

- `fp`: the output file pointer. Must be set in binary mode (mode='wb')

**Returns**:

None

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi"></a>
## `_`CosmosApi Objects

```python
class _CosmosApi(LedgerApi)
```

Class to interact with the Cosmos SDK via a HTTP APIs.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs: Any) -> None
```

Initialize the Cosmos ledger APIs.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.api"></a>
#### api

```python
 | @property
 | api() -> Any
```

Get the underlying API object.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_balance"></a>
#### get`_`balance

```python
 | get_balance(address: Address) -> Optional[int]
```

Get the balance of a given account.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_state"></a>
#### get`_`state

```python
 | get_state(callable_name: str, *args: Any, **kwargs: Any) -> Optional[JSONLike]
```

Call a specified function on the ledger API.

Based on the cosmos REST
API specification, which takes a path (strings separated by '/'). The
convention here is to define the root of the path (txs, blocks, etc.)
as the callable_name and the rest of the path as args.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_deploy_transaction"></a>
#### get`_`deploy`_`transaction

```python
 | get_deploy_transaction(contract_interface: Dict[str, str], deployer_address: Address, **kwargs: Any, ,) -> Optional[JSONLike]
```

Get the transaction to deploy the smart contract.

Dispatches to _get_storage_transaction and _get_init_transaction based on kwargs.

**Arguments**:

- `contract_interface`: the contract interface.
- `deployer_address`: The address that will deploy the contract.
:returns tx: the transaction dictionary.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_handle_transaction"></a>
#### get`_`handle`_`transaction

```python
 | get_handle_transaction(sender_address: Address, contract_address: Address, handle_msg: Any, amount: int, tx_fee: int, denom: Optional[str] = None, gas: int = 0, memo: str = "", chain_id: Optional[str] = None) -> Optional[JSONLike]
```

Create a CosmWasm HandleMsg transaction.

**Arguments**:

- `sender_address`: the sender address of the message initiator.
- `contract_address`: the address of the smart contract.
- `handle_msg`: HandleMsg in JSON format.
- `amount`: Funds amount sent with transaction.
- `tx_fee`: the tx fee accepted.
- `denom`: the name of the denomination of the contract funds
- `gas`: Maximum amount of gas to be used on executing command.
- `memo`: any string comment.
- `chain_id`: the Chain ID of the CosmWasm transaction. Default is 1 (i.e. mainnet).

**Returns**:

the unsigned CosmWasm HandleMsg

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.execute_contract_query"></a>
#### execute`_`contract`_`query

```python
 | execute_contract_query(contract_address: Address, query_msg: JSONLike) -> Optional[JSONLike]
```

Execute a CosmWasm QueryMsg. QueryMsg doesn't require signing.

**Arguments**:

- `contract_address`: the address of the smart contract.
- `query_msg`: QueryMsg in JSON format.

**Returns**:

the message receipt

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_transfer_transaction"></a>
#### get`_`transfer`_`transaction

```python
 | get_transfer_transaction(sender_address: Address, destination_address: Address, amount: int, tx_fee: int, tx_nonce: str, denom: Optional[str] = None, gas: int = 80000, memo: str = "", chain_id: Optional[str] = None, **kwargs: Any, ,) -> Optional[JSONLike]
```

Submit a transfer transaction to the ledger.

**Arguments**:

- `sender_address`: the sender address of the payer.
- `destination_address`: the destination address of the payee.
- `amount`: the amount of wealth to be transferred.
- `tx_fee`: the transaction fee.
- `tx_nonce`: verifies the authenticity of the tx
- `denom`: the denomination of tx fee and amount
- `gas`: the gas used.
- `memo`: memo to include in tx.
- `chain_id`: the chain ID of the transaction.

**Returns**:

the transfer transaction

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | send_signed_transaction(tx_signed: JSONLike) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction

**Returns**:

tx_digest, if present

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.is_cosmwasm_transaction"></a>
#### is`_`cosmwasm`_`transaction

```python
 | is_cosmwasm_transaction(tx_signed: JSONLike) -> bool
```

Check whether it is a cosmwasm tx.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.is_transfer_transaction"></a>
#### is`_`transfer`_`transaction

```python
 | @staticmethod
 | is_transfer_transaction(tx_signed: JSONLike) -> bool
```

Check whether it is a transfer tx.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_transaction_receipt"></a>
#### get`_`transaction`_`receipt

```python
 | get_transaction_receipt(tx_digest: str) -> Optional[JSONLike]
```

Get the transaction receipt for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx receipt, if present

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_transaction"></a>
#### get`_`transaction

```python
 | get_transaction(tx_digest: str) -> Optional[JSONLike]
```

Get the transaction for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx, if present

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_contract_instance"></a>
#### get`_`contract`_`instance

```python
 | get_contract_instance(contract_interface: Dict[str, str], contract_address: Optional[str] = None) -> Any
```

Get the instance of a contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `contract_address`: the contract address.

**Returns**:

the contract instance

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_last_code_id"></a>
#### get`_`last`_`code`_`id

```python
 | get_last_code_id() -> int
```

Get ID of latest deployed .wasm bytecode.

**Returns**:

code id of last deployed .wasm bytecode

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_last_contract_address"></a>
#### get`_`last`_`contract`_`address

```python
 | get_last_contract_address(code_id: int) -> str
```

Get contract address of latest initialised contract by its ID.

**Arguments**:

- `code_id`: id of deployed CosmWasm bytecode

**Returns**:

contract address of last initialised contract

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.update_with_gas_estimate"></a>
#### update`_`with`_`gas`_`estimate

```python
 | update_with_gas_estimate(transaction: JSONLike) -> JSONLike
```

Attempts to update the transaction with a gas estimate

**Arguments**:

- `transaction`: the transaction

**Returns**:

the updated transaction

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosApi"></a>
## CosmosApi Objects

```python
class CosmosApi(_CosmosApi,  CosmosHelper)
```

Class to interact with the Cosmos SDK via a HTTP APIs.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosFaucetApi"></a>
## CosmosFaucetApi Objects

```python
class CosmosFaucetApi(FaucetApi)
```

Cosmos testnet faucet API.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosFaucetApi.__init__"></a>
#### `__`init`__`

```python
 | __init__(poll_interval: Optional[float] = None)
```

Initialize CosmosFaucetApi.

<a name="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosFaucetApi.get_wealth"></a>
#### get`_`wealth

```python
 | get_wealth(address: Address, url: Optional[str] = None) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `url`: the url

**Returns**:

None
:raises: RuntimeError of explicit faucet failures

