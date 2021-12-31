<a name="aea.mail.base"></a>
# aea.mail.base

Mail module abstract base classes.

<a name="aea.mail.base.URI"></a>
## URI Objects

```python
class URI()
```

URI following RFC3986.

<a name="aea.mail.base.URI.__init__"></a>
#### `__`init`__`

```python
 | __init__(uri_raw: str) -> None
```

Initialize the URI.

Must follow: https://tools.ietf.org/html/rfc3986.html

**Arguments**:

- `uri_raw`: the raw form uri

<a name="aea.mail.base.URI.scheme"></a>
#### scheme

```python
 | @property
 | scheme() -> str
```

Get the scheme.

<a name="aea.mail.base.URI.netloc"></a>
#### netloc

```python
 | @property
 | netloc() -> str
```

Get the netloc.

<a name="aea.mail.base.URI.path"></a>
#### path

```python
 | @property
 | path() -> str
```

Get the path.

<a name="aea.mail.base.URI.params"></a>
#### params

```python
 | @property
 | params() -> str
```

Get the params.

<a name="aea.mail.base.URI.query"></a>
#### query

```python
 | @property
 | query() -> str
```

Get the query.

<a name="aea.mail.base.URI.fragment"></a>
#### fragment

```python
 | @property
 | fragment() -> str
```

Get the fragment.

<a name="aea.mail.base.URI.username"></a>
#### username

```python
 | @property
 | username() -> Optional[str]
```

Get the username.

<a name="aea.mail.base.URI.password"></a>
#### password

```python
 | @property
 | password() -> Optional[str]
```

Get the password.

<a name="aea.mail.base.URI.host"></a>
#### host

```python
 | @property
 | host() -> Optional[str]
```

Get the host.

<a name="aea.mail.base.URI.port"></a>
#### port

```python
 | @property
 | port() -> Optional[int]
```

Get the port.

<a name="aea.mail.base.URI.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get string representation.

<a name="aea.mail.base.URI.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.mail.base.EnvelopeContext"></a>
## EnvelopeContext Objects

```python
class EnvelopeContext()
```

Contains context information of an envelope.

<a name="aea.mail.base.EnvelopeContext.__init__"></a>
#### `__`init`__`

```python
 | __init__(connection_id: Optional[PublicId] = None, uri: Optional[URI] = None) -> None
```

Initialize the envelope context.

**Arguments**:

- `connection_id`: the connection id used for routing the outgoing envelope in the multiplexer.
- `uri`: the URI sent with the envelope.

<a name="aea.mail.base.EnvelopeContext.uri"></a>
#### uri

```python
 | @property
 | uri() -> Optional[URI]
```

Get the URI.

<a name="aea.mail.base.EnvelopeContext.connection_id"></a>
#### connection`_`id

```python
 | @property
 | connection_id() -> Optional[PublicId]
```

Get the connection id to route the envelope.

<a name="aea.mail.base.EnvelopeContext.connection_id"></a>
#### connection`_`id

```python
 | @connection_id.setter
 | connection_id(connection_id: PublicId) -> None
```

Set the 'via' connection id.

<a name="aea.mail.base.EnvelopeContext.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="aea.mail.base.EnvelopeContext.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.mail.base.AEAConnectionError"></a>
## AEAConnectionError Objects

```python
class AEAConnectionError(Exception)
```

Exception class for connection errors.

<a name="aea.mail.base.Empty"></a>
## Empty Objects

```python
class Empty(Exception)
```

Exception for when the inbox is empty.

<a name="aea.mail.base.EnvelopeSerializer"></a>
## EnvelopeSerializer Objects

```python
class EnvelopeSerializer(ABC)
```

Abstract class to specify the serialization layer for the envelope.

<a name="aea.mail.base.EnvelopeSerializer.encode"></a>
#### encode

```python
 | @abstractmethod
 | encode(envelope: "Envelope") -> bytes
```

Encode the envelope.

**Arguments**:

- `envelope`: the envelope to encode

**Returns**:

the encoded envelope

<a name="aea.mail.base.EnvelopeSerializer.decode"></a>
#### decode

```python
 | @abstractmethod
 | decode(envelope_bytes: bytes) -> "Envelope"
```

Decode the envelope.

**Arguments**:

- `envelope_bytes`: the encoded envelope

**Returns**:

the envelope

<a name="aea.mail.base.ProtobufEnvelopeSerializer"></a>
## ProtobufEnvelopeSerializer Objects

```python
class ProtobufEnvelopeSerializer(EnvelopeSerializer)
```

Envelope serializer using Protobuf.

