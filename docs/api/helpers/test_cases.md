<a name=".aea.test_tools.test_cases"></a>
## aea.test`_`tools.test`_`cases

This module contains test case classes based on pytest for AEA end-to-end testing.

<a name=".aea.test_tools.test_cases.BaseAEATestCase"></a>
### BaseAEATestCase

```python
class BaseAEATestCase(ABC)
```

Base class for AEA test cases.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.set_agent_context"></a>
#### set`_`agent`_`context

```python
 | @classmethod
 | set_agent_context(cls, agent_name: str)
```

Set the current agent context.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.unset_agent_context"></a>
#### unset`_`agent`_`context

```python
 | @classmethod
 | unset_agent_context(cls)
```

Unset the current agent context.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.set_config"></a>
#### set`_`config

```python
 | @classmethod
 | set_config(cls, dotted_path: str, value: Any, type: str = "str") -> None
```

Set a config.
Run from agent's directory.

**Arguments**:

- `dotted_path`: str dotted path to config param.
- `value`: a new value to set.
- `type`: the type

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.force_set_config"></a>
#### force`_`set`_`config

```python
 | @classmethod
 | force_set_config(cls, dotted_path: str, value: Any) -> None
```

Force set config.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.disable_aea_logging"></a>
#### disable`_`aea`_`logging

```python
 | @classmethod
 | disable_aea_logging(cls)
```

Disable AEA logging of specific agent.
Run from agent's directory.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.run_cli_command"></a>
#### run`_`cli`_`command

```python
 | @classmethod
 | run_cli_command(cls, *args: str, cwd: str = ".") -> None
```

Run AEA CLI command.

**Arguments**:

- `args`: CLI args
- `cwd`: the working directory from where to run the command.

**Raises**:

- `AEATestingException`: if command fails.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.start_subprocess"></a>
#### start`_`subprocess

```python
 | @classmethod
 | start_subprocess(cls, *args: str, cwd: str = ".") -> subprocess.Popen
```

Run python with args as subprocess.

**Arguments**:

- `args`: CLI args

**Returns**:

subprocess object.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.start_thread"></a>
#### start`_`thread

```python
 | @classmethod
 | start_thread(cls, target: Callable, **kwargs) -> None
```

Start python Thread.

**Arguments**:

- `target`: target method.
- `process`: subprocess passed to thread args.

**Returns**:

None.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.create_agents"></a>
#### create`_`agents

```python
 | @classmethod
 | create_agents(cls, *agents_names: str) -> None
```

Create agents in current working directory.

**Arguments**:

- `agents_names`: str agent names.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.fetch_agent"></a>
#### fetch`_`agent

```python
 | @classmethod
 | fetch_agent(cls, public_id: str, agent_name: str) -> None
```

Create agents in current working directory.

**Arguments**:

- `public_id`: str public id
- `agents_name`: str agent name.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.difference_to_fetched_agent"></a>
#### difference`_`to`_`fetched`_`agent

```python
 | @classmethod
 | difference_to_fetched_agent(cls, public_id: str, agent_name: str) -> List[str]
```

Compare agent against the one fetched from public id.

**Arguments**:

- `public_id`: str public id
- `agents_name`: str agent name.

**Returns**:

list of files differing in the projects

<a name=".aea.test_tools.test_cases.BaseAEATestCase.delete_agents"></a>
#### delete`_`agents

```python
 | @classmethod
 | delete_agents(cls, *agents_names: str) -> None
```

Delete agents in current working directory.

**Arguments**:

- `agents_names`: str agent names.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.run_agent"></a>
#### run`_`agent

```python
 | @classmethod
 | run_agent(cls, *args: str) -> subprocess.Popen
```

Run agent as subprocess.
Run from agent's directory.

**Arguments**:

- `args`: CLI args

**Returns**:

subprocess object.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.terminate_agents"></a>
#### terminate`_`agents

```python
 | @classmethod
 | terminate_agents(cls, *subprocesses: subprocess.Popen, signal: signal.Signals = signal.SIGINT, timeout: int = 10) -> None
```

Terminate agent subprocesses.
Run from agent's directory.

**Arguments**:

- `subprocesses`: the subprocesses running the agents
- `signal`: the signal for interuption
- `timeout`: the timeout for interuption

<a name=".aea.test_tools.test_cases.BaseAEATestCase.is_successfully_terminated"></a>
#### is`_`successfully`_`terminated

```python
 | @classmethod
 | is_successfully_terminated(cls, *subprocesses: subprocess.Popen)
```

Check if all subprocesses terminated successfully

<a name=".aea.test_tools.test_cases.BaseAEATestCase.initialize_aea"></a>
#### initialize`_`aea

```python
 | @classmethod
 | initialize_aea(cls, author) -> None
```

Initialize AEA locally with author name.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.add_item"></a>
#### add`_`item

```python
 | @classmethod
 | add_item(cls, item_type: str, public_id: str) -> None
```

Add an item to the agent.
Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `public_id`: public id of the item.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.scaffold_item"></a>
#### scaffold`_`item

```python
 | @classmethod
 | scaffold_item(cls, item_type: str, name: str) -> None
```

Scaffold an item for the agent.
Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `name`: name of the item.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.fingerprint_item"></a>
#### fingerprint`_`item

```python
 | @classmethod
 | fingerprint_item(cls, item_type: str, public_id: str) -> None
```

