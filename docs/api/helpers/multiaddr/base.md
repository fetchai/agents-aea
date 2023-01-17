<a id="aea.helpers.multiaddr.base"></a>

# aea.helpers.multiaddr.base

This module contains multiaddress class.

<a id="aea.helpers.multiaddr.base.MultiAddr"></a>

## MultiAddr Objects

```python
class MultiAddr()
```

Protocol Labs' Multiaddress representation of a network address.

<a id="aea.helpers.multiaddr.base.MultiAddr.__init__"></a>

#### `__`init`__`

```python
def __init__(host: str,
             port: int,
             public_key: Optional[str] = None,
             multihash_id: Optional[str] = None) -> None
```

Initialize a multiaddress.

**Arguments**:

- `host`: ip host of the address
- `port`: port number of the address
- `public_key`: hex encoded public key. Must conform to Bitcoin EC encoding standard for Secp256k1
- `multihash_id`: a multihash of the public key

<a id="aea.helpers.multiaddr.base.MultiAddr.compute_peerid"></a>

#### compute`_`peerid

```python
@staticmethod
def compute_peerid(public_key: str) -> str
```

Compute the peer id from a public key.

In particular, compute the base58 representation of
libp2p PeerID from Bitcoin EC encoded Secp256k1 public key.

**Arguments**:

- `public_key`: the public key.

**Returns**:

the peer id.

<a id="aea.helpers.multiaddr.base.MultiAddr.from_string"></a>

#### from`_`string

```python
@classmethod
def from_string(cls, maddr: str) -> "MultiAddr"
```

Construct a MultiAddr object from its string format

**Arguments**:

- `maddr`: multiaddress string

**Returns**:

multiaddress object

<a id="aea.helpers.multiaddr.base.MultiAddr.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> str
```

Get the public key.

<a id="aea.helpers.multiaddr.base.MultiAddr.peer_id"></a>

#### peer`_`id

```python
@property
def peer_id() -> str
```

Get the peer id.

<a id="aea.helpers.multiaddr.base.MultiAddr.host"></a>

#### host

```python
@property
def host() -> str
```

Get the peer host.

<a id="aea.helpers.multiaddr.base.MultiAddr.port"></a>

#### port

```python
@property
def port() -> int
```

Get the peer port.

<a id="aea.helpers.multiaddr.base.MultiAddr.format"></a>

#### format

```python
def format() -> str
```

Canonical representation of a multiaddress.

<a id="aea.helpers.multiaddr.base.MultiAddr.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Default string representation of a multiaddress.

