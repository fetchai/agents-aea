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
 | __init__(initial_state: Any = None, states_enum: Optional[Container[Any]] = None)
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

**Returns**:

None

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

**Returns**:

None

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
ensure_loop(loop: Optional[AbstractEventLoop] = None) -> AbstractEventLoop
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

<a name="aea.helpers.async_utils.AwaitableProc"></a>
## AwaitableProc Objects

```python
class AwaitableProc()
```

Async-friendly subprocess.Popen

<a name="aea.helpers.async_utils.AwaitableProc.__init__"></a>
#### `__`init`__`

```python
 | __init__(*args, **kwargs)
```

Initialise awaitable proc.

<a name="aea.helpers.async_utils.AwaitableProc.start"></a>
#### start

```python
 | async start()
```

Start the subprocess

<a name="aea.helpers.async_utils.ItemGetter"></a>
## ItemGetter Objects

```python
class ItemGetter()
```

Virtual queue like object to get items from getters function.

<a name="aea.helpers.async_utils.ItemGetter.__init__"></a>
#### `__`init`__`

```python
 | __init__(getters: List[Callable]) -> None
```

Init ItemGetter.

**Arguments**:

- `getters`: List of couroutines to be awaited.

<a name="aea.helpers.async_utils.ItemGetter.get"></a>
#### get

```python
 | async get() -> Any
```

Get item.

<a name="aea.helpers.async_utils.HandlerItemGetter"></a>
## HandlerItemGetter Objects

```python
class HandlerItemGetter(ItemGetter)
```

ItemGetter with handler passed.

<a name="aea.helpers.async_utils.HandlerItemGetter.__init__"></a>
#### `__`init`__`

```python
 | __init__(getters: List[Tuple[Callable[[Any], None], Callable]])
```

Init HandlerItemGetter.

**Arguments**:

- `getters`: List of tuples of handler and couroutine to be awaiteed for an item.

