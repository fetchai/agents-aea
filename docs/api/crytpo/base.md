<a name=".aea.crypto.base"></a>
## aea.crypto.base

Abstract module wrapping the public and private key cryptography and ledger api.

<a name=".aea.crypto.base.Crypto"></a>
### Crypto

```python
class Crypto(ABC)
```

Base class for a crypto object.

<a name=".aea.crypto.base.Crypto.entity"></a>
#### entity

```python
 | @property
 | @abstractmethod
 | entity() -> Any
```

Return an entity object.

**Returns**:

an entity object

<a name=".aea.crypto.base.Crypto.public_key"></a>
#### public`_`key

```python
 | @property
 | @abstractmethod
 | public_key() -> str
```

Return a public key.

**Returns**:

a public key string

<a name=".aea.crypto.base.Crypto.address"></a>
#### address

```python
 | @property
 | @abstractmethod
 | address() -> str
```

Return the address.

**Returns**:

an address string

<a name=".aea.crypto.base.Crypto.get_address_from_public_key"></a>
#### get`_`address`_`from`_`public`_`key

```python
 | @classmethod
 | @abstractmethod
 | get_address_from_public_key(cls, public_key: str) -> str
```

Get the address from the public key.

**Arguments**:

- `public_key`: the public key

**Returns**:

str

<a name=".aea.crypto.base.Crypto.sign_message"></a>
#### sign`_`message

```python
 | @abstractmethod
 | sign_message(message: bytes) -> bytes
```

Sign a message in bytes string form.

**Arguments**:

- `message`: the message we want to send

**Returns**:

Signed message in bytes

<a name=".aea.crypto.base.Crypto.recover_message"></a>
#### recover`_`message

```python
 | @abstractmethod
 | recover_message(message: bytes, signature: bytes) -> Address
```

Recover the address from the hash.

**Arguments**:

- `message`: the message we expect
- `signature`: the transaction signature

**Returns**:

the recovered address

<a name=".aea.crypto.base.Crypto.load"></a>
#### load

```python
 | @classmethod
 | @abstractmethod
 | load(cls, fp: BinaryIO) -> "Crypto"
```

Deserialize binary file `fp` (a `.read()`-supporting file-like object containing a private key).

**Arguments**:

- `fp`: the input file pointer. Must be set in binary mode (mode='rb')

**Returns**:

None

<a name=".aea.crypto.base.Crypto.dump"></a>
#### dump

```python
 | @abstractmethod
 | dump(fp: BinaryIO) -> None
```

Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

**Arguments**:

- `fp`: the output file pointer. Must be set in binary mode (mode='wb')

**Returns**:

None

<a name=".aea.crypto.base.LedgerApi"></a>
### LedgerApi

```python
class LedgerApi(ABC)
```

Interface for ledger APIs.

<a name=".aea.crypto.base.LedgerApi.api"></a>
#### api

```python
 | @property
 | @abstractmethod
 | api() -> Any
```

Get the underlying API object.

This can be used for low-level operations with the concrete ledger APIs.
If there is no such object, return None.

<a name=".aea.crypto.base.LedgerApi.get_balance"></a>
#### get`_`balance

```python
 | @abstractmethod
 | get_balance(address: AddressLike) -> int
```

Get the balance of a given account.

This usually takes the form of a web request to be waited synchronously.

**Arguments**:

- `address`: the address.

**Returns**:

the balance.

<a name=".aea.crypto.base.LedgerApi.send_transaction"></a>
#### send`_`transaction

```python
 | @abstractmethod
 | send_transaction(crypto: Crypto, destination_address: AddressLike, amount: int, tx_fee: int, tx_nonce: str, **kwargs) -> Optional[str]
```

Submit a transaction to the ledger.

If the mandatory arguments are not enough for specifying a transaction
in the concrete ledger API, use keyword arguments for the additional parameters.

**Arguments**:

- `tx_nonce`: verifies the authenticity of the tx
- `crypto`: the crypto object associated to the payer.
- `destination_address`: the destination address of the payee.
- `amount`: the amount of wealth to be transferred.
- `tx_fee`: the transaction fee.

**Returns**:

tx digest if successful, otherwise None

<a name=".aea.crypto.base.LedgerApi.is_transaction_settled"></a>
#### is`_`transaction`_`settled

```python
 | @abstractmethod
 | is_transaction_settled(tx_digest: str) -> bool
```

Check whether a transaction is settled or not.

**Arguments**:

- `tx_digest`: the digest associated to the transaction.

**Returns**:

True if the transaction has been settled, False o/w.

<a name=".aea.crypto.base.LedgerApi.validate_transaction"></a>
#### validate`_`transaction

```python
 | @abstractmethod
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

True if the transaction referenced by the tx_digest matches the terms.

<a name=".aea.crypto.base.LedgerApi.generate_tx_nonce"></a>
#### generate`_`tx`_`nonce

```python
 | @abstractmethod
 | generate_tx_nonce(seller: Address, client: Address) -> str
```

Generate a random str message.

**Arguments**:

- `seller`: the address of the seller.
- `client`: the address of the client.

**Returns**:

return the hash in hex.

