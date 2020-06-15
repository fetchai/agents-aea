<a name=".aea.runtime"></a>
# aea.runtime

This module contains the implementation of runtime for economic agent (AEA).

<a name=".aea.runtime.RuntimeStates"></a>
## RuntimeStates Objects

```python
class RuntimeStates(Enum)
```

Runtime states.

<a name=".aea.runtime.BaseRuntime"></a>
## BaseRuntime Objects

```python
class BaseRuntime(ABC)
```

Abstract runtime class to create implementations.

<a name=".aea.runtime.BaseRuntime.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: "Agent", loop: Optional[AbstractEventLoop] = None) -> None
```

Init runtime.

**Arguments**:

- `agent`: Agent to run.
- `loop`: optional event loop. if not provided a new one will be created.

**Returns**:

None

<a name=".aea.runtime.BaseRuntime.start"></a>
#### start

```python
 | start() -> None
```

Start agent using runtime.

<a name=".aea.runtime.BaseRuntime.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop agent and runtime.

<a name=".aea.runtime.BaseRuntime.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Get running state of the runtime.

<a name=".aea.runtime.BaseRuntime.is_stopped"></a>
#### is`_`stopped

```python
 | @property
 | is_stopped() -> bool
```

Get stopped state of the runtime.

<a name=".aea.runtime.BaseRuntime.set_loop"></a>
#### set`_`loop

```python
 | set_loop(loop: AbstractEventLoop) -> None
```

Set event loop to be used.

**Arguments**:

- `loop`: event loop to use.

<a name=".aea.runtime.AsyncRuntime"></a>
## AsyncRuntime Objects

```python
class AsyncRuntime(BaseRuntime)
```

Asynchronous runtime: uses asyncio loop for multiplexer and async agent main loop.

<a name=".aea.runtime.AsyncRuntime.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: "Agent", loop: Optional[AbstractEventLoop] = None) -> None
```

Init runtime.

**Arguments**:

- `agent`: Agent to run.
- `loop`: optional event loop. if not provided a new one will be created.

**Returns**:

None

<a name=".aea.runtime.AsyncRuntime.set_loop"></a>
#### set`_`loop

```python
 | set_loop(loop: AbstractEventLoop) -> None
```

Set event loop to be used.

**Arguments**:

- `loop`: event loop to use.

<a name=".aea.runtime.AsyncRuntime.run_runtime"></a>
#### run`_`runtime

```python
 | async run_runtime() -> None
```

Run agent and starts multiplexer.

<a name=".aea.runtime.ThreadedRuntime"></a>
## ThreadedRuntime Objects

```python
class ThreadedRuntime(BaseRuntime)
```

Run agent and multiplexer in different threads with own asyncio loops.

