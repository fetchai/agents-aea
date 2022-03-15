<a name="aea.helpers.ipfs.base"></a>
# aea.helpers.ipfs.base

This module contains helper methods and classes for the 'aea' package.

<a name="aea.helpers.ipfs.base.chunks"></a>
#### chunks

```python
chunks(data: Sized, size: int) -> Generator
```

Yield successivesize chunks from data.

<a name="aea.helpers.ipfs.base.IPFSHashOnly"></a>
## IPFSHashOnly Objects

```python
class IPFSHashOnly()
```

A helper class which allows construction of an IPFS hash without interacting with an IPFS daemon.

<a name="aea.helpers.ipfs.base.IPFSHashOnly.get"></a>
#### get

```python
 | @classmethod
 | get(cls, file_path: str, wrap: bool = True) -> str
```

Get the IPFS hash.

<a name="aea.helpers.ipfs.base.IPFSHashOnly.hash_file"></a>
#### hash`_`file

```python
 | @classmethod
 | hash_file(cls, file_path: str, wrap: bool = True) -> str
```

Get the IPFS hash for a single file.

**Arguments**:

- `file_path`: the file path
- `wrap`: weather to wrap the content in wrapper node or not

**Returns**:

the ipfs hash

<a name="aea.helpers.ipfs.base.IPFSHashOnly.hash_directory"></a>
#### hash`_`directory

```python
 | @classmethod
 | hash_directory(cls, dir_path: str, wrap: bool = True) -> str
```

Get the IPFS hash for a directory.

**Arguments**:

- `dir_path`: the directory path
- `wrap`: weather to wrap the content in wrapper node or not

**Returns**:

the ipfs hash

<a name="aea.helpers.ipfs.base.IPFSHashOnly.create_link"></a>
#### create`_`link

```python
 | @staticmethod
 | create_link(link_hash: bytes, tsize: int, name: str) -> Any
```

Create PBLink object.

<a name="aea.helpers.ipfs.base.IPFSHashOnly.wrap_in_a_node"></a>
#### wrap`_`in`_`a`_`node

```python
 | @classmethod
 | wrap_in_a_node(cls, link: Any) -> str
```

Wrap content in a wrapper node.

