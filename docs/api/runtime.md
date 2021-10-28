<a name="aea.runtime"></a>
# aea.runtime

This module contains the implementation of runtime for economic agent (AEA).

<a name="aea.runtime.RuntimeStates"></a>
## RuntimeStates Objects

```python
class RuntimeStates(Enum)
```

Runtime states.

<a name="aea.runtime.BaseRuntime"></a>
## BaseRuntime Objects

```python
class BaseRuntime(Runnable,  WithLogger)
```

Abstract runtime class to create implementations.

<a name="aea.runtime.BaseRuntime.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AbstractAgent, multiplexer_options: Dict, loop_mode: Optional[str] = None, loop: Optional[AbstractEventLoop] = None, threaded: bool = False, task_manager_mode: Optional[str] = None) -> None
```

Init runtime.

**Arguments**:

- `agent`: Agent to run.
- `multiplexer_options`: options for the multiplexer.
- `loop_mode`: agent main loop mode.
- `loop`: optional event loop. if not provided a new one will be created.
- `threaded`: if True, run in threaded mode, else async
- `task_manager_mode`: mode of the task manager.

<a name="aea.runtime.BaseRuntime.storage"></a>
#### storage

```python
 | @property
 | storage() -> Optional[Storage]
```

Get optional storage.

<a name="aea.runtime.BaseRuntime.loop_mode"></a>
#### loop`_`mode

```python
 | @property
 | loop_mode() -> str
```

Get current loop mode.

<a name="aea.runtime.BaseRuntime.task_manager"></a>
#### task`_`manager

```python
 | @property
 | task_manager() -> TaskManager
```

Get the task manager.

<a name="aea.runtime.BaseRuntime.loop"></a>
#### loop

```python
 | @property
 | loop() -> Optional[AbstractEventLoop]
```

Get event loop.

<a name="aea.runtime.BaseRuntime.agent_loop"></a>
#### agent`_`loop

```python
 | @property
 | agent_loop() -> BaseAgentLoop
```

Get the agent loop.

<a name="aea.runtime.BaseRuntime.multiplexer"></a>
#### multiplexer

```python
 | @property
 | multiplexer() -> AsyncMultiplexer
```

Get multiplexer.

<a name="aea.runtime.BaseRuntime.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Get running state of the runtime.

<a name="aea.runtime.BaseRuntime.is_stopped"></a>
#### is`_`stopped

```python
 | @property
 | is_stopped() -> bool
```

Get stopped state of the runtime.

<a name="aea.runtime.BaseRuntime.state"></a>
#### state

```python
 | @property
 | state() -> RuntimeStates
```

Get runtime state.

**Returns**:

RuntimeStates

<a name="aea.runtime.BaseRuntime.decision_maker"></a>
#### decision`_`maker

```python
 | @property
 | decision_maker() -> DecisionMaker
```

Return decision maker if set.

<a name="aea.runtime.BaseRuntime.set_decision_maker"></a>
#### set`_`decision`_`maker

```python
 | set_decision_maker(decision_maker_handler: DecisionMakerHandler) -> None
```

Set decision maker with handler provided.

<a name="aea.runtime.BaseRuntime.set_loop"></a>
#### set`_`loop

```python
 | set_loop(loop: AbstractEventLoop) -> None
```

Set event loop to be used.

**Arguments**:

- `loop`: event loop to use.

<a name="aea.runtime.AsyncRuntime"></a>
## AsyncRuntime Objects

```python
class AsyncRuntime(BaseRuntime)
```

Asynchronous runtime: uses asyncio loop for multiplexer and async agent main loop.

<a name="aea.runtime.AsyncRuntime.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AbstractAgent, multiplexer_options: Dict, loop_mode: Optional[str] = None, loop: Optional[AbstractEventLoop] = None, threaded: bool = False, task_manager_mode: Optional[str] = None) -> None
```

Init runtime.

**Arguments**:

- `agent`: Agent to run.
- `multiplexer_options`: options for the multiplexer.
- `loop_mode`: agent main loop mode.
- `loop`: optional event loop. if not provided a new one will be created.
- `threaded`: if True, run in threaded mode, else async
- `task_manager_mode`: mode of the task manager.

<a name="aea.runtime.AsyncRuntime.set_loop"></a>
#### set`_`loop

```python
 | set_loop(loop: AbstractEventLoop) -> None
```

Set event loop to be used.

**Arguments**:

- `loop`: event loop to use.

<a name="aea.runtime.AsyncRuntime.run"></a>
#### run

```python
 | async run() -> None
```

Start runtime task.

Starts multiplexer and agent loop.

<a name="aea.runtime.AsyncRuntime.stop_runtime"></a>
#### stop`_`runtime

```python
 | async stop_runtime() -> None
```

Stop runtime coroutine.

Stop main loop.
Tear down the agent..
Disconnect multiplexer.

<a name="aea.runtime.AsyncRuntime.run_runtime"></a>
#### run`_`runtime

```python
 | async run_runtime() -> None
```

Run runtime which means start agent loop, multiplexer and storage.

<a name="aea.runtime.ThreadedRuntime"></a>
## ThreadedRuntime Objects

```python
class ThreadedRuntime(AsyncRuntime)
```

Run agent and multiplexer in different threads with own asyncio loops.

