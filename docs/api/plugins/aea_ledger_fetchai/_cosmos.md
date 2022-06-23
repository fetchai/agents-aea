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
def is_transaction_valid(tx: JSONLike, seller: Address, client: Address,
                         tx_nonce: str, amount: int) -> bool
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
def recover_message(cls,
                    message: bytes,
                    signature: str,
                    is_deprecated_mode: bool = False) -> Tuple[Address, ...]
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
def recover_public_keys_from_message(
        cls,
        message: bytes,
        signature: str,
        is_deprecated_mode: bool = False) -> Tuple[str, ...]
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
def __init__(private_key_path: Optional[str] = None,
             password: Optional[str] = None,
             extra_entropy: Union[str, bytes, int] = "") -> None
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
def load_private_key_from_path(cls,
                               file_name: str,
                               password: Optional[str] = None) -> SigningKey
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
def generate_private_key(cls,
                         extra_entropy: Union[str, bytes,
                                              int] = "") -> SigningKey
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
def get_state(callable_name: str,
              *args: Any,
              raise_on_try: bool = False,
              **kwargs: Any) -> Optional[JSONLike]
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

