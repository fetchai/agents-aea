<a name="aea.test_tools.test_cases"></a>
# aea.test`_`tools.test`_`cases

This module contains test case classes based on pytest for AEA end-to-end testing.

<a name="aea.test_tools.test_cases.BaseAEATestCase"></a>
## BaseAEATestCase Objects

```python
class BaseAEATestCase(ABC)
```

Base class for AEA test cases.

<a name="aea.test_tools.test_cases.BaseAEATestCase.set_agent_context"></a>
#### set`_`agent`_`context

```python
 | @classmethod
 | set_agent_context(cls, agent_name: str) -> None
```

Set the current agent context.

<a name="aea.test_tools.test_cases.BaseAEATestCase.unset_agent_context"></a>
#### unset`_`agent`_`context

```python
 | @classmethod
 | unset_agent_context(cls) -> None
```

Unset the current agent context.

<a name="aea.test_tools.test_cases.BaseAEATestCase.set_config"></a>
#### set`_`config

```python
 | @classmethod
 | set_config(cls, dotted_path: str, value: Any, type_: Optional[str] = None) -> Result
```

Set a config.

Run from agent's directory.

**Arguments**:

- `dotted_path`: str dotted path to config param.
- `value`: a new value to set.
- `type_`: the type

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.nested_set_config"></a>
#### nested`_`set`_`config

```python
 | @classmethod
 | nested_set_config(cls, dotted_path: str, value: Any) -> None
```

Force set config.

<a name="aea.test_tools.test_cases.BaseAEATestCase.disable_aea_logging"></a>
#### disable`_`aea`_`logging

```python
 | @classmethod
 | disable_aea_logging(cls) -> None
```

Disable AEA logging of specific agent.

Run from agent's directory.

<a name="aea.test_tools.test_cases.BaseAEATestCase.run_cli_command"></a>
#### run`_`cli`_`command

```python
 | @classmethod
 | run_cli_command(cls, *args: str, *, cwd: str = ".", **kwargs: str) -> Result
```

Run AEA CLI command.

**Arguments**:

- `args`: CLI args
- `cwd`: the working directory from where to run the command.
- `kwargs`: other keyword arguments to click.CliRunner.invoke.

**Raises**:

- `AEATestingException`: if command fails.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.start_subprocess"></a>
#### start`_`subprocess

```python
 | @classmethod
 | start_subprocess(cls, *args: str, *, cwd: str = ".") -> subprocess.Popen
```

Run python with args as subprocess.

**Arguments**:

- `args`: CLI args
- `cwd`: the current working directory

**Returns**:

subprocess object.

<a name="aea.test_tools.test_cases.BaseAEATestCase.start_thread"></a>
#### start`_`thread

```python
 | @classmethod
 | start_thread(cls, target: Callable, **kwargs: subprocess.Popen) -> Thread
```

Start python Thread.

**Arguments**:

- `target`: target method.
- `kwargs`: thread keyword arguments

**Returns**:

thread

<a name="aea.test_tools.test_cases.BaseAEATestCase.create_agents"></a>
#### create`_`agents

```python
 | @classmethod
 | create_agents(cls, *agents_names: str, *, is_local: bool = True, is_empty: bool = False) -> None
```

Create agents in current working directory.

**Arguments**:

- `agents_names`: str agent names.
- `is_local`: a flag for local folder add True by default.
- `is_empty`: optional boolean flag for skip adding default dependencies.

<a name="aea.test_tools.test_cases.BaseAEATestCase.fetch_agent"></a>
#### fetch`_`agent

```python
 | @classmethod
 | fetch_agent(cls, public_id: str, agent_name: str, is_local: bool = True) -> None
```

Create agents in current working directory.

**Arguments**:

- `public_id`: str public id
- `agent_name`: str agent name.
- `is_local`: a flag for local folder add True by default.

<a name="aea.test_tools.test_cases.BaseAEATestCase.difference_to_fetched_agent"></a>
#### difference`_`to`_`fetched`_`agent

