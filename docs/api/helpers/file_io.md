<a id="aea.helpers.file_io"></a>

# aea.helpers.file`_`io

Read to and write from file with envelopes.

<a id="aea.helpers.file_io.lock_file"></a>

#### lock`_`file

```python
@contextmanager
def lock_file(file_descriptor: IO[bytes],
              logger: Logger = _default_logger) -> Generator
```

Lock file in context manager.

**Arguments**:

- `file_descriptor`: file descriptor of file to lock.
- `logger`: the logger.

**Returns**:

generator

<a id="aea.helpers.file_io.write_envelope"></a>

#### write`_`envelope

```python
def write_envelope(envelope: Envelope,
                   file_pointer: IO[bytes],
                   separator: bytes = SEPARATOR,
                   logger: Logger = _default_logger) -> None
```

Write envelope to file.

<a id="aea.helpers.file_io.write_with_lock"></a>

#### write`_`with`_`lock

```python
def write_with_lock(file_pointer: IO[bytes],
                    data: Union[bytes],
                    logger: Logger = _default_logger) -> None
```

Write bytes to file protected with file lock.

<a id="aea.helpers.file_io.envelope_from_bytes"></a>

#### envelope`_`from`_`bytes

```python
def envelope_from_bytes(
        bytes_: bytes,
        separator: bytes = SEPARATOR,
        logger: Logger = _default_logger) -> Optional[Envelope]
```

Decode bytes to get the envelope.

**Arguments**:

- `bytes_`: the encoded envelope
- `separator`: the separator used
- `logger`: the logger

**Returns**:

Envelope

