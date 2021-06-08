<a name="aea.multiplexer"></a>
# aea.multiplexer

Module for the multiplexer class and related classes.

<a name="aea.multiplexer.MultiplexerStatus"></a>
## MultiplexerStatus Objects

```python
class MultiplexerStatus(AsyncState)
```

The connection status class.

<a name="aea.multiplexer.MultiplexerStatus.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Initialize the connection status.

<a name="aea.multiplexer.MultiplexerStatus.is_connected"></a>
#### is`_`connected

```python
 | @property
 | is_connected() -> bool
```

Return is connected.

<a name="aea.multiplexer.MultiplexerStatus.is_connecting"></a>
#### is`_`connecting

```python
 | @property
 | is_connecting() -> bool
```

Return is connecting.

<a name="aea.multiplexer.MultiplexerStatus.is_disconnected"></a>
#### is`_`disconnected

```python
 | @property
 | is_disconnected() -> bool
```

Return is disconnected.

<a name="aea.multiplexer.MultiplexerStatus.is_disconnecting"></a>
#### is`_`disconnecting

```python
 | @property
 | is_disconnecting() -> bool
```

Return is disconnected.

<a name="aea.multiplexer.AsyncMultiplexer"></a>
## AsyncMultiplexer Objects

```python
class AsyncMultiplexer(Runnable,  WithLogger)
```

This class can handle multiple connections at once.

<a name="aea.multiplexer.AsyncMultiplexer.__init__"></a>
#### `__`init`__`

```python
 | __init__(connections: Optional[Sequence[Connection]] = None, default_connection_index: int = 0, loop: Optional[AbstractEventLoop] = None, exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate, threaded: bool = False, agent_name: str = "standalone", default_routing: Optional[Dict[PublicId, PublicId]] = None, default_connection: Optional[PublicId] = None, protocols: Optional[List[Union[Protocol, Message]]] = None) -> None
```

Initialize the connection multiplexer.

**Arguments**:

- `connections`: a sequence of connections.
- `default_connection_index`: the index of the connection to use as default.
    This information is used for envelopes which don't specify any routing context.
    If connections is None, this parameter is ignored.
- `loop`: the event loop to run the multiplexer. If None, a new event loop is created.
- `exception_policy`: the exception policy used for connections.
- `threaded`: if True, run in threaded mode, else async
- `agent_name`: the name of the agent that owns the multiplexer, for logging purposes.
- `default_routing`: default routing map
- `default_connection`: default connection
- `protocols`: protocols used

<a name="aea.multiplexer.AsyncMultiplexer.default_connection"></a>
#### default`_`connection

```python
 | @property
 | default_connection() -> Optional[Connection]
```

Get the default connection.

<a name="aea.multiplexer.AsyncMultiplexer.in_queue"></a>
#### in`_`queue

```python
 | @property
 | in_queue() -> AsyncFriendlyQueue
```

Get the in queue.

<a name="aea.multiplexer.AsyncMultiplexer.out_queue"></a>
#### out`_`queue

```python
 | @property
 | out_queue() -> asyncio.Queue
```

Get the out queue.

<a name="aea.multiplexer.AsyncMultiplexer.connections"></a>
#### connections

```python
 | @property
 | connections() -> Tuple[Connection, ...]
```

Get the connections.

<a name="aea.multiplexer.AsyncMultiplexer.is_connected"></a>
#### is`_`connected

```python
 | @property
 | is_connected() -> bool
```

Check whether the multiplexer is processing envelopes.

<a name="aea.multiplexer.AsyncMultiplexer.default_routing"></a>
#### default`_`routing

```python
 | @property
 | default_routing() -> Dict[PublicId, PublicId]
```

Get the default routing.

<a name="aea.multiplexer.AsyncMultiplexer.default_routing"></a>
#### default`_`routing

```python
 | @default_routing.setter
 | default_routing(default_routing: Dict[PublicId, PublicId]) -> None
```

Set the default routing.

<a name="aea.multiplexer.AsyncMultiplexer.connection_status"></a>
#### connection`_`status

```python
 | @property
 | connection_status() -> MultiplexerStatus
```

Get the connection status.

<a name="aea.multiplexer.AsyncMultiplexer.run"></a>
#### run

```python
 | async run() -> None
```

Run multiplexer connect and receive/send tasks.

<a name="aea.multiplexer.AsyncMultiplexer.set_loop"></a>
#### set`_`loop

```python
 | set_loop(loop: AbstractEventLoop) -> None
```

Set event loop and all event loop related objects.

**Arguments**:

- `loop`: asyncio event loop.

<a name="aea.multiplexer.AsyncMultiplexer.add_connection"></a>
#### add`_`connection

```python
 | add_connection(connection: Connection, is_default: bool = False) -> None
```

Add a connection to the multiplexer.

**Arguments**:

- `connection`: the connection to add.
- `is_default`: whether the connection added should be the default one.

<a name="aea.multiplexer.AsyncMultiplexer.connect"></a>
#### connect