```python
 | @classmethod
 | difference_to_fetched_agent(cls, public_id: str, agent_name: str) -> List[str]
```

Compare agent against the one fetched from public id.

**Arguments**:

- `public_id`: str public id
- `agent_name`: str agent name.

**Returns**:

list of files differing in the projects

<a name="aea.test_tools.test_cases.BaseAEATestCase.delete_agents"></a>
#### delete`_`agents

```python
 | @classmethod
 | delete_agents(cls, *agents_names: str) -> None
```

Delete agents in current working directory.

**Arguments**:

- `agents_names`: str agent names.

<a name="aea.test_tools.test_cases.BaseAEATestCase.run_agent"></a>
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

<a name="aea.test_tools.test_cases.BaseAEATestCase.run_interaction"></a>
#### run`_`interaction

```python
 | @classmethod
 | run_interaction(cls) -> subprocess.Popen
```

Run interaction as subprocess.

Run from agent's directory.

**Returns**:

subprocess object.

<a name="aea.test_tools.test_cases.BaseAEATestCase.terminate_agents"></a>
#### terminate`_`agents

```python
 | @classmethod
 | terminate_agents(cls, *subprocesses: subprocess.Popen, *, timeout: int = 20) -> None
```

Terminate agent subprocesses.

Run from agent's directory.

**Arguments**:

- `subprocesses`: the subprocesses running the agents
- `timeout`: the timeout for interruption

<a name="aea.test_tools.test_cases.BaseAEATestCase.is_successfully_terminated"></a>
#### is`_`successfully`_`terminated

```python
 | @classmethod
 | is_successfully_terminated(cls, *subprocesses: subprocess.Popen) -> bool
```

Check if all subprocesses terminated successfully.

<a name="aea.test_tools.test_cases.BaseAEATestCase.initialize_aea"></a>
#### initialize`_`aea

```python
 | @classmethod
 | initialize_aea(cls, author: str) -> None
```

Initialize AEA locally with author name.

<a name="aea.test_tools.test_cases.BaseAEATestCase.add_item"></a>
#### add`_`item

```python
 | @classmethod
 | add_item(cls, item_type: str, public_id: str, local: bool = True) -> Result
```

Add an item to the agent.

Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `public_id`: public id of the item.
- `local`: a flag for local folder add True by default.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.remove_item"></a>
#### remove`_`item

```python
 | @classmethod
 | remove_item(cls, item_type: str, public_id: str) -> Result
```

Remove an item from the agent.

Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `public_id`: public id of the item.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.scaffold_item"></a>
#### scaffold`_`item

```python
 | @classmethod
 | scaffold_item(cls, item_type: str, name: str, skip_consistency_check: bool = False) -> Result
```

Scaffold an item for the agent.

Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `name`: name of the item.
- `skip_consistency_check`: if True, skip consistency check.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.fingerprint_item"></a>
#### fingerprint`_`item

```python
 | @classmethod
 | fingerprint_item(cls, item_type: str, public_id: str) -> Result
```

Fingerprint an item for the agent.

Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `public_id`: public id of the item.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.eject_item"></a>
#### eject`_`item

```python
 | @classmethod
 | eject_item(cls, item_type: str, public_id: str) -> Result
```

Eject an item in the agent in quiet mode (i.e. no interaction).

Run from agent's directory.

**Arguments**:

- `item_type`: str item type.
- `public_id`: public id of the item.

**Returns**:

None

<a name="aea.test_tools.test_cases.BaseAEATestCase.run_install"></a>
#### run`_`install

```python
 | @classmethod
 | run_install(cls) -> Result
```

Execute AEA CLI install command.

Run from agent's directory.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.generate_private_key"></a>
#### generate`_`private`_`key

```python
 | @classmethod
 | generate_private_key(cls, ledger_api_id: str = DEFAULT_LEDGER, private_key_file: Optional[str] = None, password: Optional[str] = None) -> Result
```

Generate AEA private key with CLI command.

Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.
- `private_key_file`: the private key file.
- `password`: the password.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.add_private_key"></a>
#### add`_`private`_`key

