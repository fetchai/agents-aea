<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.docker_images"></a>

# plugins.aea-ledger-fetchai.aea`_`ledger`_`fetchai.test`_`tools.docker`_`images

This module contains testing utilities.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.docker_images.FetchLedgerDockerImage"></a>

## FetchLedgerDockerImage Objects

```python
class FetchLedgerDockerImage(DockerImage)
```

Wrapper to Fetch ledger Docker image.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.docker_images.FetchLedgerDockerImage.__init__"></a>

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
- `tag`: the tag
- `config`: optional configuration to command line.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.docker_images.FetchLedgerDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the image tag.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.docker_images.FetchLedgerDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="plugins.aea-ledger-fetchai.aea_ledger_fetchai.test_tools.docker_images.FetchLedgerDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

