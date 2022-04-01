<a id="aea.helpers.transaction.base"></a>

# aea.helpers.transaction.base

This module contains terms related classes.

<a id="aea.helpers.transaction.base.RawTransaction"></a>

## RawTransaction Objects

```python
class RawTransaction()
```

This class represents an instance of RawTransaction.

<a id="aea.helpers.transaction.base.RawTransaction.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_id: str, body: JSONLike) -> None
```

Initialise an instance of RawTransaction.

<a id="aea.helpers.transaction.base.RawTransaction.ledger_id"></a>

#### ledger`_`id

```python
@property
def ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a id="aea.helpers.transaction.base.RawTransaction.body"></a>

#### body

```python
@property
def body() -> JSONLike
```

Get the body.

<a id="aea.helpers.transaction.base.RawTransaction.encode"></a>

#### encode

```python
@staticmethod
def encode(raw_transaction_protobuf_object: Any,
           raw_transaction_object: "RawTransaction") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the raw_transaction_protobuf_object argument must be matched with the instance of this class in the 'raw_transaction_object' argument.

**Arguments**:

- `raw_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `raw_transaction_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="aea.helpers.transaction.base.RawTransaction.decode"></a>

#### decode

```python
@classmethod
def decode(cls, raw_transaction_protobuf_object: Any) -> "RawTransaction"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

**Arguments**:

- `raw_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

<a id="aea.helpers.transaction.base.RawTransaction.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.helpers.transaction.base.RawTransaction.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation.

<a id="aea.helpers.transaction.base.RawMessage"></a>

## RawMessage Objects

```python
class RawMessage()
```

This class represents an instance of RawMessage.

<a id="aea.helpers.transaction.base.RawMessage.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_id: str,
             body: bytes,
             is_deprecated_mode: bool = False) -> None
```

Initialise an instance of RawMessage.

<a id="aea.helpers.transaction.base.RawMessage.ledger_id"></a>

#### ledger`_`id

```python
@property
def ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a id="aea.helpers.transaction.base.RawMessage.body"></a>

#### body

```python
@property
def body() -> bytes
```

Get the body.

<a id="aea.helpers.transaction.base.RawMessage.is_deprecated_mode"></a>

#### is`_`deprecated`_`mode

```python
@property
def is_deprecated_mode() -> bool
```

Get the is_deprecated_mode.

<a id="aea.helpers.transaction.base.RawMessage.encode"></a>

#### encode

```python
@staticmethod
def encode(raw_message_protobuf_object: Any,
           raw_message_object: "RawMessage") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the raw_message_protobuf_object argument must be matched with the instance of this class in the 'raw_message_object' argument.

**Arguments**:

- `raw_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `raw_message_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="aea.helpers.transaction.base.RawMessage.decode"></a>

#### decode

```python
@classmethod
def decode(cls, raw_message_protobuf_object: Any) -> "RawMessage"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.

**Arguments**:

- `raw_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.

<a id="aea.helpers.transaction.base.RawMessage.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.helpers.transaction.base.RawMessage.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation.

<a id="aea.helpers.transaction.base.SignedTransaction"></a>

## SignedTransaction Objects

```python
class SignedTransaction()
```

This class represents an instance of SignedTransaction.

<a id="aea.helpers.transaction.base.SignedTransaction.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_id: str, body: JSONLike) -> None
```

Initialise an instance of SignedTransaction.

<a id="aea.helpers.transaction.base.SignedTransaction.ledger_id"></a>

#### ledger`_`id

```python
@property
def ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a id="aea.helpers.transaction.base.SignedTransaction.body"></a>

#### body

```python
@property
def body() -> JSONLike
```

Get the body.

<a id="aea.helpers.transaction.base.SignedTransaction.encode"></a>

#### encode

```python
@staticmethod
def encode(signed_transaction_protobuf_object: Any,
           signed_transaction_object: "SignedTransaction") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the signed_transaction_protobuf_object argument must be matched with the instance of this class in the 'signed_transaction_object' argument.

**Arguments**:

- `signed_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `signed_transaction_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="aea.helpers.transaction.base.SignedTransaction.decode"></a>

#### decode

```python
@classmethod
def decode(cls,
           signed_transaction_protobuf_object: Any) -> "SignedTransaction"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.

