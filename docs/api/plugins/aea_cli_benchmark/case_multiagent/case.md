<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`multiagent.case

Envelopes generation speed for Behaviour act test.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.case.TestHandler"></a>

## TestHandler Objects

```python
class TestHandler(Handler)
```

Dummy handler to handle messages.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.case.TestHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Noop setup.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.case.TestHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Noop teardown.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.case.TestHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle incoming message.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent.case.run"></a>

#### run

```python
def run(duration: int, runtime_mode: str, runner_mode: str,
        start_messages: int,
        num_of_agents: int) -> List[Tuple[str, Union[int, float]]]
```

Test multiagent message exchange.

