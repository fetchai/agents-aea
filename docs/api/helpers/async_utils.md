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
 | __init__(initial_state: Any = None, states_enum: Optional[Container[Any]] = None) -> None
```

Init async state.

**Arguments**:

- `initial_state`: state to set on start.
- `states_enum`: container of valid states if not provided state not checked on set.

<a name="aea.helpers.async_utils.AsyncState.set"></a>
#### set

```python
 | set(state: Any) -> None
```

Set state.

<a name="aea.helpers.async_utils.AsyncState.add_callback"></a>
#### add`_`callback

```python
 | add_callback(callback_fn: Callable[[Any], None]) -> None
```

Add callback to track state changes.

**Arguments**:

- `callback_fn`: callable object to be called on state changed.

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

**Arguments**:

- `state_or_states`: state or list of states.

**Returns**:

tuple of previous state and new state.

<a name="aea.helpers.async_utils.AsyncState.transit"></a>
#### transit

```python
 | @contextmanager
 | transit(initial: Any = not_set, success: Any = not_set, fail: Any = not_set) -> Generator
```

Change state context according to success or not.

**Arguments**:

- `initial`: set state on context enter, not_set by default
- `success`: set state on context block done, not_set by default
- `fail`: set state on context block raises exception, not_set by default
:yield: generator

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
 | __init__(callback: Callable, period: float, start_at: Optional[datetime.datetime] = None, exception_callback: Optional[Callable[[Callable, Exception], None]] = None, loop: Optional[AbstractEventLoop] = None) -> None
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

**Returns**:

result

<a name="aea.helpers.async_utils.AnotherThreadTask.cancel"></a>
#### cancel

```python
 | cancel() -> None
```

Cancel coroutine task execution in a target loop.

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
 | __init__(loop: Optional[AbstractEventLoop] = None) -> None
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

**Returns**:

task

<a name="aea.helpers.async_utils.ThreadedAsyncRunner.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop event loop in thread.

<a name="aea.helpers.async_utils.Runnable"></a>
## Runnable Objects

```python
class Runnable(ABC)
```

Abstract Runnable class.

Use to run async task in same event loop or in dedicated thread.
Provides: start, stop sync methods to start and stop task
Use wait_completed to await task was completed.

<a name="aea.helpers.async_utils.Runnable.__init__"></a>
#### `__`init`__`

```python
 | __init__(loop: asyncio.AbstractEventLoop = None, threaded: bool = False) -> None
```

Init runnable.

**Arguments**:

- `loop`: asyncio event loop to use.
- `threaded`: bool. start in thread if True.

<a name="aea.helpers.async_utils.Runnable.start"></a>
#### start

```python
 | start() -> bool
```

Start runnable.

**Returns**:

bool started or not.

<a name="aea.helpers.async_utils.Runnable.is_running"></a>
#### is`_`running

```python
 | @property
 | is_running() -> bool
```

Get running state.

<a name="aea.helpers.async_utils.Runnable.run"></a>
#### run

```python
 | @abstractmethod
 | async run() -> Any
```

Implement run logic respectful to CancelError on termination.

<a name="aea.helpers.async_utils.Runnable.wait_completed"></a>
#### wait`_`completed

```python
 | wait_completed(sync: bool = False, timeout: float = None, force_result: bool = False) -> Awaitable
```

Wait runnable execution completed.

**Arguments**:

- `sync`: bool. blocking wait
- `timeout`: float seconds
- `force_result`: check result even it was waited.

**Returns**:

awaitable if sync is False, otherwise None

<a name="aea.helpers.async_utils.Runnable.stop"></a>
#### stop

```python
 | stop(force: bool = False) -> None
```

Stop runnable.

<a name="aea.helpers.async_utils.Runnable.start_and_wait_completed"></a>
#### start`_`and`_`wait`_`completed

```python
 | start_and_wait_completed(*args: Any, **kwargs: Any) -> Awaitable
```

Alias for start and wait methods.