```python
 | @classmethod
 | add_private_key(cls, ledger_api_id: str = DEFAULT_LEDGER, private_key_filepath: str = DEFAULT_PRIVATE_KEY_FILE, connection: bool = False, password: Optional[str] = None) -> Result
```

Add private key with CLI command.

Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.
- `private_key_filepath`: private key filepath.
- `connection`: whether or not the private key filepath is for a connection.
- `password`: the password to encrypt private keys.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.remove_private_key"></a>
#### remove`_`private`_`key

```python
 | @classmethod
 | remove_private_key(cls, ledger_api_id: str = DEFAULT_LEDGER, connection: bool = False) -> Result
```

Remove private key with CLI command.

Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.
- `connection`: whether or not the private key filepath is for a connection.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.replace_private_key_in_file"></a>
#### replace`_`private`_`key`_`in`_`file

```python
 | @classmethod
 | replace_private_key_in_file(cls, private_key: str, private_key_filepath: str = DEFAULT_PRIVATE_KEY_FILE) -> None
```

Replace the private key in the provided file with the provided key.

**Arguments**:

- `private_key`: the private key
- `private_key_filepath`: the filepath to the private key file
:raises: exception if file does not exist

<a name="aea.test_tools.test_cases.BaseAEATestCase.generate_wealth"></a>
#### generate`_`wealth

```python
 | @classmethod
 | generate_wealth(cls, ledger_api_id: str = DEFAULT_LEDGER, password: Optional[str] = None) -> Result
```

Generate wealth with CLI command.

Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.
- `password`: the password.

**Returns**:

Result

<a name="aea.test_tools.test_cases.BaseAEATestCase.get_wealth"></a>
#### get`_`wealth

```python
 | @classmethod
 | get_wealth(cls, ledger_api_id: str = DEFAULT_LEDGER, password: Optional[str] = None) -> str
```

Get wealth with CLI command.

Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.
- `password`: the password to encrypt/decrypt private keys.

**Returns**:

command line output

<a name="aea.test_tools.test_cases.BaseAEATestCase.get_address"></a>
#### get`_`address

```python
 | @classmethod
 | get_address(cls, ledger_api_id: str = DEFAULT_LEDGER, password: Optional[str] = None) -> str
```

Get address with CLI command.

Run from agent's directory.

**Arguments**:

- `ledger_api_id`: ledger API ID.
- `password`: the password to encrypt/decrypt private keys.

**Returns**:

command line output

<a name="aea.test_tools.test_cases.BaseAEATestCase.replace_file_content"></a>
#### replace`_`file`_`content

```python
 | @classmethod
 | replace_file_content(cls, src: Path, dest: Path) -> None
```

Replace the content of the source file to the destination file.

**Arguments**:

- `src`: the source file.
- `dest`: the destination file.

<a name="aea.test_tools.test_cases.BaseAEATestCase.change_directory"></a>
#### change`_`directory

```python
 | @classmethod
 | change_directory(cls, path: Path) -> None
```

Change current working directory.

**Arguments**:

- `path`: path to the new working directory.

<a name="aea.test_tools.test_cases.BaseAEATestCase.send_envelope_to_agent"></a>
#### send`_`envelope`_`to`_`agent

```python
 | @classmethod
 | send_envelope_to_agent(cls, envelope: Envelope, agent: str) -> None
```

Send an envelope to an agent, using the stub connection.

<a name="aea.test_tools.test_cases.BaseAEATestCase.read_envelope_from_agent"></a>
#### read`_`envelope`_`from`_`agent

```python
 | @classmethod
 | read_envelope_from_agent(cls, agent: str) -> Envelope
```

Read an envelope from an agent, using the stub connection.

<a name="aea.test_tools.test_cases.BaseAEATestCase.missing_from_output"></a>
#### missing`_`from`_`output

