<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`proactive.case

Envelopes generation speed for Behaviour act test.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.case.TestBehaviour"></a>

## TestBehaviour Objects

```python
class TestBehaviour(Behaviour)
```

Dummy handler to handle messages.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.case.TestBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Set up behaviour.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.case.TestBehaviour.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear up behaviour.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.case.TestBehaviour.act"></a>

#### act

```python
def act() -> None
```

Perform action on periodic basis.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_proactive.case.run"></a>

#### run

```python
def run(duration: int,
        runtime_mode: str) -> List[Tuple[str, Union[int, float]]]
```

Test act message generate performance.

