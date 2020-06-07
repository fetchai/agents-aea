<a name=".aea.identity.base"></a>
# aea.identity.base

This module contains the identity class.

<a name=".aea.identity.base.Identity"></a>
## Identity Objects

```python
class Identity()
```

The identity holds the public elements identifying an agent.

It includes:

- the agent name
- the addresses, a map from address identifier to address (can be a single key-value pair)

<a name=".aea.identity.base.Identity.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, address: Optional[str] = None, addresses: Optional[Dict[str, Address]] = None, default_address_key: str = DEFAULT_ADDRESS_KEY)
```

Instantiate the identity.

**Arguments**:

- `name`: the name of the agent.
- `address`: the default address of the agent.
- `addresses`: the addresses of the agent.
- `default_address_key`: the key for the default address.

<a name=".aea.identity.base.Identity.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the agent name.

<a name=".aea.identity.base.Identity.addresses"></a>
#### addresses

```python
 | @property
 | addresses() -> Dict[str, Address]
```

Get the addresses.

<a name=".aea.identity.base.Identity.address"></a>
#### address

```python
 | @property
 | address() -> Address
```

Get the default address.

