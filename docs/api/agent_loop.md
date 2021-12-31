<a name="aea.agent_loop"></a>
# aea.agent`_`loop

This module contains the implementation of an agent loop using asyncio.

<a name="aea.agent_loop.AgentLoopException"></a>
## AgentLoopException Objects

```python
class AgentLoopException(AEAException)
```

Exception for agent loop runtime errors.

<a name="aea.agent_loop.AgentLoopStates"></a>
## AgentLoopStates Objects

```python
class AgentLoopStates(Enum)
```

Internal agent loop states.

<a name="aea.agent_loop.BaseAgentLoop"></a>
## BaseAgentLoop Objects

```python
class BaseAgentLoop(Runnable,  WithLogger,  ABC)
```

Base abstract  agent loop class.

<a name="aea.agent_loop.BaseAgentLoop.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AbstractAgent, loop: Optional[AbstractEventLoop] = None, threaded: bool = False) -> None
```

Init loop.

**Arguments**:

- `agent`: Agent or AEA to run.
- `loop`: optional asyncio event loop. if not specified a new loop will be created.
- `threaded`: if True, run in threaded mode, else async

<a name="aea.agent_loop.BaseAgentLoop.agent"></a>
#### agent

```python
 | @property
 | agent() -> AbstractAgent
```

Get agent.

<a name="aea.agent_loop.BaseAgentLoop.state"></a>
#### state

```python
 | @property
 | state() -> AgentLoopStates
```

Get current main loop state.

<a name="aea.agent_loop.BaseAgentLoop.wait_state"></a>
#### wait`_`state

```python
 | async wait_state(state_or_states: Union[Any, Sequence[Any]]) -> Tuple[Any, Any]
```

Wait state to be set.

**Arguments**:

- `state_or_states`: state or list of states.

**Returns**:

tuple of previous state and new state.

<a name="aea.agent_loop.BaseAgentLoop.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Get running state of the loop.

<a name="aea.agent_loop.BaseAgentLoop.set_loop"></a>
#### set`_`loop

```python
 | set_loop(loop: AbstractEventLoop) -> None
```

Set event loop and all event loop related objects.

<a name="aea.agent_loop.BaseAgentLoop.run"></a>
#### run

```python
 | async run() -> None
```

Run agent loop.

<a name="aea.agent_loop.BaseAgentLoop.send_to_skill"></a>
#### send`_`to`_`skill

```python
 | @abstractmethod
 | send_to_skill(message_or_envelope: Union[Message, Envelope], context: Optional[EnvelopeContext] = None) -> None
```

Send message or envelope to another skill.

If message passed it will be wrapped into envelope with optional envelope context.

**Arguments**:

- `message_or_envelope`: envelope to send to another skill.
- `context`: envelope context

<a name="aea.agent_loop.BaseAgentLoop.skill2skill_queue"></a>
#### skill2skill`_`queue

```python
 | @property
 | @abstractmethod
 | skill2skill_queue() -> Queue
```

Get skill to skill message queue.

<a name="aea.agent_loop.AsyncAgentLoop"></a>
## AsyncAgentLoop Objects

```python
class AsyncAgentLoop(BaseAgentLoop)
```

Asyncio based agent loop suitable only for AEA.

<a name="aea.agent_loop.AsyncAgentLoop.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AbstractAgent, loop: AbstractEventLoop = None, threaded: bool = False) -> None
```

Init agent loop.

**Arguments**:

- `agent`: AEA instance
- `loop`: asyncio loop to use. optional
- `threaded`: is a new thread to be started for the agent loop

<a name="aea.agent_loop.AsyncAgentLoop.skill2skill_queue"></a>
#### skill2skill`_`queue

```python
 | @property
 | skill2skill_queue() -> Queue
```

Get skill to skill message queue.

<a name="aea.agent_loop.AsyncAgentLoop.send_to_skill"></a>
#### send`_`to`_`skill

```python
 | send_to_skill(message_or_envelope: Union[Message, Envelope], context: Optional[EnvelopeContext] = None) -> None
```

Send message or envelope to another skill.

If message passed it will be wrapped into envelope with optional envelope context.

**Arguments**:

- `message_or_envelope`: envelope to send to another skill.
- `context`: envelope context

