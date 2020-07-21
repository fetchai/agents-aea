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
create_private_key(ledger_id: str, private_key_file: Optional[str] = None) -> None
```

Create a private key for the specified ledger identifier.

**Arguments**:

- `ledger_id`: the ledger identifier.

**Returns**:

None
:raises: ValueError if the identifier is invalid.

<a name="aea.crypto.helpers.try_generate_testnet_wealth"></a>
#### try`_`generate`_`testnet`_`wealth

```python
try_generate_testnet_wealth(identifier: str, address: str) -> None
```

Try generate wealth on a testnet.

**Arguments**:

- `identifier`: the identifier of the ledger
- `address`: the address to check for

**Returns**:

None

