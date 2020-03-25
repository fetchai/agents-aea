<a name=".aea.mail.base"></a>
## aea.mail.base

Mail module abstract base classes.

<a name=".aea.mail.base.AEAConnectionError"></a>
### AEAConnectionError

```python
class AEAConnectionError(Exception)
```

Exception class for connection errors.

<a name=".aea.mail.base.Empty"></a>
### Empty

```python
class Empty(Exception)
```

Exception for when the inbox is empty.

<a name=".aea.mail.base.URI"></a>
### URI

```python
class URI()
```

URI following RFC3986.

<a name=".aea.mail.base.URI.__init__"></a>
#### `__`init`__`

```python
 | __init__(uri_raw: str)
```

Initialize the URI.

**Arguments**:

- `uri_raw`: the raw form uri

**Raises**:

- `ValueError`: if uri_raw is not RFC3986 compliant

<a name=".aea.mail.base.URI.scheme"></a>
#### scheme

```python
 | @property
 | scheme() -> str
```

Get the scheme.

<a name=".aea.mail.base.URI.netloc"></a>
#### netloc

```python
 | @property
 | netloc() -> str
```

Get the netloc.

<a name=".aea.mail.base.URI.path"></a>
#### path

```python
 | @property
 | path() -> str
```

Get the path.

<a name=".aea.mail.base.URI.params"></a>
#### params

```python
 | @property
 | params() -> str
```

Get the params.

<a name=".aea.mail.base.URI.query"></a>
#### query

```python
 | @property
 | query() -> str
```

Get the query.

<a name=".aea.mail.base.URI.fragment"></a>
#### fragment

```python
 | @property
 | fragment() -> str
```

Get the fragment.

<a name=".aea.mail.base.URI.username"></a>
#### username

```python
 | @property
 | username() -> Optional[str]
```

Get the username.

<a name=".aea.mail.base.URI.password"></a>
#### password

```python
 | @property
 | password() -> Optional[str]
```

Get the password.

<a name=".aea.mail.base.URI.host"></a>
#### host

```python
 | @property
 | host() -> Optional[str]
```

Get the host.

<a name=".aea.mail.base.URI.port"></a>
#### port

```python
 | @property
 | port() -> Optional[int]
```

Get the port.

<a name=".aea.mail.base.URI.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get string representation.

<a name=".aea.mail.base.URI.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.mail.base.EnvelopeContext"></a>
### EnvelopeContext

```python
class EnvelopeContext()
```

Extra information for the handling of an envelope.

<a name=".aea.mail.base.EnvelopeContext.__init__"></a>
#### `__`init`__`

```python
 | __init__(connection_id: Optional[PublicId] = None, uri: Optional[URI] = None)
```

Initialize the envelope context.

<a name=".aea.mail.base.EnvelopeContext.uri_raw"></a>
#### uri`_`raw

```python
 | @property
 | uri_raw() -> str
```

Get uri in string format.

<a name=".aea.mail.base.EnvelopeContext.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.mail.base.EnvelopeSerializer"></a>
### EnvelopeSerializer

```python
class EnvelopeSerializer(ABC)
```

This abstract class let the devloper to specify serialization layer for the envelope.

<a name=".aea.mail.base.EnvelopeSerializer.encode"></a>
#### encode

```python
 | @abstractmethod
 | encode(envelope: "Envelope") -> bytes
```

Encode the envelope.

<a name=".aea.mail.base.EnvelopeSerializer.decode"></a>
#### decode

```python
 | @abstractmethod
 | decode(envelope_bytes: bytes) -> "Envelope"
```

Decode the envelope.

<a name=".aea.mail.base.ProtobufEnvelopeSerializer"></a>
### ProtobufEnvelopeSerializer

```python
class ProtobufEnvelopeSerializer(EnvelopeSerializer)
```

Envelope serializer using Protobuf.

<a name=".aea.mail.base.ProtobufEnvelopeSerializer.encode"></a>
#### encode

```python
 | encode(envelope: "Envelope") -> bytes
```

Encode the envelope.

<a name=".aea.mail.base.ProtobufEnvelopeSerializer.decode"></a>
#### decode

```python
 | decode(envelope_bytes: bytes) -> "Envelope"
```

Decode the envelope.

<a name=".aea.mail.base.Envelope"></a>
### Envelope

```python
class Envelope()
```

The top level message class.

<a name=".aea.mail.base.Envelope.__init__"></a>
#### `__`init`__`

```python
 | __init__(to: Address, sender: Address, protocol_id: ProtocolId, message: bytes, context: Optional[EnvelopeContext] = None)
```

Initialize a Message object.

**Arguments**:

- `to`: the address of the receiver.
- `sender`: the address of the sender.
- `protocol_id`: the protocol id.
- `message`: the protocol-specific message

<a name=".aea.mail.base.Envelope.to"></a>
#### to

```python
 | @to.setter
 | to(to: Address) -> None
```

Set address of receiver.

<a name=".aea.mail.base.Envelope.sender"></a>
#### sender

```python
 | @sender.setter
 | sender(sender: Address) -> None
```

Set address of sender.

<a name=".aea.mail.base.Envelope.protocol_id"></a>
#### protocol`_`id

```python
 | @protocol_id.setter
 | protocol_id(protocol_id: ProtocolId) -> None
```

Set the protocol id.

<a name=".aea.mail.base.Envelope.message"></a>
#### message

```python
 | @message.setter
 | message(message: bytes) -> None
```

Set the message.

<a name=".aea.mail.base.Envelope.context"></a>
#### context

```python
 | @property
 | context() -> Optional[EnvelopeContext]
```

Get the envelope context.

