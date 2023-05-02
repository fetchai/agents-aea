<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils"></a>

# plugins.aea-cli-ipfs.aea`_`cli`_`ipfs.ipfs`_`utils

Ipfs utils for `ipfs cli command`.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.resolve_addr"></a>

#### resolve`_`addr

```python
def resolve_addr(addr: str) -> Tuple[str, ...]
```

Multiaddr resolver.

**Arguments**:

- `addr`: multiaddr string.

**Returns**:

http URL

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.addr_to_url"></a>

#### addr`_`to`_`url

```python
def addr_to_url(addr: str) -> str
```

Convert address to url.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.is_remote_addr"></a>

#### is`_`remote`_`addr

```python
def is_remote_addr(host: str) -> bool
```

Check if addr is remote or local.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon"></a>

## IPFSDaemon Objects

```python
class IPFSDaemon()
```

Set up the IPFS daemon.

**Raises**:

- `Exception`: if IPFS is not installed.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.__init__"></a>

#### `__`init`__`

```python
def __init__(node_url: str = "http://127.0.0.1:5001", is_remote: bool = False)
```

Initialise IPFS daemon.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.is_started_externally"></a>

#### is`_`started`_`externally

```python
def is_started_externally() -> bool
```

Check daemon was started externally.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.is_started_internally"></a>

#### is`_`started`_`internally

```python
def is_started_internally() -> bool
```

Check daemon was started internally.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.is_started"></a>

#### is`_`started

```python
def is_started() -> bool
```

Check daemon was started.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.start"></a>

#### start

```python
def start() -> None
```

Run the ipfs daemon.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.stop"></a>

#### stop

```python
def stop() -> None
```

Terminate the ipfs daemon if it was started internally.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.__enter__"></a>

#### `__`enter`__`

```python
def __enter__() -> None
```

Run the ipfs daemon.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.__exit__"></a>

#### `__`exit`__`

```python
def __exit__(exc_type, exc_val, exc_tb) -> None
```

Terminate the ipfs daemon.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool"></a>

## IPFSTool Objects

```python
class IPFSTool()
```

IPFS tool to add, publish, remove, download directories.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.__init__"></a>

#### `__`init`__`

```python
def __init__(addr: Optional[str] = None, base: str = DEFAULT_IPFS_URI_BASE)
```

Init tool.

**Arguments**:

- `addr`: multiaddr string for IPFS client.
- `base`: API base for IPFS client.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.addr"></a>

#### addr

```python
@property
def addr() -> str
```

Node address

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.is_a_package"></a>

#### is`_`a`_`package

```python
def is_a_package(package_hash: str) -> bool
```

Checks if a package with `package_hash` is pinned or not

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.all_pins"></a>

#### all`_`pins

```python
def all_pins(recursive_only: bool = True) -> Set[str]
```

Returns a list of all pins.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.add_bytes"></a>

#### add`_`bytes

```python
def add_bytes(data: bytes, **kwargs) -> str
```

Add bytes data to ipfs.

**Arguments**:

- `data`: bytes
- `kwargs`: options passed to request library

**Returns**:

hash

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.add"></a>

#### add

```python
def add(dir_path: str,
        pin: bool = True,
        recursive: bool = True,
        wrap_with_directory: bool = True) -> Tuple[str, str, List]
```

Add directory to ipfs.

It wraps into directory.

**Arguments**:

- `dir_path`: str, path to dir to publish
- `pin`: bool, pin object or not
- `recursive`: bool, publish dierctory recursively or not
- `wrap_with_directory`: bool, wrap object with directory or not

**Returns**:

dir name published, hash, list of items processed

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.pin"></a>

#### pin

```python
def pin(hash_id: str) -> Dict
```

Pin content with hash_id

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.remove"></a>

#### remove

```python
def remove(hash_id: str) -> Dict
```

Remove dir added by it's hash.

**Arguments**:

- `hash_id`: str. hash of dir to remove

**Returns**:

dict with unlinked items.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.remove_unpinned_files"></a>

#### remove`_`unpinned`_`files

```python
def remove_unpinned_files() -> None
```

Remove dir added by it's hash.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.download"></a>

#### download

```python
def download(hash_id: str,
             target_dir: Union[str, Path],
             fix_path: bool = True,
             attempts: int = 5) -> str
```

Download dir by its hash.

**Arguments**:

- `hash_id`: str. hash of file or package to download
- `target_dir`: Union[str, Path]. directory to place downloaded
- `fix_path`: bool. default True. on download don't wrap result in to hash_id directory.
- `attempts`: int. default 5. How often to attempt the download.

**Returns**:

downloaded path

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.publish"></a>

#### publish

```python
def publish(hash_id: str) -> Dict
```

Publish directory by it's hash id.

**Arguments**:

- `hash_id`: hash of the directory to publish.

**Returns**:

dict of names it was publish for.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.check_ipfs_node_running"></a>

#### check`_`ipfs`_`node`_`running

```python
def check_ipfs_node_running() -> None
```

Check ipfs node running.

