<a id="aea.helpers.acn.uri"></a>

# aea.helpers.acn.uri

This module contains types and helpers for libp2p connections Uris.

<a id="aea.helpers.acn.uri.Uri"></a>

## Uri Objects

```python
class Uri()
```

Holds a node address in format "host:port".

<a id="aea.helpers.acn.uri.Uri.__init__"></a>

#### `__`init`__`

```python
def __init__(uri: Optional[str] = None,
             host: Optional[str] = None,
             port: Optional[int] = None) -> None
```

Initialise Uri.

<a id="aea.helpers.acn.uri.Uri.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation.

<a id="aea.helpers.acn.uri.Uri.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Get object representation.

<a id="aea.helpers.acn.uri.Uri.host"></a>

#### host

```python
@property
def host() -> str
```

Get host.

<a id="aea.helpers.acn.uri.Uri.port"></a>

#### port

```python
@property
def port() -> int
```

Get port.

