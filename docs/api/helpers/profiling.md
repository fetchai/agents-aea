<a id="aea.helpers.profiling"></a>

# aea.helpers.profiling

Implementation of background profiling daemon.

<a id="aea.helpers.profiling.Profiling"></a>

## Profiling Objects

```python
class Profiling(Runnable)
```

Profiling service.

<a id="aea.helpers.profiling.Profiling.__init__"></a>

#### `__`init`__`

```python
def __init__(
    types_to_track: List[Type],
    period: int = 0,
    output_function: Callable[[str], None] = lambda x: print(x, flush=True)
) -> None
```

Init profiler.

**Arguments**:

- `period`: delay between profiling output in seconds.
- `types_to_track`: object types to count
- `output_function`: function to display output, one str argument.

<a id="aea.helpers.profiling.Profiling.set_counters"></a>

#### set`_`counters

```python
def set_counters() -> None
```

Modify __new__ and __del__ to count objects created created and destroyed.

<a id="aea.helpers.profiling.Profiling.run"></a>

#### run

```python
async def run() -> None
```

Run profiling.

<a id="aea.helpers.profiling.Profiling.output_profile_data"></a>

#### output`_`profile`_`data

```python
def output_profile_data() -> None
```

Render profiling data and call output_function.

<a id="aea.helpers.profiling.Profiling.get_profile_data"></a>

#### get`_`profile`_`data

```python
def get_profile_data() -> Dict
```

Get profiling data dict.

<a id="aea.helpers.profiling.get_most_common_objects_in_gc"></a>

#### get`_`most`_`common`_`objects`_`in`_`gc

```python
def get_most_common_objects_in_gc(number: int = 15) -> List[Tuple[str, int]]
```

Get the highest-count objects in the garbage collector.

