<a id="aea.test_tools.acn_image"></a>

# aea.test`_`tools.acn`_`image

ACN Docker Image.

<a id="aea.test_tools.acn_image.ACNNodeDockerImage"></a>

## ACNNodeDockerImage Objects

```python
class ACNNodeDockerImage(DockerImage)
```

Wrapper to ACNNode Docker image.

<a id="aea.test_tools.acn_image.ACNNodeDockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient, config: Dict)
```

Initialize the ACNNode Docker image.

**Arguments**:

- `client`: the Docker client.
- `config`: optional configuration to command line.

<a id="aea.test_tools.acn_image.ACNNodeDockerImage.tag"></a>

#### tag

```python
@property
def tag() -> str
```

Get the image tag.

<a id="aea.test_tools.acn_image.ACNNodeDockerImage.ports"></a>

#### ports

```python
@property
def ports() -> List[str]
```

Ports

<a id="aea.test_tools.acn_image.ACNNodeDockerImage.create"></a>

#### create

```python
def create() -> Container
```

Create the container.

<a id="aea.test_tools.acn_image.ACNNodeDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait until the image is up.

<a id="aea.test_tools.acn_image.ACNWithBootstrappedEntryNodesDockerImage"></a>

## ACNWithBootstrappedEntryNodesDockerImage Objects

```python
class ACNWithBootstrappedEntryNodesDockerImage(ACNNodeDockerImage)
```

ACN with bootstrapped entry nodes

<a id="aea.test_tools.acn_image.ACNWithBootstrappedEntryNodesDockerImage.create"></a>

#### create

```python
def create() -> List[Container]
```

Instantiate the image in many containers, parametrized.

<a id="aea.test_tools.acn_image.ACNWithBootstrappedEntryNodesDockerImage.wait"></a>

#### wait

```python
def wait(max_attempts: int = 15, sleep_rate: float = 1.0) -> bool
```

Wait - this is container specific (using self._config) so doesn't work

