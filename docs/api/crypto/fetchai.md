<a name=".aea.crypto.fetchai"></a>
## aea.crypto.fetchai

Fetchai module wrapping the public and private key cryptography and ledger api.

<a name=".aea.crypto.fetchai.FetchAICrypto"></a>
### FetchAICrypto

```python
class FetchAICrypto(Crypto)
```

Class wrapping the Entity Generation from Fetch.AI ledger.

<a name=".aea.crypto.fetchai.FetchAICrypto.__init__"></a>
#### `__`init`__`

```python
 | __init__(private_key_path: Optional[str] = None)
```

Instantiate a fetchai crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent

<a name=".aea.crypto.fetchai.FetchAICrypto.entity"></a>
#### entity

```python
 | @property
 | entity() -> Entity
```

Get the entity.

<a name=".aea.crypto.fetchai.FetchAICrypto.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a name=".aea.crypto.fetchai.FetchAICrypto.address"></a>
#### address

```python
 | @property
 | address() -> str
```

Return the address for the key pair.

**Returns**:

a display_address str

<a name=".aea.crypto.fetchai.FetchAICrypto.sign_message"></a>
#### sign`_`message

```python
 | sign_message(message: bytes, is_deprecated_mode: bool = False) -> str
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message we want to send
- `is_deprecated_mode`: if the deprecated signing is used

**Returns**:

signature of the message in string form

<a name=".aea.crypto.fetchai.FetchAICrypto.sign_transaction"></a>
#### sign`_`transaction

```python
 | sign_transaction(transaction: Any) -> Any
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed

**Returns**:

signed transaction

<a name=".aea.crypto.fetchai.FetchAICrypto.recover_message"></a>
#### recover`_`message

```python
 | recover_message(message: bytes, signature: bytes) -> Address
```

Recover the address from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature

**Returns**:

the recovered address

<a name=".aea.crypto.fetchai.FetchAICrypto.get_address_from_public_key"></a>
#### get`_`address`_`from`_`public`_`key

```python
 | @classmethod
 | get_address_from_public_key(cls, public_key: str) -> Address
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a name=".aea.crypto.fetchai.FetchAICrypto.load"></a>
#### load

```python
 | @classmethod
 | load(cls, fp: BinaryIO)
```

Deserialize binary file `fp` (a `.read()`-supporting file-like object containing a private key).

**Arguments**:

- `fp`: the input file pointer. Must be set in binary mode (mode='rb')

**Returns**:

None

<a name=".aea.crypto.fetchai.FetchAICrypto.dump"></a>
#### dump

```python
 | dump(fp: BinaryIO) -> None
```

Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

**Arguments**:

- `fp`: the output file pointer. Must be set in binary mode (mode='wb')

**Returns**:

None

<a name=".aea.crypto.fetchai.FetchAIApi"></a>
### FetchAIApi

```python
class FetchAIApi(LedgerApi)
```

Class to interact with the Fetch ledger APIs.

<a name=".aea.crypto.fetchai.FetchAIApi.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs)
```

Initialize the Fetch.AI ledger APIs.

**Arguments**:

- `kwargs`: key word arguments (expects either a pair of 'host' and 'port' or a 'network')

<a name=".aea.crypto.fetchai.FetchAIApi.api"></a>
#### api

```python
 | @property
 | api() -> FetchaiLedgerApi
```

Get the underlying API object.

<a name=".aea.crypto.fetchai.FetchAIApi.get_balance"></a>
#### get`_`balance

```python
 | get_balance(address: AddressLike) -> int
```

Get the balance of a given account.

<a name=".aea.crypto.fetchai.FetchAIApi.send_transaction"></a>
#### send`_`transaction

```python
 | send_transaction(crypto: Crypto, destination_address: AddressLike, amount: int, tx_fee: int, tx_nonce: str, is_waiting_for_confirmation: bool = True, **kwargs) -> Optional[str]
```

Submit a transaction to the ledger.

<a name=".aea.crypto.fetchai.FetchAIApi.send_raw_transaction"></a>
#### send`_`raw`_`transaction

```python
 | send_raw_transaction(tx_signed) -> Optional[Dict]
```

Send a signed transaction and wait for confirmation.

<a name=".aea.crypto.fetchai.FetchAIApi.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | is_transaction_settled(tx_digest: str) -> bool
```

Check whether a transaction is settled or not.

<a name=".aea.crypto.fetchai.FetchAIApi.send_signed_transaction"></a>
#### send`_`signed`_`transaction

```python
 | send_signed_transaction(is_waiting_for_confirmation: bool, tx_signed: Any, **kwargs) -> str
```

Send a signed transaction and wait for confirmation.

**Arguments**:

- `is_waiting_for_confirmation`: whether or not to wait for confirmation
- `tx_signed`: the signed transaction

<a name=".aea.crypto.fetchai.FetchAIApi.get_transaction_status"></a>
#### get`_`transaction`_`status

```python
 | get_transaction_status(tx_digest: str) -> Any
```

Get the transaction status for a transaction digest.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

the tx status, if present

<a name=".aea.crypto.fetchai.FetchAIApi.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a random str message.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

<a name=".aea.crypto.fetchai.FetchAIApi.validate_transaction"></a>
#### validate`_`transaction

```python
 | validate_transaction(tx_digest: str, seller: Address, client: Address, tx_nonce: str, amount: int) -> bool
```

Check whether a transaction is valid or not.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.
- `tx_nonce`: the transaction nonce.
- `amount`: the amount we expect to get from the transaction.
- `tx_digest`: the transaction digest.

**Returns**:

True if the random_message is equals to tx['input']

