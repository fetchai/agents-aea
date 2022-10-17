<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos"></a>

# plugins.aea-ledger-fetchai.aea`_`ledger`_`fetchai.`_`cosmos

Cosmos module wrapping the public and private key cryptography and ledger api.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.lazy_load"></a>

#### lazy`_`load

```python
def lazy_load()
```

Temporary solution because of protos mismatch.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.DataEncrypt"></a>

## DataEncrypt Objects

```python
class DataEncrypt()
```

Class to encrypt/decrypt data strings with password provided.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.DataEncrypt.encrypt"></a>

#### encrypt

```python
@classmethod
def encrypt(cls, data: bytes, password: str) -> bytes
```

Encrypt data with password.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.DataEncrypt.bytes_encode"></a>

#### bytes`_`encode

```python
@staticmethod
def bytes_encode(data: bytes) -> str
```

Encode bytes to ascii friendly string.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.DataEncrypt.bytes_decode"></a>

#### bytes`_`decode

```python
@staticmethod
def bytes_decode(data: str) -> bytes
```

Decode ascii friendly string to bytes.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.DataEncrypt.decrypt"></a>

#### decrypt

```python
@classmethod
def decrypt(cls, encrypted_data: bytes, password: str) -> bytes
```

Decrypt data with password provided.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper"></a>

## CosmosHelper Objects

```python
class CosmosHelper(Helper)
```

Helper class usable as Mixin for CosmosApi or as standalone class.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.is_transaction_settled"></a>

#### is`_`transaction`_`settled

```python
@staticmethod
def is_transaction_settled(tx_receipt: JSONLike) -> bool
```

Check whether a transaction is settled or not.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

True if the transaction has been settled, False o/w.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_code_id"></a>

#### get`_`code`_`id

```python
@classmethod
def get_code_id(cls, tx_receipt: JSONLike) -> Optional[int]
```

Retrieve the `code_id` from a transaction receipt.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

the code id, if present

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_event_attributes"></a>

#### get`_`event`_`attributes

```python
@staticmethod
def get_event_attributes(tx_receipt: JSONLike) -> Dict
```

Retrieve events attributes from tx receipt.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

dict

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_contract_address"></a>

#### get`_`contract`_`address

```python
@classmethod
def get_contract_address(cls, tx_receipt: JSONLike) -> Optional[str]
```

Retrieve the `contract_address` from a transaction receipt.

**Arguments**:

- `tx_receipt`: the receipt of the transaction.

**Returns**:

the contract address, if present

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.is_transaction_valid"></a>

#### is`_`transaction`_`valid

```python
@staticmethod
def is_transaction_valid(tx: JSONLike, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
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

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.generate_tx_nonce"></a>

#### generate`_`tx`_`nonce

```python
@staticmethod
def generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a unique hash to distinguish transactions with the same terms.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_address_from_public_key"></a>

#### get`_`address`_`from`_`public`_`key

