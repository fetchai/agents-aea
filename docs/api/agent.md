<a name=".aea.agent"></a>
## aea.agent

This module contains the implementation of a generic agent.

<a name=".aea.agent.AgentState"></a>
### AgentState

```python
class AgentState(Enum)
```

Enumeration for an agent state.

In particular, it can be one of the following states:

- AgentState.INITIATED: when the Agent object has been created.
- AgentState.CONNECTED: when the agent is connected.
- AgentState.RUNNING: when the agent is running.

<a name=".aea.agent.Liveness"></a>
### Liveness

```python
class Liveness()
```

Determines the liveness of the agent.

<a name=".aea.agent.Liveness.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate the liveness.

<a name=".aea.agent.Liveness.is_stopped"></a>
#### is`_`stopped

```python
 | @property
 | is_stopped() -> bool
```

Check whether the liveness is stopped.

<a name=".aea.agent.Liveness.start"></a>
#### start

```python
 | start() -> None
```

Start the liveness.

<a name=".aea.agent.Liveness.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop the liveness.

<a name=".aea.agent.Agent"></a>
### Agent

```python
class Agent(ABC)
```

This class provides an abstract base class for a generic agent.

<a name=".aea.agent.Agent.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, connections: List[Connection], loop: Optional[AbstractEventLoop] = None, timeout: float = 1.0, is_debug: bool = False, is_programmatic: bool = True) -> None
```

Instantiate the agent.

**Arguments**:

- `identity`: the identity of the agent.
- `connections`: the list of connections of the agent.
- `loop`: the event loop to run the connections.
- `timeout`: the time in (fractions of) seconds to time out an agent between act and react
- `is_debug`: if True, run the agent in debug mode (does not connect the multiplexer).
- `is_programmatic`: if True, run the agent in programmatic mode (skips loading of resources from directory).

**Returns**:

None

<a name=".aea.agent.Agent.identity"></a>
#### identity

```python
 | @property
 | identity() -> Identity
```

Get the identity.

<a name=".aea.agent.Agent.multiplexer"></a>
#### multiplexer

```python
 | @property
 | multiplexer() -> Multiplexer
```

Get the multiplexer.

<a name=".aea.agent.Agent.inbox"></a>
#### inbox

```python
 | @property
 | inbox() -> InBox
```

Get the inbox.

The inbox contains Envelopes from the Multiplexer.
The agent can pick these messages for processing.

<a name=".aea.agent.Agent.outbox"></a>
#### outbox

```python
 | @property
 | outbox() -> OutBox
```

Get the outbox.

The outbox contains Envelopes for the Multiplexer.
Envelopes placed in the Outbox are processed by the Multiplexer.

<a name=".aea.agent.Agent.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the agent name.

<a name=".aea.agent.Agent.liveness"></a>
#### liveness

```python
 | @property
 | liveness() -> Liveness
```

Get the liveness.

<a name=".aea.agent.Agent.tick"></a>
#### tick

```python
 | @property
 | tick() -> int
```

Get the tick (or agent loop count).

Each agent loop (one call to each one of act(), react(), update()) increments the tick.

<a name=".aea.agent.Agent.agent_state"></a>
#### agent`_`state

```python
 | @property
 | agent_state() -> AgentState
```

Get the state of the agent.

**Raises**:

- `ValueError`: if the state does not satisfy any of the foreseen conditions.

**Returns**:

None

<a name=".aea.agent.Agent.start"></a>
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

<a name=".aea.agent.Agent.stop"></a>
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

<a name=".aea.agent.Agent.setup"></a>
#### setup

```python
 | @abstractmethod
 | setup() -> None
```

Set up the agent.

**Returns**:

None

<a name=".aea.agent.Agent.act"></a>
#### act

```python
 | @abstractmethod
 | act() -> None
```

Perform actions.

**Returns**:

None

<a name=".aea.agent.Agent.react"></a>
#### react

```python
 | @abstractmethod
 | react() -> None
```

React to events.

**Returns**:

None

<a name=".aea.agent.Agent.update"></a>
#### update

```python
 | @abstractmethod
 | update() -> None
```

Update the internal state of the agent.

:return None

<a name=".aea.agent.Agent.teardown"></a>
#### teardown

```python
 | @abstractmethod
 | teardown() -> None
```

Tear down the agent.

**Returns**:

None

