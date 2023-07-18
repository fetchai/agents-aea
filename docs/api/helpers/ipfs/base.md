<a id="aea.helpers.ipfs.base"></a>

# aea.helpers.ipfs.base

This module contains helper methods and classes for the 'aea' package.

<a id="aea.helpers.ipfs.base.SHA256_ID"></a>

#### SHA256`_`ID

0x12

<a id="aea.helpers.ipfs.base.LEN_SHA256"></a>

#### LEN`_`SHA256

0x20

<a id="aea.helpers.ipfs.base.chunks"></a>

#### chunks

```python
def chunks(data: Sized, size: int) -> Generator
```

Yield successivesize chunks from data.

<a id="aea.helpers.ipfs.base.IPFSHashOnly"></a>

## IPFSHashOnly Objects

```python
class IPFSHashOnly()
```

A helper class which allows construction of an IPFS hash without interacting with an IPFS daemon.

<a id="aea.helpers.ipfs.base.IPFSHashOnly.get"></a>

#### get

```python
@classmethod
def get(cls, file_path: str, wrap: bool = True, cid_v1: bool = True) -> str
```

Get the IPFS hash.

<a id="aea.helpers.ipfs.base.IPFSHashOnly.hash_file"></a>

#### hash`_`file

```python
@classmethod
def hash_file(cls,
              file_path: str,
              wrap: bool = True,
              cid_v1: bool = True) -> str
```

Get the IPFS hash for a single file.

**Arguments**:

- `file_path`: the file path
- `wrap`: whether to wrap the content in wrapper node or not
- `cid_v1`: whether to use CID v1 hashes

**Returns**:

the ipfs hash

<a id="aea.helpers.ipfs.base.IPFSHashOnly.hash_bytes"></a>

#### hash`_`bytes

```python
@classmethod
def hash_bytes(cls,
               data: bytes,
               wrap: bool = True,
               cid_v1: bool = True,
               file_name_if_wrap: Optional[str] = None) -> str
```

Get the IPFS hash for a single file.

**Arguments**:

- `data`: bytes
- `wrap`: whether to wrap the content in wrapper node or not
- `cid_v1`: whether to use CID v1 hashes
- `file_name_if_wrap`: optional str with filename applied if wrap is True

**Returns**:

the ipfs hash

<a id="aea.helpers.ipfs.base.IPFSHashOnly.hash_directory"></a>

#### hash`_`directory

```python
@classmethod
def hash_directory(cls,
                   dir_path: str,
                   wrap: bool = True,
                   cid_v1: bool = True) -> str
```

Get the IPFS hash for a directory.

**Arguments**:

- `dir_path`: the directory path
- `wrap`: whether to wrap the content in wrapper node or not
- `cid_v1`: whether to use CID v1 hashes

**Returns**:

the ipfs hash

<a id="aea.helpers.ipfs.base.IPFSHashOnly.create_link"></a>

#### create`_`link

```python
@staticmethod
def create_link(link_hash: bytes, tsize: int, name: str) -> Any
```

Create PBLink object.

<a id="aea.helpers.ipfs.base.IPFSHashOnly.wrap_in_a_node"></a>

#### wrap`_`in`_`a`_`node

```python
@classmethod
def wrap_in_a_node(cls, link: Any) -> str
```

Wrap content in a wrapper node.

