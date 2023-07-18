<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.utils

Performance checks utils.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.ROOT_DIR"></a>

#### ROOT`_`DIR

type: ignore

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.wait_for_condition"></a>

#### wait`_`for`_`condition

```python
def wait_for_condition(condition_checker: Callable,
                       timeout: int = 2,
                       error_msg: str = "Timeout") -> None
```

Wait for condition occurs in selected timeout.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.make_agent"></a>

#### make`_`agent

```python
def make_agent(agent_name: str = "my_agent",
               runtime_mode: str = "threaded",
               resources: Optional[Resources] = None,
               wallet: Optional[Wallet] = None,
               identity: Optional[Identity] = None,
               packages_dir=PACKAGES_DIR,
               default_ledger=None) -> AEA
```

Make AEA instance.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.make_envelope"></a>

#### make`_`envelope

```python
def make_envelope(sender: str,
                  to: str,
                  message: Optional[Message] = None) -> Envelope
```

Make an envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection"></a>

## GeneratorConnection Objects

```python
class GeneratorConnection(Connection)
```

Generates messages and count.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any)
```

Init connection.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.enable"></a>

#### enable

```python
def enable() -> None
```

Enable message generation.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.disable"></a>

#### disable

```python
def disable() -> None
```

Disable message generation.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.connect"></a>

#### connect

```python
async def connect() -> None
```

Connect connection.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.disconnect"></a>

#### disconnect

```python
async def disconnect() -> None
```

Disconnect connection.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.send"></a>

#### send

```python
async def send(envelope: "Envelope") -> None
```

Handle incoming envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.receive"></a>

#### receive

```python
async def receive(*args: Any, **kwargs: Any) -> Optional["Envelope"]
```

Generate an envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.GeneratorConnection.make"></a>

#### make

```python
@classmethod
def make(cls) -> "GeneratorConnection"
```

Construct connection instance.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.SyncedGeneratorConnection"></a>

## SyncedGeneratorConnection Objects

```python
class SyncedGeneratorConnection(GeneratorConnection)
```

Synchronized message generator.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.SyncedGeneratorConnection.__init__"></a>

#### `__`init`__`

```python
def __init__(*args: Any, **kwargs: Any) -> None
```

Init connection.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.SyncedGeneratorConnection.condition"></a>

#### condition

```python
@property
def condition() -> asyncio.Event
```

Get condition.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.SyncedGeneratorConnection.connect"></a>

#### connect

```python
async def connect() -> None
```

Connect connection.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.SyncedGeneratorConnection.send"></a>

#### send

```python
async def send(envelope: "Envelope") -> None
```

Handle incoming envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.SyncedGeneratorConnection.receive"></a>

#### receive

```python
async def receive(*args: Any, **kwargs: Any) -> Optional["Envelope"]
```

Generate an envelope.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.make_skill"></a>

#### make`_`skill

```python
def make_skill(agent: AEA,
               handlers: Optional[Dict[str, Type[Handler]]] = None,
               behaviours: Optional[Dict[str, Type[Behaviour]]] = None,
               skill_id: Optional[PublicId] = None) -> Skill
```

Construct skill instance for agent from behaviours.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.get_mem_usage_in_mb"></a>

#### get`_`mem`_`usage`_`in`_`mb

```python
def get_mem_usage_in_mb() -> float
```

Get memory usage of the current process in megabytes.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.multi_run"></a>

#### multi`_`run

```python
def multi_run(num_runs: int, fn: Callable,
              args: Tuple) -> List[Tuple[str, Any, Any, Any]]
```

Perform multiple test runs.

**Arguments**:

- `num_runs`: host many times to run
- `fn`: callable  that returns list of tuples with result
- `args`: args to pass to callable

**Returns**:

list of tuples of results

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.print_results"></a>

#### print`_`results

```python
def print_results(
        output_format: str, parameters: Dict,
        result_fn: Callable[..., List[Tuple[str, Any, Any, Any]]]) -> Any
```

Print result for multi_run response.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.make_identity_from_wallet"></a>

#### make`_`identity`_`from`_`wallet

```python
def make_identity_from_wallet(name, wallet, default_ledger)
```

Make indentity for ledger id and wallet specified.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.utils.with_packages"></a>

#### with`_`packages

```python
@contextmanager
def with_packages(packages: List[Tuple[str, str]],
                  packages_dir: Optional[Path] = None)
```

Download and install packages context manager.

