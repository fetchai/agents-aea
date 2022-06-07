<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`mem`_`usage.case

Memory usage check.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.case.TestHandler"></a>

## TestHandler Objects

```python
class TestHandler(Handler)
```

Dummy handler to handle messages.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.case.TestHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Noop setup.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.case.TestHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Noop teardown.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.case.TestHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle incoming message.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_mem_usage.case.run"></a>

#### run

```python
def run(duration: int,
        runtime_mode: str) -> List[Tuple[str, Union[int, float]]]
```

Check memory usage.

