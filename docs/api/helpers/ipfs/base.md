<a id="aea.helpers.ipfs.base"></a>

# aea.helpers.ipfs.base

This module contains helper methods and classes for the 'aea' package.

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
def get(file_path: str) -> str
```

Get the IPFS hash for a single file.

**Arguments**:

- `file_path`: the file path

**Returns**:

the ipfs hash

