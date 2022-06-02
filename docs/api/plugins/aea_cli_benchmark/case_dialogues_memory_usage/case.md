<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`dialogues`_`memory`_`usage.case

Memory usage of dialogues across the time.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.DialogueHandler"></a>

## DialogueHandler Objects

```python
class DialogueHandler()
```

Generate messages and process with dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.DialogueHandler.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Set dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.DialogueHandler.random_string"></a>

#### random`_`string

```python
@property
def random_string() -> str
```

Get random string on every access.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.DialogueHandler.process_message"></a>

#### process`_`message

```python
def process_message() -> None
```

Process a message with dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.DialogueHandler.update"></a>

#### update

```python
def update(message: HttpMessage) -> HttpDialogue
```

Update dialogues with message.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.DialogueHandler.reply"></a>

#### reply

```python
@staticmethod
def reply(dialogue: HttpDialogue, message: HttpMessage) -> Message
```

Construct and send a response for message received.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.DialogueHandler.create"></a>

#### create

```python
def create() -> HttpMessage
```

Make initial http request.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_dialogues_memory_usage.case.run"></a>

#### run

```python
def run(messages_amount: int) -> List[Tuple[str, Union[float, int]]]
```

Test messages generation and memory consumption with dialogues.

