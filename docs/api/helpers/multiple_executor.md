<a id="aea.helpers.multiple_executor"></a>

# aea.helpers.multiple`_`executor

This module contains the helpers to run multiple stoppable tasks in different modes: async, threaded, multiprocess .

<a id="aea.helpers.multiple_executor.ExecutorExceptionPolicies"></a>

## ExecutorExceptionPolicies Objects

```python
class ExecutorExceptionPolicies(Enum)
```

Runner exception policy modes.

<a id="aea.helpers.multiple_executor.ExecutorExceptionPolicies.stop_all"></a>

#### stop`_`all

stop all agents on one agent's failure, log exception

<a id="aea.helpers.multiple_executor.ExecutorExceptionPolicies.propagate"></a>

#### propagate

log exception and reraise it to upper level

<a id="aea.helpers.multiple_executor.ExecutorExceptionPolicies.log_only"></a>

#### log`_`only

log exception and skip it

<a id="aea.helpers.multiple_executor.AbstractExecutorTask"></a>

## AbstractExecutorTask Objects

```python
class AbstractExecutorTask(ABC)
```

Abstract task class to create Task classes.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Init task.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.future"></a>

#### future

```python
@property
def future() -> Optional[TaskAwaitable]
```

Return awaitable to get result of task execution.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.future"></a>

#### future

```python
@future.setter
def future(future: TaskAwaitable) -> None
```

Set awaitable to get result of task execution.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.start"></a>

#### start

```python
@abstractmethod
def start() -> Tuple[Callable, Sequence[Any]]
```

Implement start task function here.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.stop"></a>

#### stop

```python
@abstractmethod
def stop() -> None
```

Implement stop task function here.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.create_async_task"></a>

#### create`_`async`_`task

```python
@abstractmethod
def create_async_task(loop: AbstractEventLoop) -> TaskAwaitable
```

Create asyncio task for task run in asyncio loop.

**Arguments**:

- `loop`: the event loop

**Returns**:

task to run in asyncio loop.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.id"></a>

#### id

```python
@property
def id() -> Any
```

Return task id.

<a id="aea.helpers.multiple_executor.AbstractExecutorTask.failed"></a>

#### failed

```python
@property
def failed() -> bool
```

Return was exception failed or not.

If it's running it's not failed.

**Returns**:

bool

<a id="aea.helpers.multiple_executor.AbstractMultiprocessExecutorTask"></a>

## AbstractMultiprocessExecutorTask Objects

```python
class AbstractMultiprocessExecutorTask(AbstractExecutorTask)
```

Task for multiprocess executor.

<a id="aea.helpers.multiple_executor.AbstractMultiprocessExecutorTask.start"></a>

#### start

```python
@abstractmethod
def start() -> Tuple[Callable, Sequence[Any]]
```

Return function and arguments to call within subprocess.

<a id="aea.helpers.multiple_executor.AbstractMultiprocessExecutorTask.create_async_task"></a>

#### create`_`async`_`task

```python
def create_async_task(loop: AbstractEventLoop) -> TaskAwaitable
```

Create asyncio task for task run in asyncio loop.

Raise error, cause async mode is not supported, cause this task for multiprocess executor only.

**Arguments**:

- `loop`: the event loop

**Raises**:

- `ValueError`: async task construction not possible

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor"></a>

## AbstractMultipleExecutor Objects

```python
class AbstractMultipleExecutor(ABC)
```

Abstract class to create multiple executors classes.

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor.__init__"></a>

#### `__`init`__`

```python
def __init__(
    tasks: Sequence[AbstractExecutorTask],
    task_fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.
    propagate
) -> None
```

Init executor.

**Arguments**:

- `tasks`: sequence of AbstractExecutorTask instances to run.
- `task_fail_policy`: the exception policy of all the tasks

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor.is_running"></a>

#### is`_`running

```python
@property
def is_running() -> bool
```

Return running state of the executor.

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor.start"></a>

#### start

```python
def start() -> None
```

Start tasks.

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor.stop"></a>

#### stop

```python
def stop() -> None
```

Stop tasks.

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor.num_failed"></a>

#### num`_`failed

```python
@property
def num_failed() -> int
```

Return number of failed tasks.

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor.failed_tasks"></a>

#### failed`_`tasks

```python
@property
def failed_tasks() -> Sequence[AbstractExecutorTask]
```

Return sequence failed tasks.

<a id="aea.helpers.multiple_executor.AbstractMultipleExecutor.not_failed_tasks"></a>

#### not`_`failed`_`tasks

```python
@property
def not_failed_tasks() -> Sequence[AbstractExecutorTask]
```

Return sequence successful tasks.

<a id="aea.helpers.multiple_executor.ThreadExecutor"></a>

## ThreadExecutor Objects

```python
class ThreadExecutor(AbstractMultipleExecutor)
```

Thread based executor to run multiple agents in threads.

<a id="aea.helpers.multiple_executor.ProcessExecutor"></a>

## ProcessExecutor Objects

```python
class ProcessExecutor(ThreadExecutor)
```

Subprocess based executor to run multiple agents in threads.

<a id="aea.helpers.multiple_executor.AsyncExecutor"></a>

## AsyncExecutor Objects

```python
class AsyncExecutor(AbstractMultipleExecutor)
```

Thread based executor to run multiple agents in threads.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner"></a>

## AbstractMultipleRunner Objects

```python
class AbstractMultipleRunner()
```

Abstract multiple runner to create classes to launch tasks with selected mode.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.__init__"></a>

#### `__`init`__`

```python
def __init__(
    mode: str,
    fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.
    propagate
) -> None
```

Init with selected executor mode.

**Arguments**:

- `mode`: one of supported executor modes
- `fail_policy`: one of ExecutorExceptionPolicies to be used with Executor

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.is_running"></a>

#### is`_`running

```python
@property
def is_running() -> bool
```

Return state of the executor.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.start"></a>

#### start

```python
def start(threaded: bool = False) -> None
```

Run agents.

**Arguments**:

- `threaded`: run in dedicated thread without blocking current thread.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.stop"></a>

#### stop

```python
def stop(timeout: Optional[float] = None) -> None
```

Stop agents.

**Arguments**:

- `timeout`: timeout in seconds to wait thread stopped, only if started in thread mode.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.num_failed"></a>

#### num`_`failed

```python
@property
def num_failed() -> int
```

Return number of failed tasks.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.failed"></a>

#### failed

```python
@property
def failed() -> Sequence[Task]
```

Return sequence failed tasks.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.not_failed"></a>

#### not`_`failed

```python
@property
def not_failed() -> Sequence[Task]
```

Return sequence successful tasks.

<a id="aea.helpers.multiple_executor.AbstractMultipleRunner.try_join_thread"></a>

#### try`_`join`_`thread

```python
def try_join_thread() -> None
```

Try to join thread if running in thread mode.

