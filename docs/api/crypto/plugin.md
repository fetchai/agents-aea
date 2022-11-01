<a id="aea.crypto.plugin"></a>

# aea.crypto.plugin

Implementation of plug-in mechanism for cryptos.

<a id="aea.crypto.plugin.Plugin"></a>

## Plugin Objects

```python
class Plugin()
```

Class that implements an AEA plugin.

<a id="aea.crypto.plugin.Plugin.__init__"></a>

#### `__`init`__`

```python
def __init__(group: str, entry_point: EntryPoint)
```

Initialize the plugin.

**Arguments**:

- `group`: the group the plugin belongs to.
- `entry_point`: the entrypoint.

<a id="aea.crypto.plugin.Plugin.name"></a>

#### name

```python
@property
def name() -> str
```

Get the plugin identifier.

<a id="aea.crypto.plugin.Plugin.group"></a>

#### group

```python
@property
def group() -> str
```

Get the group.

<a id="aea.crypto.plugin.Plugin.attr"></a>

#### attr

```python
@property
def attr() -> str
```

Get the class name.

<a id="aea.crypto.plugin.Plugin.entry_point_path"></a>

#### entry`_`point`_`path

```python
@property
def entry_point_path() -> str
```

Get the entry point path.

<a id="aea.crypto.plugin.load_all_plugins"></a>

#### load`_`all`_`plugins

```python
def load_all_plugins(is_raising_exception: bool = True) -> None
```

Load all plugins.

