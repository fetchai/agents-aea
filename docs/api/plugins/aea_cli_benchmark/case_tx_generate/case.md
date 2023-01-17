<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`tx`_`generate.case

Ledger TX generation and processing benchmark.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.LedgerApiHandler"></a>

## LedgerApiHandler Objects

```python
class LedgerApiHandler(Handler)
```

Dummy handler to handle messages.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.LedgerApiHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Noop setup.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.LedgerApiHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Noop teardown.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.LedgerApiHandler.handle"></a>

#### handle

```python
def handle(ledger_api_msg: Message) -> None
```

Handle incoming message.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.GenericSigningHandler"></a>

## GenericSigningHandler Objects

```python
class GenericSigningHandler(Handler)
```

Implement the signing handler.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.GenericSigningHandler.setup"></a>

#### setup

```python
def setup() -> None
```

Implement the setup for the handler.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.GenericSigningHandler.handle"></a>

#### handle

```python
def handle(message: Message) -> None
```

Implement the reaction to a message.

**Arguments**:

- `message`: the message

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.GenericSigningHandler.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Implement the handler teardown.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case"></a>

## Case Objects

```python
class Case()
```

TBenchmark case implementation.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.__init__"></a>

#### `__`init`__`

```python
def __init__(ledger_id: str, ledger_api_config: Dict, private_keys: Dict)
```

Init case.

**Arguments**:

- `ledger_id`: str, ledger id, one of fetchai, ethereum
- `ledger_api_config`: config for ledger connection
- `private_keys`: private keys dict to use for wallet contruction

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.ledger_handler"></a>

#### ledger`_`handler

```python
@property
def ledger_handler() -> LedgerApiHandler
```

Get ledger api handler instance.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.tx_settled_counter"></a>

#### tx`_`settled`_`counter

```python
@property
def tx_settled_counter() -> int
```

Get amount of txs settled.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.wait_tx_settled"></a>

#### wait`_`tx`_`settled

```python
def wait_tx_settled() -> None
```

Wait for tx settled.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.ledger_api_dialogues"></a>

#### ledger`_`api`_`dialogues

```python
@property
def ledger_api_dialogues() -> LedgerApiDialogues
```

Get ledger api dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.my_addr"></a>

#### my`_`addr

```python
@property
def my_addr() -> str
```

Get my agent address.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.make_ledger_msg"></a>

#### make`_`ledger`_`msg

```python
def make_ledger_msg(sender_address: str,
                    counterparty_address: str) -> LedgerApiMessage
```

Make ledger api message to be signed and published over ledger netework.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.start_agent"></a>

#### start`_`agent

```python
def start_agent() -> None
```

Construct and start agent.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.stop_agent"></a>

#### stop`_`agent

```python
def stop_agent() -> None
```

Stop agent.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.put_message_and_wait"></a>

#### put`_`message`_`and`_`wait

```python
def put_message_and_wait(msg: Message) -> None
```

Put ledger api message and wait tx constructed, signed and settled.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.Case.run"></a>

#### run

```python
def run(time_in_seconds: float) -> Tuple[int, float]
```

Run a test case.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.case.run"></a>

#### run

```python
def run(ledger_id: str,
        running_time: float) -> List[Tuple[str, Union[int, float]]]
```

Check tx processing speed.

