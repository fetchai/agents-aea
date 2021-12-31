<a name="aea.helpers.sym_link"></a>
# aea.helpers.sym`_`link

Sym link implementation for Linux, MacOS, and Windows.

<a name="aea.helpers.sym_link.make_symlink"></a>
#### make`_`symlink

```python
make_symlink(link_name: str, target: str) -> None
```

Make a symbolic link, cross platform.

**Arguments**:

- `link_name`: the link name.
- `target`: the target.

<a name="aea.helpers.sym_link.cd"></a>
#### cd

```python
@contextlib.contextmanager
cd(path: Path) -> Generator
```

Change directory with context manager.

<a name="aea.helpers.sym_link.create_symlink"></a>
#### create`_`symlink

```python
create_symlink(link_path: Path, target_path: Path, root_path: Path) -> int
```

Change directory and call the cross-platform script.

The working directory must be the parent of the symbolic link name
when executing 'create_symlink_crossplatform.sh'. Hence, we
need to translate target_path into the relative path from the
symbolic link directory to the target directory.

So:
1) from link_path, extract the number of jumps to the parent directory
in order to reach the repository root directory, and chain many "../" paths.
2) from target_path, compute the relative path to the root
3) relative_target_path is just the concatenation of the results from step (1) and (2).


For instance, given
- link_path: './directory_1//symbolic_link
- target_path: './directory_2/target_path

we want to compute:
- link_path: 'symbolic_link' (just the last bit)
- relative_target_path: '../../directory_1/target_path'

The resulting command on UNIX systems will be:

    cd directory_1 && ln -s ../../directory_1/target_path symbolic_link

**Arguments**:

- `link_path`: the source path
- `target_path`: the target path
- `root_path`: the root path

**Returns**:

exit code

