<a name=".aea.agent_loop"></a>
## aea.agent`_`loop

This module contains the implementation of an agent loop using asyncio.

<a name=".aea.agent_loop.ensure_list"></a>
#### ensure`_`list

```python
ensure_list(value: Any) -> List
```

Return [value] or list(value) if value is a sequence.

<a name=".aea.agent_loop.AsyncState"></a>
### AsyncState

```python
class AsyncState()
```

Awaitable state.

<a name=".aea.agent_loop.AsyncState.__init__"></a>
#### `__`init`__`

```python
 | __init__(initial_state: Any = None, loop: AbstractEventLoop = None)
```

Init async state.

**Arguments**:

- `initial_state`: state to set on start.
- `loop`: optional asyncio event loop.

<a name=".aea.agent_loop.AsyncState.state"></a>
#### state

```python
 | @state.setter
 | state(state: Any) -> None
```

Set state.

<a name=".aea.agent_loop.AsyncState.wait"></a>
#### wait

```python
 | async wait(state_or_states: Union[Any, Sequence[Any]]) -> Tuple[Any, Any]
```

Wait state to be set.

:params state_or_states: state or list of states.

**Returns**:

tuple of previous state and new state.

<a name=".aea.agent_loop.PeriodicCaller"></a>
### PeriodicCaller

```python
class PeriodicCaller()
```

Schedule a periodic call of callable using event loop.

<a name=".aea.agent_loop.PeriodicCaller.__init__"></a>
#### `__`init`__`

```python
 | __init__(callback: Callable, period: float, start_at: Optional[datetime.datetime] = None, exception_callback: Optional[Callable[[Callable, Exception], None]] = None, loop: Optional[AbstractEventLoop] = None)
```

Init periodic caller.

**Arguments**:

- `callback`: function to call periodically
- `period`: period in seconds.
- `start_at`: optional first call datetime
- `exception_callback`: optional handler to call on exception raised.
- `loop`: optional asyncio event loop

<a name=".aea.agent_loop.PeriodicCaller.start"></a>
#### start

```python
 | start() -> None
```

Activate period calls.

<a name=".aea.agent_loop.PeriodicCaller.stop"></a>
#### stop

```python
 | stop() -> None
```

Remove from schedule.

<a name=".aea.agent_loop.BaseAgentLoop"></a>
### BaseAgentLoop

```python
class BaseAgentLoop(ABC)
```

Base abstract  agent loop class.

<a name=".aea.agent_loop.BaseAgentLoop.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: "Agent") -> None
```

Init loop.

:params agent: Agent or AEA to run.

<a name=".aea.agent_loop.BaseAgentLoop.start"></a>
#### start

```python
 | @abstractmethod
 | start() -> None
```

Start agent loop.

<a name=".aea.agent_loop.BaseAgentLoop.stop"></a>
#### stop

```python
 | @abstractmethod
 | stop() -> None
```

Stop agent loop.

<a name=".aea.agent_loop.AgentLoopException"></a>
### AgentLoopException

```python
class AgentLoopException(AEAException)
```

Exception for agent loop runtime errors.

<a name=".aea.agent_loop.AgentLoopStates"></a>
### AgentLoopStates

```python
class AgentLoopStates(Enum)
```

Internal agent loop states.

<a name=".aea.agent_loop.AsyncAgentLoop"></a>
### AsyncAgentLoop

```python
class AsyncAgentLoop(BaseAgentLoop)
```

Asyncio based agent loop suitable only for AEA.

<a name=".aea.agent_loop.AsyncAgentLoop.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: "AEA", loop: AbstractEventLoop = None)
```

Init agent loop.

**Arguments**:

- `agent`: AEA instance
- `loop`: asyncio loop to use. optional

<a name=".aea.agent_loop.AsyncAgentLoop.start"></a>
#### start

```python
 | start()
```

Start agent loop.

<a name=".aea.agent_loop.AsyncAgentLoop.stop"></a>
#### stop

```python
 | stop()
```

Stop agent loop.

<a name=".aea.agent_loop.AsyncAgentLoop.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Get running state of the loop.

<a name=".aea.agent_loop.SyncAgentLoop"></a>
### SyncAgentLoop

```python
class SyncAgentLoop(BaseAgentLoop)
```

Synchronous agent loop.

<a name=".aea.agent_loop.SyncAgentLoop.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: "Agent") -> None
```

Init agent loop.

**Arguments**:

- `agent`: agent or AEA instance.

<a name=".aea.agent_loop.SyncAgentLoop.start"></a>
#### start

```python
 | start() -> None
```

Start agent loop.

<a name=".aea.agent_loop.SyncAgentLoop.stop"></a>
#### stop

```python
 | stop()
```

Stop agent loop.

