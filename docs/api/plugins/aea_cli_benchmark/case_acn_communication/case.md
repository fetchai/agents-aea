<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`acn`_`communication.case

Check amount of time for acn connection communications.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.case.TimeMeasure"></a>

## TimeMeasure Objects

```python
class TimeMeasure()
```

Time measure data class.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.case.TimeMeasure.__init__"></a>

#### `__`init`__`

```python
def __init__()
```

Init data class instance.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.case.time_measure"></a>

#### time`_`measure

```python
@contextmanager
def time_measure()
```

Get time measure context.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.case.make_envelope"></a>

#### make`_`envelope

```python
def make_envelope(from_addr: str, to_addr: str) -> Envelope
```

Construct an envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_acn_communication.case.run"></a>

#### run

```python
def run(connection: str,
        run_times: int = 10) -> List[Tuple[str, Union[int, float]]]
```

Check construction time and memory usage.

