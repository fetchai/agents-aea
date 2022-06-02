<a id="packages.open_aea.protocols.signing.serialization"></a>

# packages.open`_`aea.protocols.signing.serialization

Serialization module for signing protocol.

<a id="packages.open_aea.protocols.signing.serialization.SigningSerializer"></a>

## SigningSerializer Objects

```python
class SigningSerializer(Serializer)
```

Serialization for the 'signing' protocol.

<a id="packages.open_aea.protocols.signing.serialization.SigningSerializer.encode"></a>

#### encode

```python
@staticmethod
def encode(msg: Message) -> bytes
```

Encode a 'Signing' message into bytes.

**Arguments**:

- `msg`: the message object.

**Returns**:

the bytes.

<a id="packages.open_aea.protocols.signing.serialization.SigningSerializer.decode"></a>

#### decode

```python
@staticmethod
def decode(obj: bytes) -> Message
```

Decode bytes into a 'Signing' message.

**Arguments**:

- `obj`: the bytes object.

**Returns**:

the 'Signing' message.

