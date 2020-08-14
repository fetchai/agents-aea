<a name="aea.helpers.pipe"></a>
# aea.helpers.pipe

Portable pipe implementation for Linux, MacOS, and Windows.

<a name="aea.helpers.pipe.LocalPortablePipe"></a>
## LocalPortablePipe Objects

```python
class LocalPortablePipe(ABC)
```

Multi-platform interprocess communication channel

<a name="aea.helpers.pipe.LocalPortablePipe.connect"></a>
#### connect

```python
 | @abstractmethod
 | async connect(timeout=PIPE_CONN_TIMEOUT) -> bool
```

Setup the communication channel with the other process

<a name="aea.helpers.pipe.LocalPortablePipe.write"></a>
#### write

```python
 | @abstractmethod
 | async write(data: bytes) -> None
```

Write `data` bytes to the other end of the channel
Will first write the size than the actual data

<a name="aea.helpers.pipe.LocalPortablePipe.read"></a>
#### read

```python
 | @abstractmethod
 | async read() -> Optional[bytes]
```

Read bytes from the other end of the channel
Will first read the size than the actual data

<a name="aea.helpers.pipe.LocalPortablePipe.close"></a>
#### close

```python
 | @abstractmethod
 | async close() -> None
```

Close the communication channel

<a name="aea.helpers.pipe.LocalPortablePipe.in_path"></a>
#### in`_`path

```python
 | @property
 | @abstractmethod
 | in_path() -> str
```

Returns the rendezvous point for incoming communication

<a name="aea.helpers.pipe.LocalPortablePipe.out_path"></a>
#### out`_`path

```python
 | @property
 | @abstractmethod
 | out_path() -> str
```

Returns the rendezvous point for outgoing communication

<a name="aea.helpers.pipe.TCPSocketPipe"></a>
## TCPSocketPipe Objects

```python
class TCPSocketPipe(LocalPortablePipe)
```

Interprocess communication implementation using tcp sockets

<a name="aea.helpers.pipe.PosixNamedPipe"></a>
## PosixNamedPipe Objects

```python
class PosixNamedPipe(LocalPortablePipe)
```

Interprocess communication implementation using Posix named pipes

<a name="aea.helpers.pipe.PosixNamedPipe.write"></a>
#### write

```python
 | async write(data: bytes) -> None
```

Write to the writer stream.

**Arguments**:

- `data`: data to write to stream

<a name="aea.helpers.pipe.PosixNamedPipe.read"></a>
#### read

```python
 | async read() -> Optional[bytes]
```

Read from the reader stream.

**Returns**:

bytes

<a name="aea.helpers.pipe.make_pipe"></a>
#### make`_`pipe

```python
make_pipe(logger: logging.Logger = _default_logger) -> LocalPortablePipe
```

Build a portable bidirectional Interprocess Communication Channel

