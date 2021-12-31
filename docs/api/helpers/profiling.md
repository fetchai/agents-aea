<a name="aea.helpers.profiling"></a>
# aea.helpers.profiling

Implementation of background profiling daemon.

<a name="aea.helpers.profiling.Profiling"></a>
## Profiling Objects

```python
class Profiling(Runnable)
```

Profiling service.

<a name="aea.helpers.profiling.Profiling.__init__"></a>
#### `__`init`__`

```python
 | __init__(period: int = 0, objects_instances_to_count: List[Type] = None, objects_created_to_count: List[Type] = None, output_function: Callable[[str], None] = lambda x: print(x, flush=True)) -> None
```

Init profiler.

**Arguments**:

- `period`: delay between profiling output in seconds.
- `objects_instances_to_count`: object to count
- `objects_created_to_count`: object created to count
- `output_function`: function to display output, one str argument.

<a name="aea.helpers.profiling.Profiling.set_counters"></a>
#### set`_`counters

```python
 | set_counters() -> None
```

Modify obj.__new__ to count objects created created.

<a name="aea.helpers.profiling.Profiling.run"></a>
#### run

```python
 | async run() -> None
```

Run profiling.

<a name="aea.helpers.profiling.Profiling.output_profile_data"></a>
#### output`_`profile`_`data

```python
 | output_profile_data() -> None
```

Render profiling data and call output_function.

<a name="aea.helpers.profiling.Profiling.get_profile_data"></a>
#### get`_`profile`_`data

```python
 | get_profile_data() -> Dict
```

Get profiling data dict.

<a name="aea.helpers.profiling.Profiling.get_objects_instances"></a>
#### get`_`objects`_`instances

```python
 | get_objects_instances() -> Dict
```

Return dict with counted object instances present now.

<a name="aea.helpers.profiling.Profiling.get_objecst_created"></a>
#### get`_`objecst`_`created

```python
 | get_objecst_created() -> Dict
```

Return dict with counted object instances created.

