<a name="aea.runner"></a>
# aea.runner

This module contains the implementation of AEA multiple instances runner.

<a name="aea.runner.AEAInstanceTask"></a>
## AEAInstanceTask Objects

```python
class AEAInstanceTask(AbstractExecutorTask)
```

Task to run agent instance.

<a name="aea.runner.AEAInstanceTask.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent: AEA) -> None
```

Init aea instance task.

**Arguments**:

- `agent`: AEA instance to run within task.

<a name="aea.runner.AEAInstanceTask.id"></a>
#### id

```python
 | @property
 | id() -> str
```

Return agent name.

<a name="aea.runner.AEAInstanceTask.start"></a>
#### start

```python
 | start() -> None
```

Start task.

<a name="aea.runner.AEAInstanceTask.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop task.

<a name="aea.runner.AEAInstanceTask.create_async_task"></a>
#### create`_`async`_`task

```python
 | create_async_task(loop: AbstractEventLoop) -> TaskAwaitable
```

Return asyncio Task for task run in asyncio loop.

**Arguments**:

- `loop`: abstract event loop

**Returns**:

task to run runtime

<a name="aea.runner.AEARunner"></a>
## AEARunner Objects

```python
class AEARunner(AbstractMultipleRunner)
```

Run multiple AEA instances.

<a name="aea.runner.AEARunner.__init__"></a>
#### `__`init`__`

```python
 | __init__(agents: Sequence[AEA], mode: str, fail_policy: ExecutorExceptionPolicies = ExecutorExceptionPolicies.propagate) -> None
```

Init AEARunner.

**Arguments**:

- `agents`: sequence of AEA instances to run.
- `mode`: executor name to use.
- `fail_policy`: one of ExecutorExceptionPolicies to be used with Executor

