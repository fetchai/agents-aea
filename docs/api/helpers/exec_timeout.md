<a name="aea.helpers.exec_timeout"></a>
# aea.helpers.exec`_`timeout

Python code execution time limit tools.

<a name="aea.helpers.exec_timeout.TimeoutResult"></a>
## TimeoutResult Objects

```python
class TimeoutResult()
```

Result of ExecTimeout context manager.

<a name="aea.helpers.exec_timeout.TimeoutResult.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Init.

<a name="aea.helpers.exec_timeout.TimeoutResult.set_cancelled_by_timeout"></a>
#### set`_`cancelled`_`by`_`timeout

```python
 | set_cancelled_by_timeout() -> None
```

Set code was terminated cause timeout.

<a name="aea.helpers.exec_timeout.TimeoutResult.is_cancelled_by_timeout"></a>
#### is`_`cancelled`_`by`_`timeout

```python
 | is_cancelled_by_timeout() -> bool
```

Return True if code was terminated by ExecTimeout cause timeout.

**Returns**:

bool

<a name="aea.helpers.exec_timeout.TimeoutException"></a>
## TimeoutException Objects

```python
class TimeoutException(BaseException)
```

TimeoutException raised by ExecTimeout context managers in thread with limited execution time.

Used internally, does not propagated outside of context manager

<a name="aea.helpers.exec_timeout.BaseExecTimeout"></a>
## BaseExecTimeout Objects

```python
class BaseExecTimeout(ABC)
```

Base class for implementing context managers to limit python code execution time.

exception_class - is exception type to raise in code controlled in case of timeout.

<a name="aea.helpers.exec_timeout.BaseExecTimeout.__init__"></a>
#### `__`init`__`

```python
 | __init__(timeout: float = 0.0) -> None
```

Init.

**Arguments**:

- `timeout`: number of seconds to execute code before interruption

<a name="aea.helpers.exec_timeout.BaseExecTimeout.__enter__"></a>
#### `__`enter`__`

```python
 | __enter__() -> TimeoutResult
```

Enter context manager.

**Returns**:

TimeoutResult

<a name="aea.helpers.exec_timeout.BaseExecTimeout.__exit__"></a>
#### `__`exit`__`

```python
 | __exit__(exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None
```

Exit context manager.

**Arguments**:

- `exc_type`: the exception type
- `exc_val`: the exception
- `exc_tb`: the traceback

<a name="aea.helpers.exec_timeout.ExecTimeoutSigAlarm"></a>
## ExecTimeoutSigAlarm Objects

```python
class ExecTimeoutSigAlarm(BaseExecTimeout)
```

ExecTimeout context manager implementation using signals and SIGALARM.

Does not support threads, have to be used only in main thread.

<a name="aea.helpers.exec_timeout.ExecTimeoutThreadGuard"></a>
## ExecTimeoutThreadGuard Objects

```python
class ExecTimeoutThreadGuard(BaseExecTimeout)
```

ExecTimeout context manager implementation using threads and PyThreadState_SetAsyncExc.

Support threads.
Requires supervisor thread start/stop to control execution time control.
Possible will be not accurate in case of long c functions used inside code controlled.

<a name="aea.helpers.exec_timeout.ExecTimeoutThreadGuard.__init__"></a>
#### `__`init`__`

```python
 | __init__(timeout: float = 0.0) -> None
```

Init ExecTimeoutThreadGuard variables.

**Arguments**:

- `timeout`: number of seconds to execute code before interruption

<a name="aea.helpers.exec_timeout.ExecTimeoutThreadGuard.start"></a>
#### start

```python
 | @classmethod
 | start(cls) -> None
```

Start supervisor thread to check timeouts.

Supervisor starts once but number of start counted.

<a name="aea.helpers.exec_timeout.ExecTimeoutThreadGuard.stop"></a>
#### stop

```python
 | @classmethod
 | stop(cls, force: bool = False) -> None
```

Stop supervisor thread.

Actual stop performed on force == True or if  number of stops == number of starts

**Arguments**:

- `force`: force stop regardless number of start.

