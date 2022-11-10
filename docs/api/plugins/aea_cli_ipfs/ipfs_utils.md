<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils"></a>

# plugins.aea-cli-ipfs.aea`_`cli`_`ipfs.ipfs`_`utils

Ipfs utils for `ipfs cli command`.

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
def __init__() -> None
```

Initialise IPFS daemon.

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

Terminate the ipfs daemon.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.BaseIPFSToolException"></a>

## BaseIPFSToolException Objects

```python
class BaseIPFSToolException(Exception)
```

Base ipfs tool exception.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.RemoveError"></a>

## RemoveError Objects

```python
class RemoveError(BaseIPFSToolException)
```

Exception on remove.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.PublishError"></a>

## PublishError Objects

```python
class PublishError(BaseIPFSToolException)
```

Exception on publish.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.NodeError"></a>

## NodeError Objects

```python
class NodeError(BaseIPFSToolException)
```

Exception for node connection check.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.DownloadError"></a>

## DownloadError Objects

```python
class DownloadError(BaseIPFSToolException)
```

Exception on download failed.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool"></a>

## IPFSTool Objects

```python
class IPFSTool()
```

IPFS tool to add, publish, remove, download directories.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.__init__"></a>

#### `__`init`__`

```python
def __init__(client_options: Optional[Dict] = None)
```

Init tool.

**Arguments**:

- `client_options`: dict, options for ipfshttpclient instance.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.add"></a>

#### add

```python
def add(dir_path: str, pin: bool = True) -> Tuple[str, str, List]
```

Add directory to ipfs.

It wraps into directory.

**Arguments**:

- `dir_path`: str, path to dir to publish
- `pin`: bool, pin object or not

**Returns**:

dir name published, hash, list of items processed

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

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.download"></a>

#### download

```python
def download(hash_id: str, target_dir: str, fix_path: bool = True) -> None
```

Download dir by it's hash.

**Arguments**:

- `hash_id`: str. hash of file to download
- `target_dir`: str. directory to place downloaded
- `fix_path`: bool. default True. on download don't wrap result in to hash_id directory.

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

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.ipfs_utils.IPFSTool.chec_ipfs_node_running"></a>

#### chec`_`ipfs`_`node`_`running

```python
def chec_ipfs_node_running() -> None
```

Check ipfs node running.

