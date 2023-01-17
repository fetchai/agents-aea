<a id="aea.runner"></a>

# aea.runner

This module contains the implementation of AEA multiple instances runner.

<a id="aea.runner.AEAInstanceTask"></a>

## AEAInstanceTask Objects

```python
class AEAInstanceTask(AbstractExecutorTask)
```

Task to run agent instance.

<a id="aea.runner.AEAInstanceTask.__init__"></a>

#### `__`init`__`

```python
def __init__(agent: AEA) -> None
```

Init AEA instance task.

**Arguments**:

- `agent`: AEA instance to run within task.

<a id="aea.runner.AEAInstanceTask.id"></a>

#### id

```python
@property
def id() -> str
```

Return agent name.

<a id="aea.runner.AEAInstanceTask.start"></a>

#### start

```python
def start() -> None
```

Start task.

<a id="aea.runner.AEAInstanceTask.stop"></a>

#### stop

```python
def stop() -> None
```

Stop task.

<a id="aea.runner.AEAInstanceTask.create_async_task"></a>

#### create`_`async`_`task

```python
def create_async_task(loop: AbstractEventLoop) -> TaskAwaitable
```

Return asyncio Task for task run in asyncio loop.

**Arguments**:

- `loop`: abstract event loop

**Returns**:

task to run runtime

<a id="aea.runner.AEARunner"></a>

## AEARunner Objects

```python
class AEARunner(AbstractMultipleRunner)
```

Run multiple AEA instances.

<a id="aea.runner.AEARunner.__init__"></a>

#### `__`init`__`

```python
def __init__(
    agents: Sequence[AEA],
    mode: str,
    fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.
    propagate
) -> None
```

Init AEARunner.

**Arguments**:

- `agents`: sequence of AEA instances to run.
- `mode`: executor name to use.
- `fail_policy`: one of ExecutorExceptionPolicies to be used with Executor