```python
@classmethod
def get_address_from_public_key(cls, public_key: str) -> str
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.recover_message"></a>

#### recover`_`message

```python
@classmethod
def recover_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[Address, ...]
```

Recover the addresses from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered addresses

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.recover_public_keys_from_message"></a>

#### recover`_`public`_`keys`_`from`_`message

```python
@classmethod
def recover_public_keys_from_message(cls, message: bytes, signature: str, is_deprecated_mode: bool = False) -> Tuple[str, ...]
```

Get the public key used to produce the `signature` of the `message`

**Arguments**:

- `message`: raw bytes used to produce signature
- `signature`: signature of the message
- `is_deprecated_mode`: if the deprecated signing was used

**Returns**:

the recovered public keys

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.get_hash"></a>

#### get`_`hash

```python
@staticmethod
def get_hash(message: bytes) -> str
```

Get the hash of a message.

**Arguments**:

- `message`: the message to be hashed.

**Returns**:

the hash of the message.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.is_valid_address"></a>

#### is`_`valid`_`address

```python
@classmethod
def is_valid_address(cls, address: Address) -> bool
```

Check if the address is valid.

**Arguments**:

- `address`: the address to validate

**Returns**:

whether address is valid or not

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosHelper.load_contract_interface"></a>

#### load`_`contract`_`interface

```python
@classmethod
def load_contract_interface(cls, file_path: Path) -> Dict[str, str]
```

Load contract interface.

**Arguments**:

- `file_path`: the file path to the interface

**Returns**:

the interface

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto"></a>

## CosmosCrypto Objects

```python
class CosmosCrypto(Crypto[SigningKey])
```

Class wrapping the Account Generation from Ethereum ledger.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.__init__"></a>

#### `__`init`__`

```python
def __init__(private_key_path: Optional[str] = None, password: Optional[str] = None, extra_entropy: Union[str, bytes, int] = "") -> None
```

Instantiate an ethereum crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent
- `password`: the password to encrypt/decrypt the private key.
- `extra_entropy`: add extra randomness to whatever randomness your OS can provide

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.private_key"></a>

#### private`_`key

```python
@property
def private_key() -> str
```

Return a private key.

**Returns**:

a private key string

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.address"></a>

#### address

```python
@property
def address() -> str
```

Return the address for the key pair.

**Returns**:

a display_address str

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.load_private_key_from_path"></a>

#### load`_`private`_`key`_`from`_`path

```python
@classmethod
def load_private_key_from_path(cls, file_name: str, password: Optional[str] = None) -> SigningKey
```

Load a private key in hex format from a file.

**Arguments**:

- `file_name`: the path to the hex file.
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

the Entity.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.sign_message"></a>

#### sign`_`message

```python
def sign_message(message: bytes, is_deprecated_mode: bool = False) -> str
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message to be signed
- `is_deprecated_mode`: if the deprecated signing is used

**Returns**:

signature of the message in string form

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.sign_transaction"></a>

#### sign`_`transaction

```python
def sign_transaction(transaction: JSONLike) -> JSONLike
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed

**Returns**:

signed transaction

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.generate_private_key"></a>

#### generate`_`private`_`key

```python
@classmethod
def generate_private_key(cls, extra_entropy: Union[str, bytes, int] = "") -> SigningKey
```

Generate a key pair for cosmos network.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.encrypt"></a>

#### encrypt

```python
def encrypt(password: str) -> str
```

Encrypt the private key and return in json.

**Arguments**:

- `password`: the password to decrypt.

**Returns**:

json string containing encrypted private key.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosCrypto.decrypt"></a>

#### decrypt

```python
@classmethod
def decrypt(cls, keyfile_json: str, password: str) -> str
```

Decrypt the private key and return in raw form.

**Arguments**:

- `keyfile_json`: json string containing encrypted private key.
- `password`: the password to decrypt.

**Returns**:

the raw private key.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi"></a>

## `_`CosmosApi Objects

```python
class _CosmosApi(LedgerApi)
```

Class to interact with the Cosmos SDK via a HTTP APIs.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the Cosmos ledger APIs.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.api"></a>

#### api

```python
@property
def api() -> Any
```

Get the underlying API object.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_balance"></a>

#### get`_`balance

```python
def get_balance(address: Address, raise_on_try: bool = False) -> Optional[int]
```

Get the balance of a given account.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_state"></a>

#### get`_`state

```python
def get_state(callable_name: str, *args: Any, *, raise_on_try: bool = False, **kwargs: Any) -> Optional[JSONLike]
```

Call a specified function on the ledger API.

Based on the cosmos REST
API specification, which takes a path (strings separated by '/'). The
convention here is to define the root of the path (txs, blocks, etc.)
as the callable_name and the rest of the path as args.

**Arguments**:

- `callable_name`: name of the callable
- `args`: positional arguments
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: keyword arguments

**Returns**:

the transaction dictionary

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_deploy_transaction"></a>

#### get`_`deploy`_`transaction

```python
def get_deploy_transaction(contract_interface: Dict[str, str], deployer_address: Address, raise_on_try: bool = False, **kwargs: Any, ,) -> Optional[JSONLike]
```

Get the transaction to deploy the smart contract.

Dispatches to _get_storage_transaction and _get_init_transaction based on kwargs.

**Arguments**:

- `contract_interface`: the contract interface.
- `deployer_address`: The address that will deploy the contract.
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: keyword arguments.

**Returns**:

the transaction dictionary.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_handle_transaction"></a>

#### get`_`handle`_`transaction

```python
def get_handle_transaction(sender_address: Address, contract_address: Address, handle_msg: Any, amount: int, tx_fee: int, denom: Optional[str] = None, gas: int = DEFAULT_GAS_AMOUNT, memo: str = "", chain_id: Optional[str] = None, account_number: Optional[int] = None, sequence: Optional[int] = None, tx_fee_denom: Optional[str] = None, raise_on_try: bool = False) -> Optional[JSONLike]
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
- `account_number`: Account number
- `sequence`: Sequence
- `tx_fee_denom`: Denomination of tx_fee, identical with denom param when None
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the unsigned CosmWasm HandleMsg

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.execute_contract_query"></a>

