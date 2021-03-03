<a name="aea.crypto.helpers"></a>
# aea.crypto.helpers

Module wrapping the helpers of public and private key cryptography.

<a name="aea.crypto.helpers.try_validate_private_key_path"></a>
#### try`_`validate`_`private`_`key`_`path

```python
try_validate_private_key_path(ledger_id: str, private_key_path: str, exit_on_error: bool = True) -> None
```

Try validate a private key path.

**Arguments**:

- `ledger_id`: one of 'fetchai', 'ethereum'
- `private_key_path`: the path to the private key.

**Returns**:

None
:raises: ValueError if the identifier is invalid.

<a name="aea.crypto.helpers.create_private_key"></a>
#### create`_`private`_`key

```python
create_private_key(ledger_id: str, private_key_file: str) -> None
```

Create a private key for the specified ledger identifier.

**Arguments**:

- `ledger_id`: the ledger identifier.
- `private_key_file`: the private key file.

**Returns**:

None
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

**Returns**:

None

<a name="aea.crypto.helpers.private_key_verify_or_create"></a>
#### private`_`key`_`verify`_`or`_`create

```python
private_key_verify_or_create(aea_conf: AgentConfig, aea_project_path: Path, create_keys: bool = True) -> None
```

Check key or create if none present.

**Arguments**:

- `aea_conf`: AgentConfig
- `aea_project_path`: Path, where project placed.

**Returns**:

None

<a name="aea.crypto.helpers.make_certificate"></a>
#### make`_`certificate

```python
make_certificate(ledger_id: str, crypto_private_key_path: str, message: bytes, output_path: str) -> str
```

Create certificate.

<a name="aea.crypto.helpers.get_wallet_from_agent_config"></a>
#### get`_`wallet`_`from`_`agent`_`config

```python
get_wallet_from_agent_config(agent_config: AgentConfig) -> Wallet
```

Get wallet from agent_cofig provided.