```python
 | async connect() -> None
```

Connect the multiplexer.

<a name="aea.multiplexer.AsyncMultiplexer.disconnect"></a>
#### disconnect

```python
 | async disconnect() -> None
```

Disconnect the multiplexer.

<a name="aea.multiplexer.AsyncMultiplexer.get"></a>
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

<a name="aea.multiplexer.AsyncMultiplexer.async_get"></a>
#### async`_`get

```python
 | async async_get() -> Envelope
```

Get an envelope async way.

**Returns**:

the envelope

<a name="aea.multiplexer.AsyncMultiplexer.async_wait"></a>
#### async`_`wait

```python
 | async async_wait() -> None
```

Get an envelope async way.

**Returns**:

the envelope

<a name="aea.multiplexer.AsyncMultiplexer.put"></a>
#### put

```python
 | put(envelope: Envelope) -> None
```

Schedule an envelope for sending it.

Notice that the output queue is an asyncio.Queue which uses an event loop
running on a different thread than the one used in this function.

**Arguments**:

- `envelope`: the envelope to be sent.

<a name="aea.multiplexer.Multiplexer"></a>
## Multiplexer Objects

```python
class Multiplexer(AsyncMultiplexer)
```

Transit sync multiplexer for compatibility.

<a name="aea.multiplexer.Multiplexer.__init__"></a>
#### `__`init`__`

```python
 | __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the connection multiplexer.

**Arguments**:

- `args`: arguments
- `kwargs`: keyword arguments

<a name="aea.multiplexer.Multiplexer.set_loop"></a>
#### set`_`loop

```python
 | set_loop(loop: AbstractEventLoop) -> None
```

Set event loop and all event loop related objects.

**Arguments**:

- `loop`: asyncio event loop.

<a name="aea.multiplexer.Multiplexer.connect"></a>
#### connect

```python
 | connect() -> None
```

Connect the multiplexer.

Synchronously in thread spawned if new loop created.

<a name="aea.multiplexer.Multiplexer.disconnect"></a>
#### disconnect

```python
 | disconnect() -> None
```

Disconnect the multiplexer.

Also stops a dedicated thread for event loop if spawned on connect.

<a name="aea.multiplexer.Multiplexer.put"></a>
#### put

```python
 | put(envelope: Envelope) -> None
```

Schedule an envelope for sending it.

Notice that the output queue is an asyncio.Queue which uses an event loop
running on a different thread than the one used in this function.

**Arguments**:

- `envelope`: the envelope to be sent.

<a name="aea.multiplexer.InBox"></a>
## InBox Objects

```python
class InBox()
```

A queue from where you can only consume envelopes.

<a name="aea.multiplexer.InBox.__init__"></a>
#### `__`init`__`

```python
 | __init__(multiplexer: AsyncMultiplexer) -> None
```

Initialize the inbox.

**Arguments**:

- `multiplexer`: the multiplexer

<a name="aea.multiplexer.InBox.empty"></a>
#### empty

```python
 | empty() -> bool
```

Check for a envelope on the in queue.

**Returns**:

boolean indicating whether there is an envelope or not

<a name="aea.multiplexer.InBox.get"></a>
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

- `Empty`: if the attempt to get an envelope fails.

<a name="aea.multiplexer.InBox.get_nowait"></a>
#### get`_`nowait

```python
 | get_nowait() -> Optional[Envelope]
```

Check for a envelope on the in queue and wait for no time.

**Returns**:

the envelope object

<a name="aea.multiplexer.InBox.async_get"></a>
#### async`_`get

```python
 | async async_get() -> Envelope
```

Check for a envelope on the in queue.

**Returns**:

the envelope object.

<a name="aea.multiplexer.InBox.async_wait"></a>
#### async`_`wait

```python
 | async async_wait() -> None
```

Check for a envelope on the in queue.

<a name="aea.multiplexer.OutBox"></a>
## OutBox Objects

```python
class OutBox()
```

A queue from where you can only enqueue envelopes.

<a name="aea.multiplexer.OutBox.__init__"></a>
#### `__`init`__`

```python
 | __init__(multiplexer: AsyncMultiplexer) -> None
```

Initialize the outbox.

**Arguments**:

- `multiplexer`: the multiplexer

<a name="aea.multiplexer.OutBox.empty"></a>
#### empty

```python
 | empty() -> bool
```

Check for a envelope on the in queue.

**Returns**:

boolean indicating whether there is an envelope or not

<a name="aea.multiplexer.OutBox.put"></a>
#### put

```python
 | put(envelope: Envelope) -> None
```

Put an envelope into the queue.

**Arguments**:

- `envelope`: the envelope.

<a name="aea.multiplexer.OutBox.put_message"></a>
#### put`_`message

```python
 | put_message(message: Message, context: Optional[EnvelopeContext] = None) -> None
```

Put a message in the outbox.

This constructs an envelope with the input arguments.

**Arguments**:

- `message`: the message
- `context`: the envelope context