<a name=".aea.mail.base.Envelope.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other)
```

Compare with another object.

<a name=".aea.mail.base.Envelope.encode"></a>
#### encode

```python
 | encode(serializer: Optional[EnvelopeSerializer] = None) -> bytes
```

Encode the envelope.

**Arguments**:

- `serializer`: the serializer that implements the encoding procedure.

**Returns**:

the encoded envelope.

<a name=".aea.mail.base.Envelope.decode"></a>
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

<a name=".aea.mail.base.Envelope.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation of an envelope.

<a name=".aea.mail.base.Multiplexer"></a>
### Multiplexer

```python
class Multiplexer()
```

This class can handle multiple connections at once.

<a name=".aea.mail.base.Multiplexer.__init__"></a>
#### `__`init`__`

```python
 | __init__(connections: Sequence["Connection"], default_connection_index: int = 0, loop: Optional[AbstractEventLoop] = None)
```

Initialize the connection multiplexer.

**Arguments**:

- `connections`: a sequence of connections.
- `default_connection_index`: the index of the connection to use as default.
| this information is used for envelopes which
| don't specify any routing context.
- `loop`: the event loop to run the multiplexer. If None, a new event loop is created.

<a name=".aea.mail.base.Multiplexer.in_queue"></a>
#### in`_`queue

```python
 | @property
 | in_queue() -> queue.Queue
```

Get the in queue.

<a name=".aea.mail.base.Multiplexer.out_queue"></a>
#### out`_`queue

```python
 | @property
 | out_queue() -> asyncio.Queue
```

Get the out queue.

<a name=".aea.mail.base.Multiplexer.connections"></a>
#### connections

```python
 | @property
 | connections() -> Tuple["Connection"]
```

Get the connections.

<a name=".aea.mail.base.Multiplexer.is_connected"></a>
#### is`_`connected

```python
 | @property
 | is_connected() -> bool
```

Check whether the multiplexer is processing messages.

<a name=".aea.mail.base.Multiplexer.connection_status"></a>
#### connection`_`status

```python
 | @property
 | connection_status() -> ConnectionStatus
```

Get the connection status.

<a name=".aea.mail.base.Multiplexer.connect"></a>
#### connect

```python
 | connect() -> None
```

Connect the multiplexer.

<a name=".aea.mail.base.Multiplexer.disconnect"></a>
#### disconnect

```python
 | disconnect() -> None
```

Disconnect the multiplexer.

<a name=".aea.mail.base.Multiplexer.get"></a>
#### get

```python
 | get(block: bool = False, timeout: Optional[float] = None) -> Optional[Envelope]
```

Get an envelope within a timeout.

**Arguments**:

- `block`: make the call blocking (ignore the timeout).
- `timeout`: the timeout to wait until an envelope is received.

**Returns**:

the envelope, or None if no envelope is available within a timeout.

<a name=".aea.mail.base.Multiplexer.put"></a>
#### put

```python
 | put(envelope: Envelope) -> None
```

Schedule an envelope for sending it.

Notice that the output queue is an asyncio.Queue which uses an event loop
running on a different thread than the one used in this function.

**Arguments**:

- `envelope`: the envelope to be sent.

**Returns**:

None

<a name=".aea.mail.base.InBox"></a>
### InBox

```python
class InBox()
```

A queue from where you can only consume messages.

<a name=".aea.mail.base.InBox.__init__"></a>
#### `__`init`__`

```python
 | __init__(multiplexer: Multiplexer)
```

Initialize the inbox.

**Arguments**:

- `multiplexer`: the multiplexer

<a name=".aea.mail.base.InBox.empty"></a>
#### empty

```python
 | empty() -> bool
```

Check for a envelope on the in queue.

**Returns**:

boolean indicating whether there is a message or not

<a name=".aea.mail.base.InBox.get"></a>
#### get

```python
 | get(block: bool = False, timeout: Optional[float] = None) -> Envelope
```

Check for a envelope on the in queue.

**Arguments**:

- `block`: make the call blocking (ignore the timeout).
- `timeout`: times out the block after timeout seconds.

**Returns**:

the envelope object.

**Raises**:

- `Empty`: if the attempt to get a message fails.

<a name=".aea.mail.base.InBox.get_nowait"></a>
#### get`_`nowait

```python
 | get_nowait() -> Optional[Envelope]
```

Check for a envelope on the in queue and wait for no time.

**Returns**:

the envelope object

<a name=".aea.mail.base.OutBox"></a>
### OutBox

```python
class OutBox()
```

A queue from where you can only enqueue messages.

<a name=".aea.mail.base.OutBox.__init__"></a>
#### `__`init`__`

```python
 | __init__(multiplexer: Multiplexer)
```

Initialize the outbox.

**Arguments**:

- `multiplexer`: the multiplexer

<a name=".aea.mail.base.OutBox.empty"></a>
#### empty

```python
 | empty() -> bool
```

Check for a envelope on the in queue.

**Returns**:

boolean indicating whether there is a message or not

<a name=".aea.mail.base.OutBox.put"></a>
#### put

```python
 | put(envelope: Envelope) -> None
```

Put an envelope into the queue.

**Arguments**:

- `envelope`: the envelope.

**Returns**:

None

<a name=".aea.mail.base.OutBox.put_message"></a>
#### put`_`message

```python
 | put_message(to: Address, sender: Address, protocol_id: ProtocolId, message: bytes) -> None
```

Put a message in the outbox.

**Arguments**:

- `to`: the recipient of the message.
- `sender`: the sender of the message.
- `protocol_id`: the protocol id.
- `message`: the content of the message.

**Returns**:

None

