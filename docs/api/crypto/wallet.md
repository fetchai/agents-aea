<a name="aea.crypto.wallet"></a>
# aea.crypto.wallet

Module wrapping all the public and private keys cryptography.

<a name="aea.crypto.wallet.CryptoStore"></a>
## CryptoStore Objects

```python
class CryptoStore()
```

Utility class to store and retrieve crypto objects.

<a name="aea.crypto.wallet.CryptoStore.__init__"></a>
#### `__`init`__`

```python
 | __init__(crypto_id_to_path: Optional[Dict[str, Optional[str]]] = None, password: Optional[str] = None) -> None
```

Initialize the crypto store.

**Arguments**:

- `crypto_id_to_path`: dictionary from crypto id to an (optional) path
    to the private key.
- `password`: the password to encrypt/decrypt the private key.

<a name="aea.crypto.wallet.CryptoStore.public_keys"></a>
#### public`_`keys

```python
 | @property
 | public_keys() -> Dict[str, str]
```

Get the public_key dictionary.

<a name="aea.crypto.wallet.CryptoStore.crypto_objects"></a>
#### crypto`_`objects

```python
 | @property
 | crypto_objects() -> Dict[str, Crypto]
```

Get the crypto objects (key pair).

<a name="aea.crypto.wallet.CryptoStore.addresses"></a>
#### addresses

```python
 | @property
 | addresses() -> Dict[str, str]
```

Get the crypto addresses.

<a name="aea.crypto.wallet.CryptoStore.private_keys"></a>
#### private`_`keys

```python
 | @property
 | private_keys() -> Dict[str, str]
```

Get the crypto addresses.

<a name="aea.crypto.wallet.Wallet"></a>
## Wallet Objects

```python
class Wallet()
```

Container for crypto objects.

The cryptos are separated into two categories:

- main cryptos: used by the AEA for the economic side (i.e. signing transaction)
- connection cryptos: exposed to the connection objects for encrypted communication.

<a name="aea.crypto.wallet.Wallet.__init__"></a>
#### `__`init`__`

```python
 | __init__(private_key_paths: Dict[str, Optional[str]], connection_private_key_paths: Optional[Dict[str, Optional[str]]] = None, password: Optional[str] = None)
```

Instantiate a wallet object.

**Arguments**:

- `private_key_paths`: the private key paths
- `connection_private_key_paths`: the private key paths for the connections.
- `password`: the password to encrypt/decrypt the private key.

<a name="aea.crypto.wallet.Wallet.public_keys"></a>
#### public`_`keys

```python
 | @property
 | public_keys() -> Dict[str, str]
```

Get the public_key dictionary.

<a name="aea.crypto.wallet.Wallet.crypto_objects"></a>
#### crypto`_`objects

```python
 | @property
 | crypto_objects() -> Dict[str, Crypto]
```

Get the crypto objects (key pair).

<a name="aea.crypto.wallet.Wallet.addresses"></a>
#### addresses

```python
 | @property
 | addresses() -> Dict[str, str]
```

Get the crypto addresses.

<a name="aea.crypto.wallet.Wallet.private_keys"></a>
#### private`_`keys

```python
 | @property
 | private_keys() -> Dict[str, str]
```

Get the crypto addresses.

<a name="aea.crypto.wallet.Wallet.main_cryptos"></a>
#### main`_`cryptos

```python
 | @property
 | main_cryptos() -> CryptoStore
```

Get the main crypto store.

<a name="aea.crypto.wallet.Wallet.connection_cryptos"></a>
#### connection`_`cryptos

```python
 | @property
 | connection_cryptos() -> CryptoStore
```

Get the connection crypto store.

<a name="aea.crypto.wallet.Wallet.sign_message"></a>
#### sign`_`message

```python
 | sign_message(crypto_id: str, message: bytes, is_deprecated_mode: bool = False) -> Optional[str]
```

Sign a message.

**Arguments**:

- `crypto_id`: the id of the crypto
- `message`: the message to be signed
- `is_deprecated_mode`: what signing mode to use

**Returns**:

the signature of the message

<a name="aea.crypto.wallet.Wallet.sign_transaction"></a>
#### sign`_`transaction

```python
 | sign_transaction(crypto_id: str, transaction: Any) -> Optional[JSONLike]
```

Sign a tx.

**Arguments**:

- `crypto_id`: the id of the crypto
- `transaction`: the transaction to be signed

**Returns**:

the signed tx

