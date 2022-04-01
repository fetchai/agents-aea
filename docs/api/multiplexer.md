<a id="aea.multiplexer"></a>

# aea.multiplexer

Module for the multiplexer class and related classes.

<a id="aea.multiplexer.MultiplexerStatus"></a>

## MultiplexerStatus Objects

```python
class MultiplexerStatus(AsyncState)
```

The connection status class.

<a id="aea.multiplexer.MultiplexerStatus.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the connection status.

<a id="aea.multiplexer.MultiplexerStatus.is_connected"></a>

#### is`_`connected

```python
@property
def is_connected() -> bool
```

Return is connected.

<a id="aea.multiplexer.MultiplexerStatus.is_connecting"></a>

#### is`_`connecting

```python
@property
def is_connecting() -> bool
```

Return is connecting.

<a id="aea.multiplexer.MultiplexerStatus.is_disconnected"></a>

#### is`_`disconnected

```python
@property
def is_disconnected() -> bool
```

Return is disconnected.

<a id="aea.multiplexer.MultiplexerStatus.is_disconnecting"></a>

#### is`_`disconnecting

```python
@property
def is_disconnecting() -> bool
```

Return is disconnected.

<a id="aea.multiplexer.AsyncMultiplexer"></a>

## AsyncMultiplexer Objects

```python
class AsyncMultiplexer(Runnable, WithLogger)
```

This class can handle multiple connections at once.

<a id="aea.multiplexer.AsyncMultiplexer.__init__"></a>

#### `__`init`__`

```python
def __init__(
        connections: Optional[Sequence[Connection]] = None,
        default_connection_index: int = 0,
        loop: Optional[AbstractEventLoop] = None,
        exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate,
        threaded: bool = False,
        agent_name: str = "standalone",
        default_routing: Optional[Dict[PublicId, PublicId]] = None,
        default_connection: Optional[PublicId] = None,
        protocols: Optional[List[Union[Protocol, Message]]] = None) -> None
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

<a id="aea.multiplexer.AsyncMultiplexer.default_connection"></a>

#### default`_`connection

```python
@property
def default_connection() -> Optional[Connection]
```

Get the default connection.

<a id="aea.multiplexer.AsyncMultiplexer.in_queue"></a>

#### in`_`queue

```python
@property
def in_queue() -> AsyncFriendlyQueue
```

Get the in queue.

<a id="aea.multiplexer.AsyncMultiplexer.out_queue"></a>

#### out`_`queue

```python
@property
def out_queue() -> asyncio.Queue
```

Get the out queue.

<a id="aea.multiplexer.AsyncMultiplexer.connections"></a>

#### connections

```python
@property
def connections() -> Tuple[Connection, ...]
```

Get the connections.

<a id="aea.multiplexer.AsyncMultiplexer.is_connected"></a>

#### is`_`connected

```python
@property
def is_connected() -> bool
```

Check whether the multiplexer is processing envelopes.

<a id="aea.multiplexer.AsyncMultiplexer.default_routing"></a>

#### default`_`routing

```python
@property
def default_routing() -> Dict[PublicId, PublicId]
```

Get the default routing.

<a id="aea.multiplexer.AsyncMultiplexer.default_routing"></a>

#### default`_`routing

```python
@default_routing.setter
def default_routing(default_routing: Dict[PublicId, PublicId]) -> None
```

Set the default routing.

<a id="aea.multiplexer.AsyncMultiplexer.connection_status"></a>

#### connection`_`status

```python
@property
def connection_status() -> MultiplexerStatus
```

Get the connection status.

<a id="aea.multiplexer.AsyncMultiplexer.run"></a>

#### run

```python
async def run() -> None
```

Run multiplexer connect and receive/send tasks.

<a id="aea.multiplexer.AsyncMultiplexer.set_loop"></a>

#### set`_`loop

```python
def set_loop(loop: AbstractEventLoop) -> None
```

Set event loop and all event loop related objects.

**Arguments**:

- `loop`: asyncio event loop.

<a id="aea.multiplexer.AsyncMultiplexer.add_connection"></a>

#### add`_`connection

```python
def add_connection(connection: Connection, is_default: bool = False) -> None
```

Add a connection to the multiplexer.

**Arguments**:

- `connection`: the connection to add.
- `is_default`: whether the connection added should be the default one.

<a id="aea.multiplexer.AsyncMultiplexer.connect"></a>

#### connect

```python
async def connect() -> None
```

Connect the multiplexer.

<a id="aea.multiplexer.AsyncMultiplexer.disconnect"></a>

#### disconnect

```python
async def disconnect() -> None
```

Disconnect the multiplexer.

<a id="aea.multiplexer.AsyncMultiplexer.get"></a>

#### get

```python
def get(block: bool = False,
        timeout: Optional[float] = None) -> Optional[Envelope]
