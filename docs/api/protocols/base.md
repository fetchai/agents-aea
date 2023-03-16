<a id="aea.protocols.base"></a>

# aea.protocols.base

This module contains the base message and serialization definition.

<a id="aea.protocols.base.Message"></a>

## Message Objects

```python
class Message()
```

This class implements a message.

<a id="aea.protocols.base.Message.protocol_id"></a>

#### protocol`_`id

type: PublicId

<a id="aea.protocols.base.Message.protocol_specification_id"></a>

#### protocol`_`specification`_`id

type: PublicId

<a id="aea.protocols.base.Message.serializer"></a>

#### serializer

type: Type["Serializer"]

<a id="aea.protocols.base.Message.Performative"></a>

## Performative Objects

```python
class Performative(Enum)
```

Performatives for the base message.

<a id="aea.protocols.base.Message.Performative.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="aea.protocols.base.Message.__init__"></a>

#### `__`init`__`

```python
def __init__(_body: Optional[Dict] = None, **kwargs: Any) -> None
```

Initialize a Message object.

**Arguments**:

- `_body`: the dictionary of values to hold.
- `kwargs`: any additional value to add to the body. It will overwrite the body values.

<a id="aea.protocols.base.Message.json"></a>

#### json

```python
def json() -> dict
```

Get json friendly str representation of the message.

<a id="aea.protocols.base.Message.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, data: dict) -> "Message"
```

Construct message instance from json data.

<a id="aea.protocols.base.Message.valid_performatives"></a>

#### valid`_`performatives

```python
@property
def valid_performatives() -> Set[str]
```

Get valid performatives.

<a id="aea.protocols.base.Message.has_sender"></a>

#### has`_`sender

```python
@property
def has_sender() -> bool
```

Check if it has a sender.

<a id="aea.protocols.base.Message.sender"></a>

#### sender

```python
@property
def sender() -> Address
```

Get the sender of the message in Address form.

<a id="aea.protocols.base.Message.sender"></a>

#### sender

```python
@sender.setter
def sender(sender: Address) -> None
```

Set the sender of the message.

<a id="aea.protocols.base.Message.has_to"></a>

#### has`_`to

```python
@property
def has_to() -> bool
```

Check if it has a sender.

<a id="aea.protocols.base.Message.to"></a>

#### to

```python
@property
def to() -> Address
```

Get address of receiver.

<a id="aea.protocols.base.Message.to"></a>

#### to

```python
@to.setter
def to(to: Address) -> None
```

Set address of receiver.

<a id="aea.protocols.base.Message.dialogue_reference"></a>

#### dialogue`_`reference

```python
@property
def dialogue_reference() -> Tuple[str, str]
```

Get the dialogue_reference of the message.

<a id="aea.protocols.base.Message.message_id"></a>

#### message`_`id

```python
@property
def message_id() -> int
```

Get the message_id of the message.

<a id="aea.protocols.base.Message.performative"></a>

#### performative

```python
@property
def performative() -> "Performative"
```

Get the performative of the message.

<a id="aea.protocols.base.Message.target"></a>

#### target

```python
@property
def target() -> int
```

Get the target of the message.

<a id="aea.protocols.base.Message.set"></a>

#### set

```python
def set(key: str, value: Any) -> None
```

Set key and value pair.

**Arguments**:

- `key`: the key.
- `value`: the value.

<a id="aea.protocols.base.Message.get"></a>

#### get

```python
def get(key: str) -> Optional[Any]
```

Get value for key.

<a id="aea.protocols.base.Message.is_set"></a>

#### is`_`set

```python
def is_set(key: str) -> bool
```

Check value is set for key.

<a id="aea.protocols.base.Message.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Compare with another object.

<a id="aea.protocols.base.Message.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Get the representation of the message.

<a id="aea.protocols.base.Message.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation of the message. Abbreviated to prevent spamming of logs.

<a id="aea.protocols.base.Message.encode"></a>

#### encode

```python
def encode() -> bytes
```

Encode the message.

<a id="aea.protocols.base.Message.decode"></a>

#### decode

```python
@classmethod
def decode(cls, data: bytes) -> "Message"
```

Decode the message.

<a id="aea.protocols.base.Message.has_dialogue_info"></a>

#### has`_`dialogue`_`info

```python
@property
def has_dialogue_info() -> bool
```

Check whether a message has the dialogue fields populated.

More precisely, it checks whether the fields 'message_id',
'target' and 'dialogue_reference' are set.

**Returns**:

True if the message has the dialogue fields set, False otherwise.

<a id="aea.protocols.base.Encoder"></a>

## Encoder Objects

```python
class Encoder(ABC)
```

Encoder interface.

<a id="aea.protocols.base.Encoder.encode"></a>

#### encode

```python
@staticmethod
@abstractmethod
def encode(msg: Message) -> bytes
```

Encode a message.

**Arguments**:

- `msg`: the message to be encoded.

**Returns**:

the encoded message.

<a id="aea.protocols.base.Decoder"></a>

## Decoder Objects

```python
class Decoder(ABC)
```

Decoder interface.

<a id="aea.protocols.base.Decoder.decode"></a>

#### decode

```python
@staticmethod
@abstractmethod
def decode(obj: bytes) -> Message
```

Decode a message.

**Arguments**:

- `obj`: the sequence of bytes to be decoded.

**Returns**:

the decoded message.

<a id="aea.protocols.base.Serializer"></a>

## Serializer Objects

```python
class Serializer(Encoder, Decoder, ABC)
```

The implementations of this class defines a serialization layer for a protocol.

<a id="aea.protocols.base.Protocol"></a>

## Protocol Objects

```python
class Protocol(Component)
```

This class implements a specifications for a protocol.

It includes a serializer to encode/decode a message.

<a id="aea.protocols.base.Protocol.__init__"></a>

#### `__`init`__`

```python
def __init__(configuration: ProtocolConfig, message_class: Type[Message],
             **kwargs: Any) -> None
```

Initialize the protocol manager.

**Arguments**:

- `configuration`: the protocol configurations.
- `message_class`: the message class.
- `kwargs`: the keyword arguments.

<a id="aea.protocols.base.Protocol.serializer"></a>

#### serializer

```python
@property
def serializer() -> Type[Serializer]
```

Get the serializer.

<a id="aea.protocols.base.Protocol.from_dir"></a>

#### from`_`dir

```python
@classmethod
def from_dir(cls, directory: str, **kwargs: Any) -> "Protocol"
```

Load the protocol from a directory.

**Arguments**:

- `directory`: the directory to the skill package.
- `kwargs`: the keyword arguments.

**Returns**:

the protocol object.

<a id="aea.protocols.base.Protocol.from_config"></a>

#### from`_`config

```python
@classmethod
def from_config(cls, configuration: ProtocolConfig,
                **kwargs: Any) -> "Protocol"
```

Load the protocol from configuration.

**Arguments**:

- `configuration`: the protocol configuration.
- `kwargs`: the keyword arguments.

**Returns**:

the protocol object.

<a id="aea.protocols.base.Protocol.protocol_id"></a>

#### protocol`_`id

```python
@property
def protocol_id() -> PublicId
```

Get protocol id.

<a id="aea.protocols.base.Protocol.protocol_specification_id"></a>

#### protocol`_`specification`_`id

```python
@property
def protocol_specification_id() -> PublicId
```

Get protocol specification id.

<a id="aea.protocols.base.Protocol.__repr__"></a>

#### `__`repr`__`

```python
def __repr__() -> str
```

Get str representation of the protocol.

