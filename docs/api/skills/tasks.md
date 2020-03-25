<a name=".aea.skills.tasks"></a>
## aea.skills.tasks

This module contains the classes for tasks.

<a name=".aea.skills.tasks.Task"></a>
### Task

```python
class Task()
```

This class implements an abstract task.

<a name=".aea.skills.tasks.Task.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs)
```

Initialize a task.

<a name=".aea.skills.tasks.Task.__call__"></a>
#### `__`call`__`

```python
 | __call__(*args, **kwargs)
```

Execute the task.

**Arguments**:

- `args`: positional arguments forwarded to the 'execute' method.
- `kwargs`: keyword arguments forwarded to the 'execute' method.
:return the task instance

**Raises**:

- `ValueError`: if the task has already been executed.

<a name=".aea.skills.tasks.Task.is_executed"></a>
#### is`_`executed

```python
 | @property
 | is_executed() -> bool
```

Check if the task has already been executed.

<a name=".aea.skills.tasks.Task.result"></a>
#### result

```python
 | @property
 | result() -> Any
```

Get the result.

:return the result from the execute method.

**Raises**:

- `ValueError`: if the task has not been executed yet.

<a name=".aea.skills.tasks.Task.setup"></a>
#### setup

```python
 | @abstractmethod
 | setup() -> None
```

Implement the behaviour setup.

**Returns**:

None

<a name=".aea.skills.tasks.Task.execute"></a>
#### execute

```python
 | @abstractmethod
 | execute(*args, **kwargs) -> None
```

Run the task logic.

**Returns**:

None

<a name=".aea.skills.tasks.Task.teardown"></a>
#### teardown

```python
 | @abstractmethod
 | teardown() -> None
```

Implement the behaviour teardown.

**Returns**:

None

<a name=".aea.skills.tasks.init_worker"></a>
#### init`_`worker

```python
init_worker()
```

Initialize a worker.

Disable the SIGINT handler.
Related to a well-known bug: https://bugs.python.org/issue8296

<a name=".aea.skills.tasks.TaskManager"></a>
### TaskManager

```python
class TaskManager()
```

A Task manager.

<a name=".aea.skills.tasks.TaskManager.__init__"></a>
#### `__`init`__`

```python
 | __init__(nb_workers: int = 5)
```

Initialize the task manager.

**Arguments**:

- `nb_workers`: the number of worker processes.

<a name=".aea.skills.tasks.TaskManager.nb_workers"></a>
#### nb`_`workers

```python
 | @property
 | nb_workers() -> int
```

Get the number of workers.

<a name=".aea.skills.tasks.TaskManager.enqueue_task"></a>
#### enqueue`_`task

```python
 | enqueue_task(func: Callable, args: Sequence = (), kwds: Optional[Dict[str, Any]] = None) -> int
```

Enqueue a task with the executor.

**Arguments**:

- `func`: the callable instance to be enqueued
- `args`: the positional arguments to be passed to the function.
- `kwds`: the keyword arguments to be passed to the function.
:return the task id to get the the result.

**Raises**:

- `ValueError`: if the task manager is not running.

<a name=".aea.skills.tasks.TaskManager.get_task_result"></a>
#### get`_`task`_`result

```python
 | get_task_result(task_id: int) -> AsyncResult
```

Get the result from a task.

<a name=".aea.skills.tasks.TaskManager.start"></a>
#### start

```python
 | start() -> None
```

Start the task manager.

<a name=".aea.skills.tasks.TaskManager.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop the task manager.

