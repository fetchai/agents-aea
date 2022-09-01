<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.docker_images"></a>

# plugins.aea-ledger-ethereum.aea`_`ledger`_`ethereum.test`_`tools.docker`_`images

Constants.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.docker_images.GanacheDockerImage"></a>

## GanacheDockerImage Objects

```python
class GanacheDockerImage(DockerImage)
```

Wrapper to Ganache Docker image.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.docker_images.GanacheDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient,
             addr: str,
             port: int,
             config: Optional[Dict] = None,
             gas_limit: str = "0x9184e72a000")
```

Initialize the Ganache Docker image.

**Arguments**:

- `client`: the Docker client.
- `addr`: the address.
- `port`: the port.
- `config`: optional configuration to command line.
- `gas_limit`: the gas limit for blocks.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.docker_images.GanacheDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the image tag.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.docker_images.GanacheDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="plugins.aea-ledger-ethereum.aea_ledger_ethereum.test_tools.docker_images.GanacheDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

