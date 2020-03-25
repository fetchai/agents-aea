<a name=".aea.crypto.wallet"></a>
## aea.crypto.wallet

Module wrapping all the public and private keys cryptography.

<a name=".aea.crypto.wallet.Wallet"></a>
### Wallet

```python
class Wallet()
```

Store all the cryptos we initialise.

<a name=".aea.crypto.wallet.Wallet.__init__"></a>
#### `__`init`__`

```python
 | __init__(private_key_paths: Dict[str, str])
```

Instantiate a wallet object.

**Arguments**:

- `private_key_paths`: the private key paths

<a name=".aea.crypto.wallet.Wallet.public_keys"></a>
#### public`_`keys

```python
 | @property
 | public_keys()
```

Get the public_key dictionary.

<a name=".aea.crypto.wallet.Wallet.crypto_objects"></a>
#### crypto`_`objects

```python
 | @property
 | crypto_objects()
```

Get the crypto objects (key pair).

<a name=".aea.crypto.wallet.Wallet.addresses"></a>
#### addresses

```python
 | @property
 | addresses() -> Dict[str, str]
```

Get the crypto addresses.

