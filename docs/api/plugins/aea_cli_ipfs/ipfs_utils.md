<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils"></a>
# plugins.aea-cli-ipfs.aea`_`cli`_`ipfs.ipfs`_`utils

Ipfs utils for `ipfs cli command`.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.resolve_addr"></a>
#### resolve`_`addr

```python
resolve_addr(addr: str) -> Tuple[str, ...]
```

Multiaddr resolver.

**Arguments**:

- `addr`: multiaddr string.

**Returns**:

http URL

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.addr_to_url"></a>
#### addr`_`to`_`url

```python
addr_to_url(addr: str) -> str
```

Convert address to url.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon"></a>
## IPFSDaemon Objects

```python
class IPFSDaemon()
```

Set up the IPFS daemon.

**Raises**:

- `Exception`: if IPFS is not installed.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.__init__"></a>
#### `__`init`__`

```python
 | __init__(offline: bool = False, api_url: str = "http://127.0.0.1:5001")
```

Initialise IPFS daemon.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.is_started_externally"></a>
#### is`_`started`_`externally

```python
 | is_started_externally() -> bool
```

Check daemon was started externally.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.is_started_internally"></a>
#### is`_`started`_`internally

```python
 | is_started_internally() -> bool
```

Check daemon was started internally.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.is_started"></a>
#### is`_`started

```python
 | is_started() -> bool
```

Check daemon was started.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.start"></a>
#### start

```python
 | start() -> None
```

Run the ipfs daemon.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.stop"></a>
#### stop

```python
 | stop() -> None
```

Terminate the ipfs daemon if it was started internally.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.__enter__"></a>
#### `__`enter`__`

```python
 | __enter__() -> None
```

Run the ipfs daemon.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSDaemon.__exit__"></a>
#### `__`exit`__`

```python
 | __exit__(exc_type, exc_val, exc_tb) -> None
```

Terminate the ipfs daemon.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.BaseIPFSToolException"></a>
## BaseIPFSToolException Objects

```python
class BaseIPFSToolException(Exception)
```

Base ipfs tool exception.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.RemoveError"></a>
## RemoveError Objects

```python
class RemoveError(BaseIPFSToolException)
```

Exception on remove.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.PublishError"></a>
## PublishError Objects

```python
class PublishError(BaseIPFSToolException)
```

Exception on publish.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.NodeError"></a>
## NodeError Objects

```python
class NodeError(BaseIPFSToolException)
```

Exception for node connection check.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.DownloadError"></a>
## DownloadError Objects

```python
class DownloadError(BaseIPFSToolException)
```

Exception on download failed.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool"></a>
## IPFSTool Objects

```python
class IPFSTool()
```

IPFS tool to add, publish, remove, download directories.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.__init__"></a>
#### `__`init`__`

```python
 | __init__(addr: Optional[str] = None, offline: bool = True)
```

Init tool.

**Arguments**:

- `addr`: multiaddr string for IPFS client.
- `offline`: ipfs mode.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.addr"></a>
#### addr

```python
 | @property
 | addr() -> str
```

Node address

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.add"></a>
#### add

```python
 | add(dir_path: str, pin: bool = True) -> Tuple[str, str, List]
```

Add directory to ipfs.

It wraps into directory.

**Arguments**:

- `dir_path`: str, path to dir to publish
- `pin`: bool, pin object or not

**Returns**:

dir name published, hash, list of items processed

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.remove"></a>
#### remove

```python
 | remove(hash_id: str) -> Dict
```

Remove dir added by it's hash.

**Arguments**:

- `hash_id`: str. hash of dir to remove

**Returns**:

dict with unlinked items.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.download"></a>
#### download

```python
 | download(hash_id: str, target_dir: str, fix_path: bool = True) -> None
```

Download dir by it's hash.

**Arguments**:

- `hash_id`: str. hash of file to download
- `target_dir`: str. directory to place downloaded
- `fix_path`: bool. default True. on download don't wrap result in to hash_id directory.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.publish"></a>
#### publish

```python
 | publish(hash_id: str) -> Dict
```

Publish directory by it's hash id.

**Arguments**:

- `hash_id`: hash of the directory to publish.

**Returns**:

dict of names it was publish for.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.check_ipfs_node_running"></a>
#### check`_`ipfs`_`node`_`running

```python
 | check_ipfs_node_running() -> None
```

Check ipfs node running.

