<a name="aea.identity.base"></a>
# aea.identity.base

This module contains the identity class.

<a name="aea.identity.base.Identity"></a>
## Identity Objects

```python
class Identity()
```

The identity holds the public elements identifying an agent.

It includes:

- the agent name
- the addresses, a map from address identifier to address (can be a single key-value pair)

<a name="aea.identity.base.Identity.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: SimpleIdOrStr, address: Optional[str] = None, public_key: Optional[str] = None, addresses: Optional[Dict[str, Address]] = None, public_keys: Optional[Dict[str, str]] = None, default_address_key: str = DEFAULT_LEDGER) -> None
```

Instantiate the identity.

**Arguments**:

- `name`: the name of the agent.
- `address`: the default address of the agent.
- `public_key`: the public key of the agent.
- `addresses`: the addresses of the agent.
- `public_keys`: the public keys of the agent.
- `default_address_key`: the key for the default address.

<a name="aea.identity.base.Identity.default_address_key"></a>
#### default`_`address`_`key

```python
 | @property
 | default_address_key() -> str
```

Get the default address key.

<a name="aea.identity.base.Identity.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the agent name.

<a name="aea.identity.base.Identity.addresses"></a>
#### addresses

```python
 | @property
 | addresses() -> Dict[str, Address]
```

Get the addresses.

<a name="aea.identity.base.Identity.address"></a>
#### address

```python
 | @property
 | address() -> Address
```

Get the default address.

<a name="aea.identity.base.Identity.public_keys"></a>
#### public`_`keys

```python
 | @property
 | public_keys() -> Dict[str, str]
```

Get the public keys.

<a name="aea.identity.base.Identity.public_key"></a>
#### public`_`key

```python
 | @property
 | public_key() -> str
```

Get the default public key.

