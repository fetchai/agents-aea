<a id="aea.runtime"></a>

# aea.runtime

This module contains the implementation of runtime for economic agent (AEA).

<a id="aea.runtime.RuntimeStates"></a>

## RuntimeStates Objects

```python
class RuntimeStates(Enum)
```

Runtime states.

<a id="aea.runtime.BaseRuntime"></a>

## BaseRuntime Objects

```python
class BaseRuntime(Runnable, WithLogger)
```

Abstract runtime class to create implementations.

<a id="aea.runtime.BaseRuntime.__init__"></a>

#### `__`init`__`

```python
def __init__(agent: AbstractAgent,
             multiplexer_options: Dict,
             loop_mode: Optional[str] = None,
             loop: Optional[AbstractEventLoop] = None,
             threaded: bool = False,
             task_manager_mode: Optional[str] = None) -> None
```

Init runtime.

**Arguments**:

- `agent`: Agent to run.
- `multiplexer_options`: options for the multiplexer.
- `loop_mode`: agent main loop mode.
- `loop`: optional event loop. if not provided a new one will be created.
- `threaded`: if True, run in threaded mode, else async
- `task_manager_mode`: mode of the task manager.

<a id="aea.runtime.BaseRuntime.storage"></a>

#### storage

```python
@property
def storage() -> Optional[Storage]
```

Get optional storage.

<a id="aea.runtime.BaseRuntime.loop_mode"></a>

#### loop`_`mode

```python
@property
def loop_mode() -> str
```

Get current loop mode.

<a id="aea.runtime.BaseRuntime.task_manager"></a>

#### task`_`manager

```python
@property
def task_manager() -> TaskManager
```

Get the task manager.

<a id="aea.runtime.BaseRuntime.loop"></a>

#### loop

```python
@property
def loop() -> Optional[AbstractEventLoop]
```

Get event loop.

<a id="aea.runtime.BaseRuntime.agent_loop"></a>

#### agent`_`loop

```python
@property
def agent_loop() -> BaseAgentLoop
```

Get the agent loop.

<a id="aea.runtime.BaseRuntime.multiplexer"></a>

#### multiplexer

```python
@property
def multiplexer() -> AsyncMultiplexer
```

Get multiplexer.

<a id="aea.runtime.BaseRuntime.is_running"></a>

#### is`_`running

```python
@property
def is_running() -> bool
```

Get running state of the runtime.

<a id="aea.runtime.BaseRuntime.is_stopped"></a>

#### is`_`stopped

```python
@property
def is_stopped() -> bool
```

Get stopped state of the runtime.

<a id="aea.runtime.BaseRuntime.state"></a>

#### state

```python
@property
def state() -> RuntimeStates
```

Get runtime state.

**Returns**:

RuntimeStates

<a id="aea.runtime.BaseRuntime.decision_maker"></a>

#### decision`_`maker

```python
@property
def decision_maker() -> DecisionMaker
```

Return decision maker if set.

<a id="aea.runtime.BaseRuntime.set_decision_maker"></a>

#### set`_`decision`_`maker

```python
def set_decision_maker(decision_maker_handler: DecisionMakerHandler) -> None
```

Set decision maker with handler provided.

<a id="aea.runtime.BaseRuntime.set_loop"></a>

#### set`_`loop

```python
def set_loop(loop: AbstractEventLoop) -> None
```

Set event loop to be used.

**Arguments**:

- `loop`: event loop to use.

<a id="aea.runtime.AsyncRuntime"></a>

## AsyncRuntime Objects

```python
class AsyncRuntime(BaseRuntime)
```

Asynchronous runtime: uses asyncio loop for multiplexer and async agent main loop.

<a id="aea.runtime.AsyncRuntime.__init__"></a>

#### `__`init`__`

```python
def __init__(agent: AbstractAgent,
             multiplexer_options: Dict,
             loop_mode: Optional[str] = None,
             loop: Optional[AbstractEventLoop] = None,
             threaded: bool = False,
             task_manager_mode: Optional[str] = None) -> None
```

Init runtime.

**Arguments**:

- `agent`: Agent to run.
- `multiplexer_options`: options for the multiplexer.
- `loop_mode`: agent main loop mode.
- `loop`: optional event loop. if not provided a new one will be created.
- `threaded`: if True, run in threaded mode, else async
- `task_manager_mode`: mode of the task manager.

<a id="aea.runtime.AsyncRuntime.set_loop"></a>

#### set`_`loop

```python
def set_loop(loop: AbstractEventLoop) -> None
```

Set event loop to be used.

**Arguments**:

- `loop`: event loop to use.

<a id="aea.runtime.AsyncRuntime.run"></a>

#### run

```python
async def run() -> None
```

Start runtime task.

Starts multiplexer and agent loop.

<a id="aea.runtime.AsyncRuntime.stop_runtime"></a>

#### stop`_`runtime

```python
async def stop_runtime() -> None
```

Stop runtime coroutine.

Stop main loop.
Tear down the agent..
Disconnect multiplexer.

<a id="aea.runtime.AsyncRuntime.run_runtime"></a>

#### run`_`runtime

```python
async def run_runtime() -> None
```

Run runtime which means start agent loop, multiplexer and storage.

<a id="aea.runtime.ThreadedRuntime"></a>

## ThreadedRuntime Objects

```python
class ThreadedRuntime(AsyncRuntime)
```

Run agent and multiplexer in different threads with own asyncio loops.

