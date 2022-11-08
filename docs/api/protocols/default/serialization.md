<a id="packages.fetchai.protocols.default.serialization"></a>

# packages.fetchai.protocols.default.serialization

Serialization module for default protocol.

<a id="packages.fetchai.protocols.default.serialization.DefaultSerializer"></a>

## DefaultSerializer Objects

```python
class DefaultSerializer(Serializer)
```

Serialization for the 'default' protocol.

<a id="packages.fetchai.protocols.default.serialization.DefaultSerializer.encode"></a>

#### encode

```python
@staticmethod
def encode(msg: Message) -> bytes
```

Encode a 'Default' message into bytes.

**Arguments**:

- `msg`: the message object.

**Returns**:

the bytes.

<a id="packages.fetchai.protocols.default.serialization.DefaultSerializer.decode"></a>

#### decode

```python
@staticmethod
def decode(obj: bytes) -> Message
```

Decode bytes into a 'Default' message.

**Arguments**:

- `obj`: the bytes object.

**Returns**:

the 'Default' message.

