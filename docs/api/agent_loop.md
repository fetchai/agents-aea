<a id="aea.agent_loop"></a>

# aea.agent`_`loop

This module contains the implementation of an agent loop using asyncio.

<a id="aea.agent_loop.AgentLoopException"></a>

## AgentLoopException Objects

```python
class AgentLoopException(AEAException)
```

Exception for agent loop runtime errors.

<a id="aea.agent_loop.AgentLoopStates"></a>

## AgentLoopStates Objects

```python
class AgentLoopStates(Enum)
```

Internal agent loop states.

<a id="aea.agent_loop.BaseAgentLoop"></a>

## BaseAgentLoop Objects

```python
class BaseAgentLoop(Runnable, WithLogger, ABC)
```

Base abstract  agent loop class.

<a id="aea.agent_loop.BaseAgentLoop.__init__"></a>

#### `__`init`__`

```python
def __init__(agent: AbstractAgent,
             loop: Optional[AbstractEventLoop] = None,
             threaded: bool = False) -> None
```

Init loop.

**Arguments**:

- `agent`: Agent or AEA to run.
- `loop`: optional asyncio event loop. if not specified a new loop will be created.
- `threaded`: if True, run in threaded mode, else async

<a id="aea.agent_loop.BaseAgentLoop.agent"></a>

#### agent

```python
@property
def agent() -> AbstractAgent
```

Get agent.

<a id="aea.agent_loop.BaseAgentLoop.state"></a>

#### state

```python
@property
def state() -> AgentLoopStates
```

Get current main loop state.

<a id="aea.agent_loop.BaseAgentLoop.wait_state"></a>

#### wait`_`state

```python
async def wait_state(
        state_or_states: Union[Any, Sequence[Any]]) -> Tuple[Any, Any]
```

Wait state to be set.

**Arguments**:

- `state_or_states`: state or list of states.

**Returns**:

tuple of previous state and new state.

<a id="aea.agent_loop.BaseAgentLoop.is_running"></a>

#### is`_`running

```python
@property
def is_running() -> bool
```

Get running state of the loop.

<a id="aea.agent_loop.BaseAgentLoop.set_loop"></a>

#### set`_`loop

```python
def set_loop(loop: AbstractEventLoop) -> None
```

Set event loop and all event loop related objects.

<a id="aea.agent_loop.BaseAgentLoop.run"></a>

#### run

```python
async def run() -> None
```

Run agent loop.

<a id="aea.agent_loop.BaseAgentLoop.send_to_skill"></a>

#### send`_`to`_`skill

```python
@abstractmethod
def send_to_skill(message_or_envelope: Union[Message, Envelope],
                  context: Optional[EnvelopeContext] = None) -> None
```

Send message or envelope to another skill.

If message passed it will be wrapped into envelope with optional envelope context.

**Arguments**:

- `message_or_envelope`: envelope to send to another skill.
- `context`: envelope context

<a id="aea.agent_loop.BaseAgentLoop.skill2skill_queue"></a>

#### skill2skill`_`queue

```python
@property
@abstractmethod
def skill2skill_queue() -> Queue
```

Get skill to skill message queue.

<a id="aea.agent_loop.AsyncAgentLoop"></a>

## AsyncAgentLoop Objects

```python
class AsyncAgentLoop(BaseAgentLoop)
```

Asyncio based agent loop suitable only for AEA.

<a id="aea.agent_loop.AsyncAgentLoop.NEW_BEHAVIOURS_PROCESS_SLEEP"></a>

#### NEW`_`BEHAVIOURS`_`PROCESS`_`SLEEP

check new behaviours registered every second.

<a id="aea.agent_loop.AsyncAgentLoop.__init__"></a>

#### `__`init`__`

```python
def __init__(agent: AbstractAgent,
             loop: Optional[AbstractEventLoop] = None,
             threaded: bool = False) -> None
```

Init agent loop.

**Arguments**:

- `agent`: AEA instance
- `loop`: asyncio loop to use. optional
- `threaded`: is a new thread to be started for the agent loop

<a id="aea.agent_loop.AsyncAgentLoop.skill2skill_queue"></a>

#### skill2skill`_`queue

```python
@property
def skill2skill_queue() -> Queue
```

Get skill to skill message queue.

<a id="aea.agent_loop.AsyncAgentLoop.send_to_skill"></a>

#### send`_`to`_`skill

```python
def send_to_skill(message_or_envelope: Union[Message, Envelope],
                  context: Optional[EnvelopeContext] = None) -> None
```

Send message or envelope to another skill.

If message passed it will be wrapped into envelope with optional envelope context.

**Arguments**:

- `message_or_envelope`: envelope to send to another skill.
- `context`: envelope context

<a id="aea.agent_loop.SyncAgentLoop"></a>

#### SyncAgentLoop

temporary solution!