**Arguments**:

- `signed_transaction_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.

<a id="aea.helpers.transaction.base.SignedTransaction.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.helpers.transaction.base.SignedTransaction.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation.

<a id="aea.helpers.transaction.base.SignedMessage"></a>

## SignedMessage Objects

```python
class SignedMessage()
```

This class represents an instance of RawMessage.

<a id="aea.helpers.transaction.base.SignedMessage.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_id: str,
             body: str,
             is_deprecated_mode: bool = False) -> None
```

Initialise an instance of SignedMessage.

<a id="aea.helpers.transaction.base.SignedMessage.ledger_id"></a>

#### ledger`_`id

```python
@property
def ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a id="aea.helpers.transaction.base.SignedMessage.body"></a>

#### body

```python
@property
def body() -> str
```

Get the body.

<a id="aea.helpers.transaction.base.SignedMessage.is_deprecated_mode"></a>

#### is`_`deprecated`_`mode

```python
@property
def is_deprecated_mode() -> bool
```

Get the is_deprecated_mode.

<a id="aea.helpers.transaction.base.SignedMessage.encode"></a>

#### encode

```python
@staticmethod
def encode(signed_message_protobuf_object: Any,
           signed_message_object: "SignedMessage") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the signed_message_protobuf_object argument must be matched with the instance of this class in the 'signed_message_object' argument.

**Arguments**:

- `signed_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `signed_message_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="aea.helpers.transaction.base.SignedMessage.decode"></a>

#### decode

```python
@classmethod
def decode(cls, signed_message_protobuf_object: Any) -> "SignedMessage"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.

**Arguments**:

- `signed_message_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.

<a id="aea.helpers.transaction.base.SignedMessage.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.helpers.transaction.base.SignedMessage.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation.

<a id="aea.helpers.transaction.base.State"></a>

## State Objects

```python
class State()
```

This class represents an instance of State.

<a id="aea.helpers.transaction.base.State.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_id: str, body: JSONLike) -> None
```

Initialise an instance of State.

<a id="aea.helpers.transaction.base.State.ledger_id"></a>

#### ledger`_`id

```python
@property
def ledger_id() -> str
```

Get the id of the ledger on which the terms are to be settled.

<a id="aea.helpers.transaction.base.State.body"></a>

#### body

```python
@property
def body() -> JSONLike
```

Get the body.

<a id="aea.helpers.transaction.base.State.encode"></a>

#### encode

```python
@staticmethod
def encode(state_protobuf_object: Any, state_object: "State") -> None
```

Encode an instance of this class into the protocol buffer object.

The protocol buffer object in the state_protobuf_object argument must be matched with the instance of this class in the 'state_object' argument.

**Arguments**:

- `state_protobuf_object`: the protocol buffer object whose type corresponds with this class.
- `state_object`: an instance of this class to be encoded in the protocol buffer object.

<a id="aea.helpers.transaction.base.State.decode"></a>

#### decode

```python
@classmethod
def decode(cls, state_protobuf_object: Any) -> "State"
```

Decode a protocol buffer object that corresponds with this class into an instance of this class.

A new instance of this class must be created that matches the protocol buffer object in the 'state_protobuf_object' argument.

**Arguments**:

- `state_protobuf_object`: the protocol buffer object whose type corresponds with this class.

**Returns**:

A new instance of this class that matches the protocol buffer object in the 'state_protobuf_object' argument.

<a id="aea.helpers.transaction.base.State.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check equality.

<a id="aea.helpers.transaction.base.State.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get string representation.

<a id="aea.helpers.transaction.base.Terms"></a>

## Terms Objects

```python
class Terms()
```

Class to represent the terms of a multi-currency & multi-token ledger transaction.

<a id="aea.helpers.transaction.base.Terms.__init__"></a>

#### `__`init`__`

