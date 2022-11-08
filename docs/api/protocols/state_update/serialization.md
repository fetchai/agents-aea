<a id="packages.fetchai.protocols.state_update.serialization"></a>

# packages.fetchai.protocols.state`_`update.serialization

Serialization module for state_update protocol.

<a id="packages.fetchai.protocols.state_update.serialization.StateUpdateSerializer"></a>

## StateUpdateSerializer Objects

```python
class StateUpdateSerializer(Serializer)
```

Serialization for the 'state_update' protocol.

<a id="packages.fetchai.protocols.state_update.serialization.StateUpdateSerializer.encode"></a>

#### encode

```python
@staticmethod
def encode(msg: Message) -> bytes
```

Encode a 'StateUpdate' message into bytes.

**Arguments**:

- `msg`: the message object.

**Returns**:

the bytes.

<a id="packages.fetchai.protocols.state_update.serialization.StateUpdateSerializer.decode"></a>

#### decode

```python
@staticmethod
def decode(obj: bytes) -> Message
```

Decode bytes into a 'StateUpdate' message.

**Arguments**:

- `obj`: the bytes object.

**Returns**:

the 'StateUpdate' message.

