<a id="aea.test_tools.docker_image"></a>

# aea.test`_`tools.docker`_`image

This module contains testing utilities.

<a id="aea.test_tools.docker_image.DockerImage"></a>

## DockerImage Objects

```python
class DockerImage(ABC)
```

A class to wrap interaction with a Docker image.

<a id="aea.test_tools.docker_image.DockerImage.__init__"></a>

#### `__`init`__`

```python
def __init__(client: DockerClient)
```

Initialize.

<a id="aea.test_tools.docker_image.DockerImage.check_skip"></a>

#### check`_`skip

```python
def check_skip() -> None
```

Check whether the test should be skipped.

By default, nothing happens.

<a id="aea.test_tools.docker_image.DockerImage.tag"></a>

#### tag

```python
@property
@abstractmethod
def tag() -> str
```

Return the tag of the image.

<a id="aea.test_tools.docker_image.DockerImage.stop_if_already_running"></a>

#### stop`_`if`_`already`_`running

```python
def stop_if_already_running() -> None
```

Stop the running images with the same tag, if any.

<a id="aea.test_tools.docker_image.DockerImage.create"></a>

#### create

```python
@abstractmethod
def create() -> Container
```

Instantiate the image in a container.

<a id="aea.test_tools.docker_image.DockerImage.wait"></a>

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

<a id="aea.test_tools.docker_image.launch_image"></a>

#### launch`_`image

```python
def launch_image(image: DockerImage,
                 timeout: float = 2.0,
                 max_attempts: int = 10) -> Generator
```

Launch image.

