<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi"></a>

# plugins.aea-ledger-ethereum-hwi.aea`_`ledger`_`ethereum`_`hwi.hwi

Ethereum module wrapping the public and private key cryptography and ledger api.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto"></a>

## EthereumHWICrypto Objects

```python
class EthereumHWICrypto(Crypto[HWIAccount])
```

Class wrapping the Account Generation from Ethereum ledger.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.__init__"></a>

#### `__`init`__`

```python
def __init__(private_key_path: Optional[str] = None,
             password: Optional[str] = None,
             extra_entropy: Union[str, bytes, int] = "",
             **kwargs: Any) -> None
```

Instantiate an ethereum crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent
- `password`: the password to encrypt/decrypt the private key.
- `extra_entropy`: add extra randomness to whatever randomness your OS can provide
- `kwargs`: extra keyword arguments

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.private_key"></a>

#### private`_`key

```python
@property
def private_key() -> str
```

Return a private key.

64 random hex characters (i.e. 32 bytes) + "0x" prefix.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> str
```

Return a public key in hex format.

128 hex characters (i.e. 64 bytes) + "0x" prefix.

**Returns**:

a public key string in hex format

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.address"></a>

#### address

```python
@property
def address() -> str
```

Return the address for the key pair.

40 hex characters (i.e. 20 bytes) + "0x" prefix.

**Returns**:

an address string in hex format

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.load_private_key_from_path"></a>

#### load`_`private`_`key`_`from`_`path

```python
@classmethod
def load_private_key_from_path(cls,
                               file_name: str,
                               password: Optional[str] = None) -> LocalAccount
```

Load a private key in hex format from a file.

**Arguments**:

- `file_name`: the path to the hex file.
- `password`: the password to encrypt/decrypt the private key.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.sign_message"></a>

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

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.sign_transaction"></a>

#### sign`_`transaction

```python
def sign_transaction(transaction: JSONLike, **kwargs: Any) -> JSONLike
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed
- `kwargs`: extra keyword arguments

**Returns**:

signed transaction

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.generate_private_key"></a>

#### generate`_`private`_`key

```python
@classmethod
def generate_private_key(cls,
                         extra_entropy: Union[str, bytes,
                                              int] = "") -> LocalAccount
```

Generate a key pair for ethereum network.

**Arguments**:

- `extra_entropy`: add extra randomness to whatever randomness your OS can provide

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.encrypt"></a>

#### encrypt

```python
def encrypt(password: str) -> str
```

Encrypt the private key and return in json.

**Arguments**:

- `password`: the password to decrypt.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWICrypto.decrypt"></a>

#### decrypt

```python
@classmethod
def decrypt(cls, keyfile_json: str, password: str) -> str
```

Decrypt the private key and return in raw form.

**Arguments**:

- `keyfile_json`: json str containing encrypted private key.
- `password`: the password to decrypt.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWIHelper"></a>

## EthereumHWIHelper Objects

```python
class EthereumHWIHelper(EthereumHelper)
```

Helper class usable as Mixin for EthereumApi or as standalone class.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWIApi"></a>

## EthereumHWIApi Objects

```python
class EthereumHWIApi(EthereumApi, EthereumHWIHelper)
```

Class to interact with the Ethereum Web3 APIs.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWIApi.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any)
```

Initialize object.

<a id="plugins.aea-ledger-ethereum-hwi.aea_ledger_ethereum_hwi.hwi.EthereumHWIFaucetApi"></a>

## EthereumHWIFaucetApi Objects

```python
class EthereumHWIFaucetApi(EthereumFaucetApi)
```

Ethereum testnet faucet API.

