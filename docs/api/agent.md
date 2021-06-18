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
 | __init__(identity: Identity, connections: List[Connection], loop: Optional[AbstractEventLoop] = None, period: float = 1.0, loop_mode: Optional[str] = None, runtime_mode: Optional[str] = None, storage_uri: Optional[str] = None, logger: Logger = _default_logger, task_manager_mode: Optional[str] = None) -> None
```

Instantiate the agent.

**Arguments**:

- `identity`: the identity of the agent.
- `connections`: the list of connections of the agent.
- `loop`: the event loop to run the connections.
- `period`: period to call agent's act
- `loop_mode`: loop_mode to choose agent run loop.
- `runtime_mode`: runtime mode to up agent.
- `storage_uri`: optional uri to set generic storage
- `task_manager_mode`: task manager mode.
- `logger`: the logger.
- `task_manager_mode`: mode of the task manager.

<a name="aea.agent.Agent.storage_uri"></a>
#### storage`_`uri

```python
 | @property
 | storage_uri() -> Optional[str]
```

Return storage uri.

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

**Returns**:

InBox instance

<a name="aea.agent.Agent.outbox"></a>
#### outbox

```python
 | @property
 | outbox() -> OutBox
```

Get the outbox.

The outbox contains Envelopes for the Multiplexer.
Envelopes placed in the Outbox are processed by the Multiplexer.

**Returns**:

OutBox instance

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

**Returns**:

tick count

<a name="aea.agent.Agent.state"></a>
#### state

```python
 | @property
 | state() -> RuntimeStates
```

Get state of the agent's runtime.

**Returns**:

RuntimeStates

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

<a name="aea.agent.Agent.setup"></a>
#### setup

```python
 | setup() -> None
```

Set up the agent.

<a name="aea.agent.Agent.start"></a>
#### start

```python
 | start() -> None
```

Start the agent.

Performs the following:

- calls start() on runtime.
- waits for runtime to complete running (blocking)

<a name="aea.agent.Agent.handle_envelope"></a>
#### handle`_`envelope

```python
 | handle_envelope(envelope: Envelope) -> None
```

Handle an envelope.

**Arguments**:

- `envelope`: the envelope to handle.

<a name="aea.agent.Agent.act"></a>
#### act

```python
 | act() -> None
```

Perform actions on period.

<a name="aea.agent.Agent.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop the agent.

Performs the following:

- calls stop() on runtime
- waits for runtime to stop (blocking)

<a name="aea.agent.Agent.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Tear down the agent.

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