Scaffold an item for the agent.
Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `name`: public id of the item.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.run_install"></a>
#### run`_`install

```python
 | @classmethod
 | run_install(cls)
```

Execute AEA CLI install command.
Run from agent's directory.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.generate_private_key"></a>
#### generate`_`private`_`key

```python
 | @classmethod
 | generate_private_key(cls, ledger_api_id: str = FETCHAI_NAME) -> None
```

Generate AEA private key with CLI command.
Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.add_private_key"></a>
#### add`_`private`_`key

```python
 | @classmethod
 | add_private_key(cls, ledger_api_id: str = FETCHAI_NAME, private_key_filepath: str = FETCHAI_PRIVATE_KEY_FILE) -> None
```

Add private key with CLI command.
Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.
- `private_key_filepath`: private key filepath.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.replace_private_key_in_file"></a>
#### replace`_`private`_`key`_`in`_`file

```python
 | @classmethod
 | replace_private_key_in_file(cls, private_key: str, private_key_filepath: str = FETCHAI_PRIVATE_KEY_FILE) -> None
```

Replace the private key in the provided file with the provided key.

**Arguments**:

- `private_key`: the private key
- `private_key_filepath`: the filepath to the private key file

**Returns**:

None
:raises: exception if file does not exist

<a name=".aea.test_tools.test_cases.BaseAEATestCase.generate_wealth"></a>
#### generate`_`wealth

```python
 | @classmethod
 | generate_wealth(cls, ledger_api_id: str = FETCHAI_NAME) -> None
```

Generate wealth with CLI command.
Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.get_wealth"></a>
#### get`_`wealth

```python
 | @classmethod
 | get_wealth(cls, ledger_api_id: str = FETCHAI_NAME) -> str
```

Get wealth with CLI command.
Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.

**Returns**:

command line output

<a name=".aea.test_tools.test_cases.BaseAEATestCase.replace_file_content"></a>
#### replace`_`file`_`content

```python
 | @classmethod
 | replace_file_content(cls, src: Path, dest: Path) -> None
```

Replace the content of the source file to the dest file.

**Arguments**:

- `src`: the source file.
- `dest`: the destination file.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.change_directory"></a>
#### change`_`directory

```python
 | @classmethod
 | change_directory(cls, path: Path) -> None
```

Change current working directory.

**Arguments**:

- `path`: path to the new working directory.

**Returns**:

None

<a name=".aea.test_tools.test_cases.BaseAEATestCase.send_envelope_to_agent"></a>
#### send`_`envelope`_`to`_`agent

```python
 | @classmethod
 | send_envelope_to_agent(cls, envelope: Envelope, agent: str)
```

Send an envelope to an agent, using the stub connection.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.read_envelope_from_agent"></a>
#### read`_`envelope`_`from`_`agent

```python
 | @classmethod
 | read_envelope_from_agent(cls, agent: str) -> Envelope
```

Read an envelope from an agent, using the stub connection.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.missing_from_output"></a>
#### missing`_`from`_`output

```python
 | @classmethod
 | missing_from_output(cls, process: subprocess.Popen, strings: Tuple[str], timeout: int = DEFAULT_PROCESS_TIMEOUT, period: int = 1, is_terminating: bool = True) -> List[str]
```

Check if strings are present in process output.
Read process stdout in thread and terminate when all strings are present
or timeout expired.

**Arguments**:

- `process`: agent subprocess.
- `strings`: tuple of strings expected to appear in output.
- `timeout`: int amount of seconds before stopping check.
- `period`: int period of checking.
- `is_terminating`: whether or not the agents are terminated

**Returns**:

list of missed strings.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.is_running"></a>
#### is`_`running

```python
 | @classmethod
 | is_running(cls, process: subprocess.Popen, timeout: int = DEFAULT_LAUNCH_TIMEOUT)
```

Check if the AEA is launched and running (ready to process messages).

**Arguments**:

- `process`: agent subprocess.
- `timeout`: the timeout to wait for launch to complete

<a name=".aea.test_tools.test_cases.BaseAEATestCase.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls)
```

Set up the test class.

<a name=".aea.test_tools.test_cases.BaseAEATestCase.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls)
```

Teardown the test.

<a name=".aea.test_tools.test_cases.AEATestCaseEmpty"></a>
### AEATestCaseEmpty

```python
class AEATestCaseEmpty(BaseAEATestCase)
```

Test case for a default AEA project.

This test case will create a default AEA project.

<a name=".aea.test_tools.test_cases.AEATestCaseEmpty.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls)
```

Set up the test class.

<a name=".aea.test_tools.test_cases.AEATestCaseMany"></a>
### AEATestCaseMany

```python
class AEATestCaseMany(BaseAEATestCase)
```

Test case for many AEA projects.

<a name=".aea.test_tools.test_cases.AEATestCaseMany.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls)
```

Set up the test class.

<a name=".aea.test_tools.test_cases.AEATestCaseMany.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls)
```

Teardown the test class.

<a name=".aea.test_tools.test_cases.AEATestCase"></a>
### AEATestCase

```python
class AEATestCase(BaseAEATestCase)
```

Test case from an existing AEA project.

Subclass this class and set `path_to_aea` properly. By default,
it is assumed the project is inside the current working directory.

<a name=".aea.test_tools.test_cases.AEATestCase.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls)
```

Set up the test class.

<a name=".aea.test_tools.test_cases.AEATestCase.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls)
```

Teardown the test class.

