<a name="aea.agent"></a>
# aea.agent

This module contains the implementation of a generic agent.

<a name="aea.agent.Agent"></a>
## Agent Objects

```python
class Agent(AbstractAgent,  WithLogger)
```

This class provides an abstract base class for a generic agent.

<a name="aea.agent.Agent.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, connections: List[Connection], loop: Optional[AbstractEventLoop] = None, period: float = 1.0, loop_mode: Optional[str] = None, runtime_mode: Optional[str] = None, logger: Logger = _default_logger) -> None
```

Instantiate the agent.

**Arguments**:

- `identity`: the identity of the agent.
- `connections`: the list of connections of the agent.
- `loop`: the event loop to run the connections.
- `period`: period to call agent's act
- `loop_mode`: loop_mode to choose agent run loop.
- `runtime_mode`: runtime mode to up agent.

**Returns**:

None

<a name="aea.agent.Agent.connections"></a>
#### connections

```python
 | @property
 | connections() -> List[Connection]
```

Return list of connections.

<a name="aea.agent.Agent.active_connections"></a>
#### active`_`connections

```python
 | @property
 | active_connections() -> List[Connection]
```

Return list of active connections.

<a name="aea.agent.Agent.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Get running state of the runtime and agent.

<a name="aea.agent.Agent.is_stopped"></a>
#### is`_`stopped

```python
 | @property
 | is_stopped() -> bool
```

Get running state of the runtime and agent.

<a name="aea.agent.Agent.get_multiplexer_setup_options"></a>
#### get`_`multiplexer`_`setup`_`options

```python
 | get_multiplexer_setup_options() -> Optional[Dict]
```

Get options to pass to Multiplexer.setup.

**Returns**:

dict of kwargs

<a name="aea.agent.Agent.identity"></a>
#### identity

```python
 | @property
 | identity() -> Identity
```

Get the identity.

<a name="aea.agent.Agent.inbox"></a>
#### inbox

```python
 | @property
 | inbox() -> InBox
```

Get the inbox.

The inbox contains Envelopes from the Multiplexer.
The agent can pick these messages for processing.

<a name="aea.agent.Agent.outbox"></a>
#### outbox

```python
 | @property
 | outbox() -> OutBox
```

Get the outbox.

The outbox contains Envelopes for the Multiplexer.
Envelopes placed in the Outbox are processed by the Multiplexer.

<a name="aea.agent.Agent.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the agent name.

<a name="aea.agent.Agent.tick"></a>
#### tick

```python
 | @property
 | tick() -> int
```

Get the tick or agent loop count.

Each agent loop (one call to each one of act(), react(), update()) increments the tick.

<a name="aea.agent.Agent.handle_envelope"></a>
#### handle`_`envelope

```python
 | handle_envelope(envelope: Envelope) -> None
```

Handle an envelope.

**Arguments**:

- `envelope`: the envelope to handle.

**Returns**:

None

<a name="aea.agent.Agent.period"></a>
#### period

```python
 | @property
 | period() -> float
```

Get a period to call act.

<a name="aea.agent.Agent.runtime"></a>
#### runtime

```python
 | @property
 | runtime() -> BaseRuntime
```

Get the runtime.

<a name="aea.agent.Agent.start"></a>
#### start

```python
 | start() -> None
```

Start the agent.

Performs the following:

- calls connect() on the multiplexer (unless in debug mode), and
- calls setup(), and
- calls start() on the liveness, and
- enters the agent main loop.

While the liveness of the agent is not stopped it continues to loop over:

- increment the tick,
- call to act(),
- sleep for specified timeout,
- call to react(),
- call to update().

**Returns**:

None

<a name="aea.agent.Agent.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop the agent.

Performs the following:

- calls stop() on the liveness, and
- calls teardown(), and
- calls disconnect() on the multiplexer.

**Returns**:

None

<a name="aea.agent.Agent.state"></a>
#### state

```python
 | @property
 | state() -> RuntimeStates
```

Get state of the agent's runtime.

**Returns**:

RuntimeStates

<a name="aea.agent.Agent.get_periodic_tasks"></a>
#### get`_`periodic`_`tasks

```python
 | get_periodic_tasks() -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]
```

Get all periodic tasks for agent.

**Returns**:

dict of callable with period specified

<a name="aea.agent.Agent.get_message_handlers"></a>
#### get`_`message`_`handlers

```python
 | get_message_handlers() -> List[Tuple[Callable[[Any], None], Callable]]
```

Get handlers with message getters.

**Returns**:

List of tuples of callables: handler and coroutine to get a message

<a name="aea.agent.Agent.exception_handler"></a>
#### exception`_`handler

```python
 | exception_handler(exception: Exception, function: Callable) -> bool
```

Handle exception raised during agent main loop execution.

**Arguments**:

- `exception`: exception raised
- `function`: a callable exception raised in.

**Returns**:

bool, propagate exception if True otherwise skip it.

