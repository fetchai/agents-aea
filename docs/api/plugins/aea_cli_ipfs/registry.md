<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.registry"></a>

# plugins.aea-cli-ipfs.aea`_`cli`_`ipfs.registry

Module with methods for ipfs registry.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.registry.validate_registry"></a>

#### validate`_`registry

```python
def validate_registry(registry_data: LocalRegistry) -> None
```

Validate local registry data.

**Arguments**:

- `registry_data`: json like object containing registry data.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.registry.write_local_registry"></a>

#### write`_`local`_`registry

```python
def write_local_registry(registry_data: LocalRegistry,
                         registry_path: str = LOCAL_REGISTRY_PATH) -> None
```

Write registry data to file.

**Arguments**:

- `registry_data`: json like object containing registry data.
- `registry_path`: local registry path.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.registry.load_local_registry"></a>

#### load`_`local`_`registry

```python
def load_local_registry(
        registry_path: str = LOCAL_REGISTRY_PATH) -> LocalRegistry
```

Returns local registry data.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.registry.get_ipfs_hash_from_public_id"></a>

#### get`_`ipfs`_`hash`_`from`_`public`_`id

```python
def get_ipfs_hash_from_public_id(
        item_type: str,
        public_id: PublicId,
        registry_path: str = LOCAL_REGISTRY_PATH) -> Optional[str]
```

Get IPFS hash from local registry.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.registry.register_item_to_local_registry"></a>

#### register`_`item`_`to`_`local`_`registry

```python
def register_item_to_local_registry(
        item_type: str,
        public_id: Union[str, PublicId],
        package_hash: str,
        registry_path: str = LOCAL_REGISTRY_PATH) -> None
```

Add PublicId to hash mapping in the local registry.

**Arguments**:

- `item_type`: item type.
- `public_id`: public id of package.
- `package_hash`: hash of package.
- `registry_path`: local registry path.

<a id="plugins.aea-cli-ipfs.aea_cli_ipfs.registry.fetch_ipfs"></a>

#### fetch`_`ipfs

```python
def fetch_ipfs(item_type: str,
               public_id: PublicId,
               dest: str,
               remote: bool = True) -> Optional[Path]
```

Fetch a package from IPFS node.

