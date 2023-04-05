<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto"></a>

# plugins.aea-ledger-solana.aea`_`ledger`_`solana.crypto

This module contains the Crypto implementation for the solana ledger.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto"></a>

## SolanaCrypto Objects

```python
class SolanaCrypto(Crypto[Keypair])
```

Class wrapping the Account Generation from Solana ledger.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.__init__"></a>

#### `__`init`__`

```python
def __init__(private_key_path: Optional[str] = None,
             password: Optional[str] = None,
             extra_entropy: Union[str, bytes, int] = "") -> None
```

Instantiate a solana crypto object.

**Arguments**:

- `private_key_path`: the private key path of the agent
- `password`: the password to encrypt/decrypt the private key.
- `extra_entropy`: add extra randomness to whatever randomness from OS.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.private_key"></a>

#### private`_`key

```python
@property
def private_key() -> str
```

Return a private key.

64 random hex characters (i.e. 32 bytes) prefix.

**Returns**:

a private key string in hex format

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> str
```

Return a public key in hex format.

**Returns**:

a public key string in hex format

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.address"></a>

#### address

```python
@property
def address() -> str
```

Return the address for the key pair.

**Returns**:

an address string in hex format

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.load_private_key_from_path"></a>

#### load`_`private`_`key`_`from`_`path

```python
@classmethod
def load_private_key_from_path(cls,
                               file_name: str,
                               password: Optional[str] = None) -> Keypair
```

Load a private key in base58 or bytes format from a file.

**Arguments**:

- `file_name`: the path to the hex file.
- `password`: the password to encrypt/decrypt the private key.

**Returns**:

the Entity.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.sign_message"></a>

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

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.sign_transaction"></a>

#### sign`_`transaction

```python
def sign_transaction(transaction: JSONLike,
                     signers: Optional[list] = None) -> JSONLike
```

Sign a transaction in bytes string form.

**Arguments**:

- `transaction`: the transaction to be signed
- `signers`: list of signers

**Returns**:

signed transaction

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.generate_private_key"></a>

#### generate`_`private`_`key

```python
@classmethod
def generate_private_key(cls,
                         extra_entropy: Union[str, bytes,
                                              int] = "") -> Keypair
```

Generate a key pair for Solana network.

**Arguments**:

- `extra_entropy`: add extra randomness to whatever randomness your OS can provide

**Returns**:

keypair object

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.encrypt"></a>

#### encrypt

```python
def encrypt(password: str) -> str
```

Encrypt the private key and return in json.

**Arguments**:

- `password`: the password to decrypt.

**Returns**:

json string containing encrypted private key.

<a id="plugins.aea-ledger-solana.aea_ledger_solana.crypto.SolanaCrypto.decrypt"></a>

#### decrypt

```python
@classmethod
def decrypt(cls, keyfile_json: str, password: str) -> str
```

Decrypt the private key and return in raw form.

**Arguments**:

- `keyfile_json`: json str containing encrypted private key.
- `password`: the password to decrypt.

**Returns**:

the raw private key.

