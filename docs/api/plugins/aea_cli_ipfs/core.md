<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.core"></a>
# plugins.aea-cli-ipfs.aea`_`cli`_`ipfs.core

Core components for `ipfs cli command`.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.core.ipfs"></a>
#### ipfs

```python
@click.group()
@click.pass_context
ipfs(click_context: click.Context) -> None
```

IPFS Commands

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.core.process_result"></a>
#### process`_`result

```python
@ipfs.resultcallback()
@click.pass_context
process_result(click_context: click.Context, *_: Any) -> None
```

Tear down command group.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.core.add"></a>
#### add

```python
@ipfs.command()
@click.argument(
    "dir_path",
    type=click.Path(
        exists=True, dir_okay=True, file_okay=False, resolve_path=True, readable=True
    ),
    required=False,
)
@click.option("-p", "--publish", is_flag=True)
@click.option("--no-pin", is_flag=True)
@click.pass_context
add(click_context: click.Context, dir_path: Optional[str], publish: bool = False, no_pin: bool = False) -> None
```

Add directory to ipfs, if not directory specified the current one will be added.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.core.remove"></a>
#### remove

```python
@ipfs.command()
@click.argument(
    "hash_", metavar="hash", type=str, required=True,
)
@click.pass_context
remove(click_context: click.Context, hash_: str) -> None
```

Remove a directory from ipfs by it's hash.

<a name="plugins.aea-cli-ipfs.aea_cli_ipfs.core.download"></a>
#### download

```python
@ipfs.command()
@click.argument(
    "hash_", metavar="hash", type=str, required=True,
)
@click.argument(
    "target_dir",
    type=click.Path(dir_okay=True, file_okay=False, resolve_path=True),
    required=False,
)
@click.pass_context
download(click_context: click.Context, hash_: str, target_dir: Optional[str]) -> None
```

Download directory by it's hash, if not target directory specified will use current one.

