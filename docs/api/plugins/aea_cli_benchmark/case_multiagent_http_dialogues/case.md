<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`multiagent`_`http`_`dialogues.case

Memory usage across the time.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.HttpPingPongHandler"></a>

## HttpPingPongHandler Objects

```python
class HttpPingPongHandler(Handler)
```

Dummy handler to handle messages.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.HttpPingPongHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Noop setup.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.HttpPingPongHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Noop teardown.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.HttpPingPongHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Handle incoming message.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.HttpPingPongHandler.make_response"></a>

#### make`_`response

```python
def make_response(dialogue: HttpDialogue, message: HttpMessage) -> None
```

Construct and send a response for message received.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.HttpPingPongHandler.make_request"></a>

#### make`_`request

```python
def make_request(recipient_addr: str) -> None
```

Make initial http request.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.make_agent"></a>

#### make`_`agent

```python
def make_agent(*args: Any, **kwargs: Any) -> AEA
```

Make agent with http protocol support.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_multiagent_http_dialogues.case.run"></a>

#### run

```python
def run(duration: int, runtime_mode: str, runner_mode: str,
        start_messages: int,
        num_of_agents: int) -> List[Tuple[str, Union[int, float]]]
```

Test multiagent message exchange.

