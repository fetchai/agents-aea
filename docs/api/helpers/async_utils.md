<a name="aea.helpers.async_utils"></a>
# aea.helpers.async`_`utils

This module contains the misc utils for async code.

<a name="aea.helpers.async_utils.ensure_list"></a>
#### ensure`_`list

```python
ensure_list(value: Any) -> List
```

Return [value] or list(value) if value is a sequence.

<a name="aea.helpers.async_utils.AsyncState"></a>
## AsyncState Objects

```python
class AsyncState()
```

Awaitable state.

<a name="aea.helpers.async_utils.AsyncState.__init__"></a>
#### `__`init`__`

```python
 | __init__(initial_state: Any = None)
```

Init async state.

**Arguments**:

- `initial_state`: state to set on start.

<a name="aea.helpers.async_utils.AsyncState.state"></a>
#### state

```python
 | @property
 | state() -> Any
```

Return current state.

<a name="aea.helpers.async_utils.AsyncState.state"></a>
#### state

```python
 | @state.setter
 | state(state: Any) -> None
```

Set state.

<a name="aea.helpers.async_utils.AsyncState.set"></a>
#### set

```python
 | set(state: Any) -> None
```

Set state.

<a name="aea.helpers.async_utils.AsyncState.get"></a>
#### get

```python
 | get() -> Any
```

Get state.

<a name="aea.helpers.async_utils.AsyncState.wait"></a>
#### wait

```python
 | async wait(state_or_states: Union[Any, Sequence[Any]]) -> Tuple[Any, Any]
```

Wait state to be set.

:params state_or_states: state or list of states.

**Returns**:

tuple of previous state and new state.

<a name="aea.helpers.async_utils.PeriodicCaller"></a>
## PeriodicCaller Objects

```python
class PeriodicCaller()
```

Schedule a periodic call of callable using event loop.

Used for periodic function run using asyncio.

<a name="aea.helpers.async_utils.PeriodicCaller.__init__"></a>
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

<a name="aea.helpers.async_utils.PeriodicCaller.start"></a>
#### start

```python
 | start() -> None
```

Activate period calls.

<a name="aea.helpers.async_utils.PeriodicCaller.stop"></a>
#### stop

```python
 | stop() -> None
```

Remove from schedule.

<a name="aea.helpers.async_utils.ensure_loop"></a>
#### ensure`_`loop

```python
ensure_loop(loop: AbstractEventLoop = None) -> AbstractEventLoop
```

Use loop provided or create new if not provided or closed.

Return loop passed if its provided,not closed and not running, otherwise returns new event loop.

**Arguments**:

- `loop`: optional event loop

**Returns**:

asyncio event loop

<a name="aea.helpers.async_utils.AnotherThreadTask"></a>
## AnotherThreadTask Objects

```python
class AnotherThreadTask()
```

Schedule a task to run on the loop in another thread.

Provides better cancel behaviour: on cancel it will wait till cancelled completely.

<a name="aea.helpers.async_utils.AnotherThreadTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(coro: Awaitable, loop: AbstractEventLoop) -> None
```

Init the task.

**Arguments**:

- `coro`: coroutine to schedule
- `loop`: an event loop to schedule on.

<a name="aea.helpers.async_utils.AnotherThreadTask.result"></a>
#### result

```python
 | result(timeout: Optional[float] = None) -> Any
```

Wait for coroutine execution result.

**Arguments**:

- `timeout`: optional timeout to wait in seconds.

<a name="aea.helpers.async_utils.AnotherThreadTask.cancel"></a>
#### cancel

```python
 | cancel() -> None
```

Cancel coroutine task execution in a target loop.

<a name="aea.helpers.async_utils.AnotherThreadTask.future_cancel"></a>
#### future`_`cancel

```python
 | future_cancel() -> None
```

Cancel task waiting future.

In this case future result will raise CanclledError not waiting for real task exit.

<a name="aea.helpers.async_utils.AnotherThreadTask.done"></a>
#### done

```python
 | done() -> bool
```

Check task is done.

<a name="aea.helpers.async_utils.ThreadedAsyncRunner"></a>
## ThreadedAsyncRunner Objects

```python
class ThreadedAsyncRunner(Thread)
```

Util to run thread with event loop and execute coroutines inside.

<a name="aea.helpers.async_utils.ThreadedAsyncRunner.__init__"></a>
#### `__`init`__`

```python
 | __init__(loop=None) -> None
```

Init threaded runner.

**Arguments**:

- `loop`: optional event loop. is it's running loop, threaded runner will use it.

<a name="aea.helpers.async_utils.ThreadedAsyncRunner.start"></a>
#### start

```python
 | start() -> None
```

Start event loop in dedicated thread.

<a name="aea.helpers.async_utils.ThreadedAsyncRunner.run"></a>
#### run

```python
 | run() -> None
```

Run code inside thread.

<a name="aea.helpers.async_utils.ThreadedAsyncRunner.call"></a>
#### call

```python
 | call(coro: Awaitable) -> Any
```

Run a coroutine inside the event loop.

**Arguments**:

- `coro`: a coroutine to run.

<a name="aea.helpers.async_utils.ThreadedAsyncRunner.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop event loop in thread.

<a name="aea.helpers.async_utils.cancel_and_wait"></a>
#### cancel`_`and`_`wait

```python
async cancel_and_wait(task: Optional[Task]) -> Any
```

Wait cancelled task and skip CancelledError.

