<a name="aea.crypto.helpers"></a>
# aea.crypto.helpers

Module wrapping the helpers of public and private key cryptography.

<a name="aea.crypto.helpers.try_validate_private_key_path"></a>
#### try`_`validate`_`private`_`key`_`path

```python
try_validate_private_key_path(ledger_id: str, private_key_path: str, password: Optional[str] = None) -> None
```

Try validate a private key path.

**Arguments**:

- `ledger_id`: one of 'fetchai', 'ethereum'
- `private_key_path`: the path to the private key.
- `password`: the password to encrypt/decrypt the private key.
:raises: ValueError if the identifier is invalid.

<a name="aea.crypto.helpers.create_private_key"></a>
#### create`_`private`_`key

```python
create_private_key(ledger_id: str, private_key_file: str, password: Optional[str] = None) -> None
```

Create a private key for the specified ledger identifier.

**Arguments**:

- `ledger_id`: the ledger identifier.
- `private_key_file`: the private key file.
- `password`: the password to encrypt/decrypt the private key.
:raises: ValueError if the identifier is invalid.

<a name="aea.crypto.helpers.try_generate_testnet_wealth"></a>
#### try`_`generate`_`testnet`_`wealth

```python
try_generate_testnet_wealth(identifier: str, address: str, url: Optional[str] = None, _sync: bool = True) -> None
```

Try generate wealth on a testnet.

**Arguments**:

- `identifier`: the identifier of the ledger
- `address`: the address to check for
- `url`: the url
- `_sync`: whether to wait to sync or not; currently unused

<a name="aea.crypto.helpers.private_key_verify"></a>
#### private`_`key`_`verify

```python
private_key_verify(aea_conf: AgentConfig, aea_project_path: Path, password: Optional[str] = None) -> None
```

Check key.

**Arguments**:

- `aea_conf`: AgentConfig
- `aea_project_path`: Path, where project placed.
- `password`: the password to encrypt/decrypt the private key.

<a name="aea.crypto.helpers.make_certificate"></a>
#### make`_`certificate

```python
make_certificate(ledger_id: str, crypto_private_key_path: str, message: bytes, output_path: str, password: Optional[str] = None) -> str
```

Create certificate.

**Arguments**:

- `ledger_id`: the ledger id
- `crypto_private_key_path`: the path to the private key.
- `message`: the message to be signed.
- `output_path`: the location where to save the certificate.
- `password`: the password to encrypt/decrypt the private keys.

**Returns**:

the signature/certificate

<a name="aea.crypto.helpers.get_wallet_from_agent_config"></a>
#### get`_`wallet`_`from`_`agent`_`config

```python
get_wallet_from_agent_config(agent_config: AgentConfig, password: Optional[str] = None) -> Wallet
```

Get wallet from agent_cofig provided.

**Arguments**:

- `agent_config`: the agent configuration object
- `password`: the password to encrypt/decrypt the private keys.

**Returns**:

wallet

<a name="aea.crypto.helpers.DecryptError"></a>
## DecryptError Objects

```python
class DecryptError(ValueError)
```

Error on bytes decryption with password.

<a name="aea.crypto.helpers.DecryptError.__init__"></a>
#### `__`init`__`

```python
 | __init__(msg: Optional[str] = None) -> None
```

Init exception.

<a name="aea.crypto.helpers.KeyIsIncorrect"></a>
## KeyIsIncorrect Objects

```python
class KeyIsIncorrect(ValueError)
```

Error decoding hex string to bytes for private key.

<a name="aea.crypto.helpers.hex_to_bytes_for_key"></a>
#### hex`_`to`_`bytes`_`for`_`key

```python
hex_to_bytes_for_key(data: str) -> bytes
```

Convert hex string to bytes with error handling.

