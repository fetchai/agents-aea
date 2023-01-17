<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`reactive.case

Latency and throughput check.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestConnectionMixIn"></a>

## TestConnectionMixIn Objects

```python
class TestConnectionMixIn()
```

Test connection with messages timing.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestConnectionMixIn.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Init connection.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestConnectionMixIn.send"></a>

#### send

```python
async def send(envelope: Envelope) -> None
```

Handle incoming envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestConnectionMixIn.receive"></a>

#### receive

```python
async def receive(*args: Any, **kwargs: Any) -> Optional[Envelope]
```

Generate outgoing envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestHandler"></a>

## TestHandler Objects

```python
class TestHandler(Handler)
```

Dummy handler to handle messages.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Noop setup.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Noop teardown.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.TestHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle incoming message.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_reactive.case.run"></a>

#### run

```python
def run(duration: int, runtime_mode: str,
        connection_mode: str) -> List[Tuple[str, Union[int, float]]]
```

Test memory usage.