```python
 | @classmethod
 | missing_from_output(cls, process: subprocess.Popen, strings: Sequence[str], timeout: int = DEFAULT_PROCESS_TIMEOUT, period: int = 1, is_terminating: bool = True) -> List[str]
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

<a name="aea.test_tools.test_cases.BaseAEATestCase.is_running"></a>
#### is`_`running

```python
 | @classmethod
 | is_running(cls, process: subprocess.Popen, timeout: int = DEFAULT_LAUNCH_TIMEOUT) -> bool
```

Check if the AEA is launched and running (ready to process messages).

**Arguments**:

- `process`: agent subprocess.
- `timeout`: the timeout to wait for launch to complete

**Returns**:

bool indicating status

<a name="aea.test_tools.test_cases.BaseAEATestCase.invoke"></a>
#### invoke

```python
 | @classmethod
 | invoke(cls, *args: str) -> Result
```

Call the cli command.

<a name="aea.test_tools.test_cases.BaseAEATestCase.load_agent_config"></a>
#### load`_`agent`_`config

```python
 | @classmethod
 | load_agent_config(cls, agent_name: str) -> AgentConfig
```

Load agent configuration.

<a name="aea.test_tools.test_cases.BaseAEATestCase.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls) -> None
```

Set up the test class.

<a name="aea.test_tools.test_cases.BaseAEATestCase.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls) -> None
```

Teardown the test.

<a name="aea.test_tools.test_cases.AEATestCaseEmpty"></a>
## AEATestCaseEmpty Objects

```python
class AEATestCaseEmpty(BaseAEATestCase)
```

Test case for a default AEA project.

This test case will create a default AEA project.

<a name="aea.test_tools.test_cases.AEATestCaseEmpty.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls) -> None
```

Set up the test class.

<a name="aea.test_tools.test_cases.AEATestCaseEmpty.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls) -> None
```

Teardown the test class.

<a name="aea.test_tools.test_cases.AEATestCaseEmptyFlaky"></a>
## AEATestCaseEmptyFlaky Objects

```python
class AEATestCaseEmptyFlaky(AEATestCaseEmpty)
```

Test case for a default AEA project.

This test case will create a default AEA project.

Use for flaky tests with the flaky decorator.

<a name="aea.test_tools.test_cases.AEATestCaseEmptyFlaky.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls) -> None
```

Set up the test class.

<a name="aea.test_tools.test_cases.AEATestCaseEmptyFlaky.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls) -> None
```

Teardown the test class.

<a name="aea.test_tools.test_cases.AEATestCaseMany"></a>
## AEATestCaseMany Objects

```python
class AEATestCaseMany(BaseAEATestCase)
```

Test case for many AEA projects.

<a name="aea.test_tools.test_cases.AEATestCaseMany.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls) -> None
```

Set up the test class.

<a name="aea.test_tools.test_cases.AEATestCaseMany.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls) -> None
```

Teardown the test class.

<a name="aea.test_tools.test_cases.AEATestCaseManyFlaky"></a>
## AEATestCaseManyFlaky Objects

```python
class AEATestCaseManyFlaky(AEATestCaseMany)
```

Test case for many AEA projects which are flaky.

Use for flaky tests with the flaky decorator.

<a name="aea.test_tools.test_cases.AEATestCaseManyFlaky.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls) -> None
```

Set up the test class.

<a name="aea.test_tools.test_cases.AEATestCaseManyFlaky.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls) -> None
```

Teardown the test class.

<a name="aea.test_tools.test_cases.AEATestCase"></a>
## AEATestCase Objects

```python
class AEATestCase(BaseAEATestCase)
```

Test case from an existing AEA project.

Subclass this class and set `path_to_aea` properly. By default,
it is assumed the project is inside the current working directory.

<a name="aea.test_tools.test_cases.AEATestCase.setup_class"></a>
#### setup`_`class

```python
 | @classmethod
 | setup_class(cls) -> None
```

Set up the test class.

<a name="aea.test_tools.test_cases.AEATestCase.teardown_class"></a>
#### teardown`_`class

```python
 | @classmethod
 | teardown_class(cls) -> None
```

Teardown the test class.

