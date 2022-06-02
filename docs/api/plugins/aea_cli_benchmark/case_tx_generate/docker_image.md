<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`tx`_`generate.docker`_`image

This module contains testing utilities.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.DockerImage"></a>

## DockerImage Objects

```python
class DockerImage(ABC)
```

A class to wrap interatction with a Docker image.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.DockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: docker.DockerClient)
```

Initialize.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.DockerImage.check_skip"></a>

#### check`_`skip

```python
def check_skip()
```

Check whether the test should be skipped.

By default, nothing happens.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.DockerImage.tag"></a>

#### tag

```python
@property
@abstractmethod
def tag() -> str
```

Return the tag of the image.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.DockerImage.stop_if_already_running"></a>

#### stop`_`if`_`already`_`running

```python
def stop_if_already_running()
```

Stop the running images with the same tag, if any.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.DockerImage.create"></a>

#### create

```python
@abstractmethod
def create() -> Container
```

Instantiate the image in a container.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.DockerImage.wait"></a>

#### wait

```python
@abstractmethod
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is running.

**Arguments**:

- `max_attempts`: max number of attempts.
- `sleep_rate`: the amount of time to sleep between different requests.

**Returns**:

True if the wait was successful, False otherwise.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.GanacheDockerImage"></a>

## GanacheDockerImage Objects

```python
class GanacheDockerImage(DockerImage)
```

Wrapper to Ganache Docker image.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.GanacheDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient,
             addr: str,
             port: int,
             config: Optional[Dict] = None,
             gas_limit: int = 10000000000000)
```

Initialize the Ganache Docker image.

**Arguments**:

- `client`: the Docker client.
- `addr`: the address.
- `port`: the port.
- `config`: optional configuration to command line.
- `gas_limit`: gas limit.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.GanacheDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the image tag.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.GanacheDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.GanacheDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.FetchLedgerDockerImage"></a>

## FetchLedgerDockerImage Objects

```python
class FetchLedgerDockerImage(DockerImage)
```

Wrapper to Fetch ledger Docker image.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.FetchLedgerDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient,
             addr: str,
             port: int,
             tag: str,
             config: Optional[Dict] = None)
```

Initialize the Fetch ledger Docker image.

**Arguments**:

- `client`: the Docker client.
- `addr`: the address.
- `port`: the port.
- `tag`: image tag
- `config`: optional configuration to command line.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.FetchLedgerDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the image tag.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.FetchLedgerDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.docker_image.FetchLedgerDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

