<a name="aea.crypto.plugin"></a>
# aea.crypto.plugin

Implementation of plug-in mechanism for cryptos.

<a name="aea.crypto.plugin.Plugin"></a>
## Plugin Objects

```python
class Plugin()
```

Class that implements an AEA plugin.

<a name="aea.crypto.plugin.Plugin.__init__"></a>
#### `__`init`__`

```python
 | __init__(group: str, entry_point: EntryPoint)
```

Initialize the plugin.

**Arguments**:

- `group`: the group the plugin belongs to.
- `entry_point`: the entrypoint.

<a name="aea.crypto.plugin.Plugin.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the plugin identifier.

<a name="aea.crypto.plugin.Plugin.group"></a>
#### group

```python
 | @property
 | group() -> str
```

Get the group.

<a name="aea.crypto.plugin.Plugin.attr"></a>
#### attr

```python
 | @property
 | attr() -> str
```

Get the class name.

<a name="aea.crypto.plugin.Plugin.entry_point_path"></a>
#### entry`_`point`_`path

```python
 | @property
 | entry_point_path() -> str
```

Get the entry point path.

<a name="aea.crypto.plugin.load_all_plugins"></a>
#### load`_`all`_`plugins

```python
load_all_plugins(is_raising_exception: bool = True) -> None
```

Load all plugins.

