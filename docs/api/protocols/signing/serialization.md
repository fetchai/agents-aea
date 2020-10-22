<a name="packages.fetchai.protocols.signing.serialization"></a>
# packages.fetchai.protocols.signing.serialization

Serialization module for signing protocol.

<a name="packages.fetchai.protocols.signing.serialization.SigningSerializer"></a>
## SigningSerializer Objects

```python
class SigningSerializer(Serializer)
```

Serialization for the 'signing' protocol.

<a name="packages.fetchai.protocols.signing.serialization.SigningSerializer.encode"></a>
#### encode

```python
 | @staticmethod
 | encode(msg: Message) -> bytes
```

Encode a 'Signing' message into bytes.

**Arguments**:

- `msg`: the message object.

**Returns**:

the bytes.

<a name="packages.fetchai.protocols.signing.serialization.SigningSerializer.decode"></a>
#### decode

```python
 | @staticmethod
 | decode(obj: bytes) -> Message
```

Decode bytes into a 'Signing' message.

**Arguments**:

- `obj`: the bytes object.

**Returns**:

the 'Signing' message.