#### execute`_`contract`_`query

```python
def execute_contract_query(contract_address: Address, query_msg: JSONLike, raise_on_try: bool = False) -> Optional[JSONLike]
```

Execute a CosmWasm QueryMsg. QueryMsg doesn't require signing.

**Arguments**:

- `contract_address`: the address of the smart contract.
- `query_msg`: QueryMsg in JSON format.
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the message receipt

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_transfer_transaction"></a>

#### get`_`transfer`_`transaction

```python
def get_transfer_transaction(sender_address: Address, destination_address: Address, amount: int, tx_fee: int, tx_nonce: str, denom: Optional[str] = None, gas: int = DEFAULT_GAS_AMOUNT, memo: str = "", chain_id: Optional[str] = None, account_number: Optional[int] = None, sequence: Optional[int] = None, tx_fee_denom: Optional[str] = None, raise_on_try: bool = False, **kwargs: Any, ,) -> Optional[JSONLike]
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
- `account_number`: Account number
- `sequence`: Sequence
- `tx_fee_denom`: Denomination of tx_fee, identical with denom param when None
- `raise_on_try`: whether the method will raise or log on error
- `kwargs`: keyword arguments.

**Returns**:

the transfer transaction

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_packed_exec_msg"></a>

#### get`_`packed`_`exec`_`msg

```python
def get_packed_exec_msg(sender_address: Address, contract_address: str, msg: JSONLike, funds: int = 0, denom: Optional[str] = None) -> ProtoAny
```

Create and pack MsgExecuteContract

**Arguments**:


- `sender_address`: Address of sender
- `contract_address`: Address of contract
- `msg`: Paramaters to be passed to smart contract
- `funds`: Funds to be sent to smart contract
- `denom`: the denomination of funds

**Returns**:

Packed MsgExecuteContract

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_packed_send_msg"></a>

#### get`_`packed`_`send`_`msg

```python
def get_packed_send_msg(from_address: Address, to_address: Address, amount: int, denom: Optional[str] = None) -> ProtoAny
```

Generate and pack MsgSend

**Arguments**:


- `from_address`: Address of sender
- `to_address`: Address of recipient
- `amount`: amount of coins to be sent
- `denom`: the denomination of and amount

**Returns**:

packer ProtoAny type message

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_multi_transaction"></a>

#### get`_`multi`_`transaction

```python
def get_multi_transaction(from_addresses: List[str], pub_keys: Optional[List[bytes]], msgs: List[ProtoAny], gas: int, tx_fee: int = 0, memo: str = "", chain_id: Optional[str] = None, denom: Optional[str] = None, tx_fee_denom: Optional[str] = None, raise_on_try: bool = False) -> JSONLike
```

Generate transaction with multiple messages

**Arguments**:


- `from_addresses`: Addresses of signers
- `pub_keys`: Public keys of signers
- `msgs`: Messages to be included in transaction
- `gas`: the gas used.
- `tx_fee`: the transaction fee.
- `memo`: memo to include in tx.
- `chain_id`: the chain ID of the transaction.
- `denom`: the denomination of tx fee
- `tx_fee_denom`: Denomination of tx_fee, identical with denom param when None
- `raise_on_try`: whether the method will raise or log on error

**Raises**:

- `RuntimeError`: if number of pubkeys is not equal to number of from_addresses

**Returns**:

the transaction

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.send_signed_transaction"></a>

#### send`_`signed`_`transaction

```python
def send_signed_transaction(tx_signed: JSONLike, raise_on_try: bool = False) -> Optional[str]
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `tx_signed`: the signed transaction
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