<a name="aea.mail.base.ProtobufEnvelopeSerializer.encode"></a>
#### encode

```python
 | encode(envelope: "Envelope") -> bytes
```

Encode the envelope.

**Arguments**:

- `envelope`: the envelope to encode

**Returns**:

the encoded envelope

<a name="aea.mail.base.ProtobufEnvelopeSerializer.decode"></a>
#### decode

```python
 | decode(envelope_bytes: bytes) -> "Envelope"
```

Decode the envelope.

The default serializer doesn't decode the message field.

**Arguments**:

- `envelope_bytes`: the encoded envelope

**Returns**:

the envelope

<a name="aea.mail.base.Envelope"></a>
## Envelope Objects

```python
class Envelope()
```

The top level message class for agent to agent communication.

<a name="aea.mail.base.Envelope.__init__"></a>
#### `__`init`__`

```python
 | __init__(to: Address, sender: Address, message: Union[Message, bytes], context: Optional[EnvelopeContext] = None, protocol_specification_id: Optional[PublicId] = None) -> None
```

Initialize a Message object.

**Arguments**:

- `to`: the address of the receiver.
- `sender`: the address of the sender.
- `message`: the protocol-specific message.
- `context`: the optional envelope context.
- `protocol_specification_id`: the protocol specification id (wire id).

<a name="aea.mail.base.Envelope.to"></a>
#### to

```python
 | @property
 | to() -> Address
```

Get address of receiver.

<a name="aea.mail.base.Envelope.to"></a>
#### to

```python
 | @to.setter
 | to(to: Address) -> None
```

Set address of receiver.

<a name="aea.mail.base.Envelope.sender"></a>
#### sender

```python
 | @property
 | sender() -> Address
```

Get address of sender.

<a name="aea.mail.base.Envelope.sender"></a>
#### sender

```python
 | @sender.setter
 | sender(sender: Address) -> None
```

Set address of sender.

<a name="aea.mail.base.Envelope.protocol_specification_id"></a>
#### protocol`_`specification`_`id

```python
 | @property
 | protocol_specification_id() -> PublicId
```

Get protocol_specification_id.

<a name="aea.mail.base.Envelope.message"></a>
#### message

```python
 | @property
 | message() -> Union[Message, bytes]
```

Get the protocol-specific message.

<a name="aea.mail.base.Envelope.message"></a>
#### message

```python
 | @message.setter
 | message(message: Union[Message, bytes]) -> None
```

Set the protocol-specific message.

<a name="aea.mail.base.Envelope.message_bytes"></a>
#### message`_`bytes

```python
 | @property
 | message_bytes() -> bytes
```

Get the protocol-specific message.

<a name="aea.mail.base.Envelope.context"></a>
#### context

```python
 | @property
 | context() -> Optional[EnvelopeContext]
```

Get the envelope context.

<a name="aea.mail.base.Envelope.to_as_public_id"></a>
#### to`_`as`_`public`_`id

```python
 | @property
 | to_as_public_id() -> Optional[PublicId]
```

Get to as public id.

<a name="aea.mail.base.Envelope.is_sender_public_id"></a>
#### is`_`sender`_`public`_`id

```python
 | @property
 | is_sender_public_id() -> bool
```

Check if sender is a public id.

<a name="aea.mail.base.Envelope.is_to_public_id"></a>
#### is`_`to`_`public`_`id

```python
 | @property
 | is_to_public_id() -> bool
```

Check if to is a public id.

<a name="aea.mail.base.Envelope.is_component_to_component_message"></a>
#### is`_`component`_`to`_`component`_`message

```python
 | @property
 | is_component_to_component_message() -> bool
```

Whether or not the message contained is component to component.

<a name="aea.mail.base.Envelope.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other: Any) -> bool
```

Compare with another object.

<a name="aea.mail.base.Envelope.encode"></a>
#### encode

```python
 | encode(serializer: Optional[EnvelopeSerializer] = None) -> bytes
```

Encode the envelope.

**Arguments**:

- `serializer`: the serializer that implements the encoding procedure.

**Returns**:

the encoded envelope.

<a name="aea.mail.base.Envelope.decode"></a>
#### decode

```python
 | @classmethod
 | decode(cls, envelope_bytes: bytes, serializer: Optional[EnvelopeSerializer] = None) -> "Envelope"
```

Decode the envelope.

**Arguments**:

- `envelope_bytes`: the bytes to be decoded.
- `serializer`: the serializer that implements the decoding procedure.

**Returns**:

the decoded envelope.

<a name="aea.mail.base.Envelope.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation of an envelope.

