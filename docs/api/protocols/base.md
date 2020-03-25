<a name=".aea.protocols.base"></a>
## aea.protocols.base

This module contains the base message and serialization definition.

<a name=".aea.protocols.base.Message"></a>
### Message

```python
class Message()
```

This class implements a message.

<a name=".aea.protocols.base.Message.__init__"></a>
#### `__`init`__`

```python
 | __init__(body: Optional[Dict] = None, **kwargs)
```

Initialize a Message object.

**Arguments**:

- `body`: the dictionary of values to hold.
- `kwargs`: any additional value to add to the body. It will overwrite the body values.

<a name=".aea.protocols.base.Message.counterparty"></a>
#### counterparty

```python
 | @counterparty.setter
 | counterparty(counterparty: Address) -> None
```

Set the counterparty of the message.

<a name=".aea.protocols.base.Message.body"></a>
#### body

```python
 | @body.setter
 | body(body: Dict) -> None
```

Set the body of hte message.

**Arguments**:

- `body`: the body.

**Returns**:

None

<a name=".aea.protocols.base.Message.set"></a>
#### set

```python
 | set(key: str, value: Any) -> None
```

Set key and value pair.

**Arguments**:

- `key`: the key.
- `value`: the value.

**Returns**:

None

<a name=".aea.protocols.base.Message.get"></a>
#### get

```python
 | get(key: str) -> Optional[Any]
```

Get value for key.

<a name=".aea.protocols.base.Message.unset"></a>
#### unset

```python
 | unset(key: str) -> None
```

Unset valye for key.

<a name=".aea.protocols.base.Message.is_set"></a>
#### is`_`set

```python
 | is_set(key: str) -> bool
```

Check value is set for key.

<a name=".aea.protocols.base.Message.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.protocols.base.Message.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation of the message.

<a name=".aea.protocols.base.Encoder"></a>
### Encoder

```python
class Encoder(ABC)
```

Encoder interface.

<a name=".aea.protocols.base.Encoder.encode"></a>
#### encode

```python
 | @abstractmethod
 | encode(msg: Message) -> bytes
```

Encode a message.

**Arguments**:

- `msg`: the message to be encoded.

**Returns**:

the encoded message.

<a name=".aea.protocols.base.Decoder"></a>
### Decoder

```python
class Decoder(ABC)
```

Decoder interface.

<a name=".aea.protocols.base.Decoder.decode"></a>
#### decode

```python
 | @abstractmethod
 | decode(obj: bytes) -> Message
```

Decode a message.

**Arguments**:

- `obj`: the sequence of bytes to be decoded.

**Returns**:

the decoded message.

<a name=".aea.protocols.base.Serializer"></a>
### Serializer

```python
class Serializer(Encoder,  Decoder,  ABC)
```

The implementations of this class defines a serialization layer for a protocol.

<a name=".aea.protocols.base.ProtobufSerializer"></a>
### ProtobufSerializer

```python
class ProtobufSerializer(Serializer)
```

Default Protobuf serializer.

It assumes that the Message contains a JSON-serializable body.

<a name=".aea.protocols.base.ProtobufSerializer.encode"></a>
#### encode

```python
 | encode(msg: Message) -> bytes
```

Encode a message into bytes using Protobuf.

<a name=".aea.protocols.base.ProtobufSerializer.decode"></a>
#### decode

```python
 | decode(obj: bytes) -> Message
```

Decode bytes into a message using Protobuf.

<a name=".aea.protocols.base.JSONSerializer"></a>
### JSONSerializer

```python
class JSONSerializer(Serializer)
```

Default serialization in JSON for the Message object.

It assumes that the Message contains a JSON-serializable body.

<a name=".aea.protocols.base.JSONSerializer.encode"></a>
#### encode

```python
 | encode(msg: Message) -> bytes
```

Encode a message into bytes using JSON format.

**Arguments**:

- `msg`: the message to be encoded.

**Returns**:

the serialized message.

<a name=".aea.protocols.base.JSONSerializer.decode"></a>
#### decode

```python
 | decode(obj: bytes) -> Message
```

Decode bytes into a message using JSON.

**Arguments**:

- `obj`: the serialized message.

**Returns**:

the decoded message.

<a name=".aea.protocols.base.Protocol"></a>
### Protocol

```python
class Protocol(ABC)
```

This class implements a specifications for a protocol.

It includes a serializer to encode/decode a message.

<a name=".aea.protocols.base.Protocol.__init__"></a>
#### `__`init`__`

```python
 | __init__(protocol_id: ProtocolId, serializer: Serializer, config: ProtocolConfig)
```

Initialize the protocol manager.

**Arguments**:

- `protocol_id`: the protocol id.
- `serializer`: the serializer.
- `config`: the protocol configurations.

<a name=".aea.protocols.base.Protocol.id"></a>
#### id

```python
 | @property
 | id() -> ProtocolId
```

Get the name.

<a name=".aea.protocols.base.Protocol.serializer"></a>
#### serializer

```python
 | @property
 | serializer() -> Serializer
```

Get the serializer.

<a name=".aea.protocols.base.Protocol.config"></a>
#### config

```python
 | @property
 | config() -> ProtocolConfig
```

Get the configuration.

<a name=".aea.protocols.base.Protocol.from_dir"></a>
#### from`_`dir

```python
 | @classmethod
 | from_dir(cls, directory: str) -> "Protocol"
```

Load a protocol from a directory.

**Arguments**:

- `directory`: the skill directory.
- `agent_context`: the agent's context

**Returns**:

the Protocol object.

**Raises**:

- `Exception`: if the parsing failed.