tx_digest, if present

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_transaction_receipt"></a>

#### get`_`transaction`_`receipt

```python
def get_transaction_receipt(tx_digest: str, raise_on_try: bool = False) -> Optional[JSONLike]
```

Get the transaction receipt for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the tx receipt, if present

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_transaction"></a>

#### get`_`transaction

```python
def get_transaction(tx_digest: str, raise_on_try: bool = False) -> Optional[JSONLike]
```

Get the transaction for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.
- `raise_on_try`: whether the method will raise or log on error

**Returns**:

the tx, if present

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_contract_instance"></a>

#### get`_`contract`_`instance

```python
def get_contract_instance(contract_interface: Dict[str, str], contract_address: Optional[str] = None) -> Any
```

Get the instance of a contract.

**Arguments**:

- `contract_interface`: the contract interface.
- `contract_address`: the contract address.

**Returns**:

the contract instance

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.update_with_gas_estimate"></a>

#### update`_`with`_`gas`_`estimate

```python
def update_with_gas_estimate(transaction: JSONLike) -> JSONLike
```

Attempts to update the transaction with a gas estimate

**Arguments**:

- `transaction`: the transaction

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.contract_method_call"></a>

#### contract`_`method`_`call

```python
def contract_method_call(contract_instance: Any, method_name: str, **method_args: Any, ,) -> Optional[JSONLike]
```

Call a contract's method

**Arguments**:

- `contract_instance`: the contract to use
- `method_name`: the contract method to call
- `method_args`: the contract call parameters

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.build_transaction"></a>

#### build`_`transaction

```python
def build_transaction(contract_instance: Any, method_name: str, method_args: Optional[Dict], tx_args: Optional[Dict], raise_on_try: bool = False) -> Optional[JSONLike]
```

Prepare a transaction

**Arguments**:

- `contract_instance`: the contract to use
- `method_name`: the contract method to call
- `method_args`: the contract parameters
- `tx_args`: the transaction parameters
- `raise_on_try`: whether the method will raise or log on error

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos._CosmosApi.get_transaction_transfer_logs"></a>

#### get`_`transaction`_`transfer`_`logs

```python
def get_transaction_transfer_logs(contract_instance: Any, tx_hash: str, target_address: Optional[str] = None) -> Optional[JSONLike]
```

Get all transfer events derived from a transaction.

**Arguments**:

- `contract_instance`: the contract
- `tx_hash`: the transaction hash
- `target_address`: optional address to filter tranfer events to just those that affect it

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosApi"></a>

## CosmosApi Objects

```python
class CosmosApi(_CosmosApi,  CosmosHelper)
```

Class to interact with the Cosmos SDK via a HTTP APIs.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosFaucetApi"></a>

## CosmosFaucetApi Objects

```python
class CosmosFaucetApi(FaucetApi)
```

Cosmos testnet faucet API.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosFaucetApi.__init__"></a>

#### `__`init`__`

```python
def __init__(poll_interval: Optional[float] = None, final_wait_interval: Optional[float] = None)
```

Initialize CosmosFaucetApi.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai._cosmos.CosmosFaucetApi.get_wealth"></a>

#### get`_`wealth

```python
def get_wealth(address: Address, url: Optional[str] = None) -> None
```

Get wealth from the faucet for the provided address.

**Arguments**:

- `address`: the address.
- `url`: the url

**Raises**:

- `RuntimeError`: of explicit faucet failures

