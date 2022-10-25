<a id="aea.helpers.cid"></a>

# aea.helpers.cid

Utils to support multiple CID versions.

Original implementation: https://github.com/ipld/py-cid/

<a id="aea.helpers.cid.BaseCID"></a>

## BaseCID Objects

```python
class BaseCID()
```

Base CID object.

<a id="aea.helpers.cid.BaseCID.__init__"></a>

#### `__`init`__`

```python
def __init__(version: int, codec: str, multihash: bytes)
```

Creates a new CID object.

<a id="aea.helpers.cid.BaseCID.version"></a>

#### version

```python
@property
def version() -> int
```

CID version

<a id="aea.helpers.cid.BaseCID.codec"></a>

#### codec

```python
@property
def codec() -> str
```

CID codec

<a id="aea.helpers.cid.BaseCID.multihash"></a>

#### multihash

```python
@property
def multihash() -> bytes
```

CID multihash

<a id="aea.helpers.cid.BaseCID.buffer"></a>

#### buffer

```python
@property
@abstractmethod
def buffer() -> bytes
```

Multihash buffer.

<a id="aea.helpers.cid.BaseCID.encode"></a>

#### encode

```python
@abstractmethod
def encode(encoding: str = DEFAULT_ENCODING) -> bytes
```

Encode multihash.

<a id="aea.helpers.cid.BaseCID.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Object representation.

<a id="aea.helpers.cid.BaseCID.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

String representation.

<a id="aea.helpers.cid.BaseCID.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: object) -> bool
```

Dunder to check object equivalence.

<a id="aea.helpers.cid.CIDv0"></a>

## CIDv0 Objects

```python
class CIDv0(BaseCID)
```

CID version 0 object

<a id="aea.helpers.cid.CIDv0.__init__"></a>

#### `__`init`__`

```python
def __init__(multihash: bytes) -> None
```

Initialize object.

<a id="aea.helpers.cid.CIDv0.buffer"></a>

#### buffer

```python
@property
def buffer() -> bytes
```

The raw representation that will be encoded.

<a id="aea.helpers.cid.CIDv0.encode"></a>

#### encode

```python
def encode(encoding: str = DEFAULT_ENCODING) -> bytes
```

base58-encoded buffer

<a id="aea.helpers.cid.CIDv0.to_v1"></a>

#### to`_`v1

```python
def to_v1() -> "CIDv1"
```

Get an equivalent `CIDv1` object.

<a id="aea.helpers.cid.CIDv1"></a>

## CIDv1 Objects

```python
class CIDv1(BaseCID)
```

CID version 1 object

<a id="aea.helpers.cid.CIDv1.__init__"></a>

#### `__`init`__`

```python
def __init__(codec: str, multihash: bytes) -> None
```

Initialize object.

<a id="aea.helpers.cid.CIDv1.buffer"></a>

#### buffer

```python
@property
def buffer() -> bytes
```

The raw representation of the CID

<a id="aea.helpers.cid.CIDv1.encode"></a>

#### encode

```python
def encode(encoding: str = DEFAULT_ENCODING) -> bytes
```

Encoded version of the raw representation

<a id="aea.helpers.cid.CIDv1.to_v0"></a>

#### to`_`v0

```python
def to_v0() -> CIDv0
```

Get an equivalent `CIDv0` object.

<a id="aea.helpers.cid.CID"></a>

## CID Objects

```python
class CID()
```

CID class.

<a id="aea.helpers.cid.CID.make"></a>

#### make

```python
@classmethod
def make(cls, version: int, codec: str, multihash: bytes) -> CIDObject
```

Make CID from given arguments.

<a id="aea.helpers.cid.CID.is_cid"></a>

#### is`_`cid

```python
@classmethod
def is_cid(cls, cid: str) -> bool
```

Checks if a given input string is valid encoded CID or not.

<a id="aea.helpers.cid.CID.from_string"></a>

#### from`_`string

```python
@classmethod
def from_string(cls, cid: str) -> CIDObject
```

Creates a CID object from a encoded form

<a id="aea.helpers.cid.CID.from_bytes"></a>

#### from`_`bytes

```python
@classmethod
def from_bytes(cls, cid: bytes) -> CIDObject
```

Creates a CID object from a encoded form

<a id="aea.helpers.cid.to_v0"></a>

#### to`_`v0

```python
def to_v0(hash_string: str) -> str
```

Convert CID v1 hash to CID v0

<a id="aea.helpers.cid.to_v1"></a>

#### to`_`v1

```python
def to_v1(hash_string: str, encoding: str = DEFAULT_ENCODING) -> str
```

Convert CID v0 hash to CID v1

