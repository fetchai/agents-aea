<a name="aea.protocols.base"></a>
# aea.protocols.base

This module contains the base message and serialization definition.

<a name="aea.protocols.base.Message"></a>
## Message Objects

```python
class Message()
```

This class implements a message.

<a name="aea.protocols.base.Message.Performative"></a>
## Performative Objects

```python
class Performative(Enum)
```

Performatives for the base message.

<a name="aea.protocols.base.Message.Performative.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="aea.protocols.base.Message.__init__"></a>
#### `__`init`__`

```python
 | __init__(_body: Optional[Dict] = None, **kwargs: Any) -> None
```

Initialize a Message object.

**Arguments**:

- `_body`: the dictionary of values to hold.
- `kwargs`: any additional value to add to the body. It will overwrite the body values.

<a name="aea.protocols.base.Message.json"></a>
#### json

```python
 | json() -> dict
```

Get json friendly str representation of the message.

<a name="aea.protocols.base.Message.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, data: dict) -> "Message"
```

Construct message instance from json data.

<a name="aea.protocols.base.Message.valid_performatives"></a>
#### valid`_`performatives

```python
 | @property
 | valid_performatives() -> Set[str]
```

Get valid performatives.

<a name="aea.protocols.base.Message.has_sender"></a>
#### has`_`sender

```python
 | @property
 | has_sender() -> bool
```

Check if it has a sender.

<a name="aea.protocols.base.Message.sender"></a>
#### sender

```python
 | @property
 | sender() -> Address
```

Get the sender of the message in Address form.

<a name="aea.protocols.base.Message.sender"></a>
#### sender

```python
 | @sender.setter
 | sender(sender: Address) -> None
```

Set the sender of the message.

<a name="aea.protocols.base.Message.has_to"></a>
#### has`_`to

```python
 | @property
 | has_to() -> bool
```

Check if it has a sender.

<a name="aea.protocols.base.Message.to"></a>
#### to

```python
 | @property
 | to() -> Address
```

Get address of receiver.

<a name="aea.protocols.base.Message.to"></a>
#### to

```python
 | @to.setter
 | to(to: Address) -> None
```

Set address of receiver.

<a name="aea.protocols.base.Message.dialogue_reference"></a>
#### dialogue`_`reference

```python
 | @property
 | dialogue_reference() -> Tuple[str, str]
```

Get the dialogue_reference of the message.

<a name="aea.protocols.base.Message.message_id"></a>
#### message`_`id

```python
 | @property
 | message_id() -> int
```

Get the message_id of the message.

<a name="aea.protocols.base.Message.performative"></a>
#### performative

```python
 | @property
 | performative() -> "Performative"
```

Get the performative of the message.

<a name="aea.protocols.base.Message.target"></a>
#### target

```python
 | @property
 | target() -> int
```

Get the target of the message.

<a name="aea.protocols.base.Message.set"></a>
#### set

```python
 | set(key: str, value: Any) -> None
```

Set key and value pair.

**Arguments**:

- `key`: the key.
- `value`: the value.

<a name="aea.protocols.base.Message.get"></a>
#### get

```python
 | get(key: str) -> Optional[Any]
```

Get value for key.

<a name="aea.protocols.base.Message.is_set"></a>
#### is`_`set

```python
 | is_set(key: str) -> bool
```

Check value is set for key.

<a name="aea.protocols.base.Message.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.protocols.base.Message.__repr__"></a>
#### `__`repr`__`

```python
 | __repr__() -> str
```

Get the representation of the message.

<a name="aea.protocols.base.Message.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of the message. Abbreviated to prevent spamming of logs.

<a name="aea.protocols.base.Message.encode"></a>
#### encode

```python
 | encode() -> bytes
```

Encode the message.

<a name="aea.protocols.base.Message.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, data: bytes) -> "Message"
```

Decode the message.

<a name="aea.protocols.base.Message.has_dialogue_info"></a>
#### has`_`dialogue`_`info

```python
 | @property
 | has_dialogue_info() -> bool
```

Check whether a message has the dialogue fields populated.

More precisely, it checks whether the fields 'message_id',
'target' and 'dialogue_reference' are set.

**Returns**:

True if the message has the dialogue fields set, False otherwise.

<a name="aea.protocols.base.Encoder"></a>
## Encoder Objects

```python
class Encoder(ABC)
```

Encoder interface.

<a name="aea.protocols.base.Encoder.encode"></a>
#### encode

```python
 | @staticmethod
 | @abstractmethod
 | encode(msg: Message) -> bytes
```

Encode a message.

**Arguments**:

- `msg`: the message to be encoded.

**Returns**:

the encoded message.

<a name="aea.protocols.base.Decoder"></a>
## Decoder Objects

```python
class Decoder(ABC)
```

Decoder interface.

<a name="aea.protocols.base.Decoder.decode"></a>
#### decode

```python
 | @staticmethod
 | @abstractmethod
 | decode(obj: bytes) -> Message
```

Decode a message.

**Arguments**:

- `obj`: the sequence of bytes to be decoded.

**Returns**:

the decoded message.

<a name="aea.protocols.base.Serializer"></a>
## Serializer Objects

```python
class Serializer(Encoder,  Decoder,  ABC)
```

The implementations of this class defines a serialization layer for a protocol.

<a name="aea.protocols.base.Protocol"></a>
## Protocol Objects

```python
class Protocol(Component)
```

This class implements a specifications for a protocol.

It includes a serializer to encode/decode a message.

<a name="aea.protocols.base.Protocol.__init__"></a>
#### `__`init`__`

```python
 | __init__(configuration: ProtocolConfig, message_class: Type[Message], **kwargs: Any) -> None
```

Initialize the protocol manager.

**Arguments**:

- `configuration`: the protocol configurations.
- `message_class`: the message class.
- `kwargs`: the keyword arguments.

<a name="aea.protocols.base.Protocol.serializer"></a>
#### serializer

```python
 | @property
 | serializer() -> Type[Serializer]
```

Get the serializer.

<a name="aea.protocols.base.Protocol.from_dir"></a>
#### from`_`dir

```python
 | @classmethod
 | from_dir(cls, directory: str, **kwargs: Any) -> "Protocol"
```

Load the protocol from a directory.

**Arguments**:

- `directory`: the directory to the skill package.
- `kwargs`: the keyword arguments.

**Returns**:

the protocol object.

<a name="aea.protocols.base.Protocol.from_config"></a>
#### from`_`config

```python
 | @classmethod
 | from_config(cls, configuration: ProtocolConfig, **kwargs: Any) -> "Protocol"
```

Load the protocol from configuration.

**Arguments**:

- `configuration`: the protocol configuration.
- `kwargs`: the keyword arguments.

**Returns**:

the protocol object.

<a name="aea.protocols.base.Protocol.protocol_id"></a>
#### protocol`_`id

```python
 | @property
 | protocol_id() -> PublicId
```

Get protocol id.

<a name="aea.protocols.base.Protocol.protocol_specification_id"></a>
#### protocol`_`specification`_`id

```python
 | @property
 | protocol_specification_id() -> PublicId
```

Get protocol specification id.

<a name="aea.protocols.base.Protocol.__repr__"></a>
#### `__`repr`__`

```python
 | __repr__() -> str
```

Get str representation of the protocol.