```

Get an envelope within a timeout.

**Arguments**:

- `block`: make the call blocking (ignore the timeout).
- `timeout`: the timeout to wait until an envelope is received.

**Returns**:

the envelope, or None if no envelope is available within a timeout.

<a id="aea.multiplexer.AsyncMultiplexer.async_get"></a>

#### async`_`get

```python
async def async_get() -> Envelope
```

Get an envelope async way.

**Returns**:

the envelope

<a id="aea.multiplexer.AsyncMultiplexer.async_wait"></a>

#### async`_`wait

```python
async def async_wait() -> None
```

Get an envelope async way.

**Returns**:

the envelope

<a id="aea.multiplexer.AsyncMultiplexer.put"></a>

#### put

```python
def put(envelope: Envelope) -> None
```

Schedule an envelope for sending it.

Notice that the output queue is an asyncio.Queue which uses an event loop
running on a different thread than the one used in this function.

**Arguments**:

- `envelope`: the envelope to be sent.

<a id="aea.multiplexer.Multiplexer"></a>

## Multiplexer Objects

```python
class Multiplexer(AsyncMultiplexer)
```

Transit sync multiplexer for compatibility.

<a id="aea.multiplexer.Multiplexer.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Initialize the connection multiplexer.

**Arguments**:

- `args`: arguments
- `kwargs`: keyword arguments

<a id="aea.multiplexer.Multiplexer.set_loop"></a>

#### set`_`loop

```python
def set_loop(loop: AbstractEventLoop) -> None
```

Set event loop and all event loop related objects.

**Arguments**:

- `loop`: asyncio event loop.

<a id="aea.multiplexer.Multiplexer.connect"></a>

#### connect

```python
def connect() -> None
```

Connect the multiplexer.

Synchronously in thread spawned if new loop created.

<a id="aea.multiplexer.Multiplexer.disconnect"></a>

#### disconnect

```python
def disconnect() -> None
```

Disconnect the multiplexer.

Also stops a dedicated thread for event loop if spawned on connect.

<a id="aea.multiplexer.Multiplexer.put"></a>

#### put

```python
def put(envelope: Envelope) -> None
```

Schedule an envelope for sending it.

Notice that the output queue is an asyncio.Queue which uses an event loop
running on a different thread than the one used in this function.

**Arguments**:

- `envelope`: the envelope to be sent.

<a id="aea.multiplexer.InBox"></a>

## InBox Objects

```python
class InBox()
```

A queue from where you can only consume envelopes.

<a id="aea.multiplexer.InBox.__init__"></a>

#### `__`init`__`

```python
def __init__(multiplexer: AsyncMultiplexer) -> None
```

Initialize the inbox.

**Arguments**:

- `multiplexer`: the multiplexer

<a id="aea.multiplexer.InBox.empty"></a>

#### empty

```python
def empty() -> bool
```

Check for a envelope on the in queue.

**Returns**:

boolean indicating whether there is an envelope or not

<a id="aea.multiplexer.InBox.get"></a>

#### get

```python
def get(block: bool = False, timeout: Optional[float] = None) -> Envelope
```

Check for a envelope on the in queue.

**Arguments**:

- `block`: make the call blocking (ignore the timeout).
- `timeout`: times out the block after timeout seconds.

**Raises**:

- `Empty`: if the attempt to get an envelope fails.

**Returns**:

the envelope object.

<a id="aea.multiplexer.InBox.get_nowait"></a>

#### get`_`nowait

```python
def get_nowait() -> Optional[Envelope]
```

Check for a envelope on the in queue and wait for no time.

**Returns**:

the envelope object

<a id="aea.multiplexer.InBox.async_get"></a>

#### async`_`get

```python
async def async_get() -> Envelope
```

Check for a envelope on the in queue.

**Returns**:

the envelope object.

<a id="aea.multiplexer.InBox.async_wait"></a>

#### async`_`wait

```python
async def async_wait() -> None
```

Check for a envelope on the in queue.

<a id="aea.multiplexer.OutBox"></a>

## OutBox Objects

```python
class OutBox()
```

A queue from where you can only enqueue envelopes.

<a id="aea.multiplexer.OutBox.__init__"></a>

#### `__`init`__`

```python
def __init__(multiplexer: AsyncMultiplexer) -> None
```

Initialize the outbox.

**Arguments**:

- `multiplexer`: the multiplexer

<a id="aea.multiplexer.OutBox.empty"></a>

#### empty

```python
def empty() -> bool
```

Check for a envelope on the in queue.

**Returns**:

boolean indicating whether there is an envelope or not

<a id="aea.multiplexer.OutBox.put"></a>

#### put

```python
def put(envelope: Envelope) -> None
```

Put an envelope into the queue.

**Arguments**:

- `envelope`: the envelope.

<a id="aea.multiplexer.OutBox.put_message"></a>

#### put`_`message

```python
def put_message(message: Message,
                context: Optional[EnvelopeContext] = None) -> None
```

Put a message in the outbox.

This constructs an envelope with the input arguments.

**Arguments**:

- `message`: the message
- `context`: the envelope context

