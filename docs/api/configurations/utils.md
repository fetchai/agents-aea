<a id="aea.configurations.utils"></a>

# aea.configurations.utils

AEA configuration utils.

<a id="aea.configurations.utils.replace_component_ids"></a>

#### replace`_`component`_`ids

```python
@singledispatch
def replace_component_ids(
        _arg: PackageConfiguration,
        _replacements: Dict[ComponentType, Dict[PublicId, PublicId]]) -> None
```

Update public id references in a package configuration.

This depends on the actual configuration being considered.

<a id="aea.configurations.utils._"></a>

#### `_`

```python
@replace_component_ids.register(AgentConfig)
def _(arg: AgentConfig, replacements: Dict[ComponentType,
                                           Dict[PublicId, PublicId]]) -> None
```

Replace references in agent configuration.

It breaks down in:
1) replace public ids in 'protocols', 'connections', 'contracts' and 'skills';
2) replace public ids in default routing;
3) replace public id of default connection;
4) replace custom component configurations.

**Arguments**:

- `arg`: the agent configuration.
- `replacements`: the replacement mapping.

<a id="aea.configurations.utils._"></a>

#### `_`

```python
@replace_component_ids.register(ProtocolConfig)
def _(_arg: ProtocolConfig,
      _replacements: Dict[ComponentType, Dict[PublicId, PublicId]]) -> None
```

Do nothing - protocols have no references.

<a id="aea.configurations.utils._"></a>

#### `_`

```python
@replace_component_ids.register(ConnectionConfig)
def _(arg: ConnectionConfig,
      replacements: Dict[ComponentType, Dict[PublicId, PublicId]]) -> None
```

Replace references in a connection configuration.

<a id="aea.configurations.utils._"></a>

#### `_`

```python
@replace_component_ids.register(ContractConfig)
def _(_arg: ContractConfig,
      _replacements: Dict[ComponentType, Dict[PublicId, PublicId]]) -> None
```

Do nothing - contracts have no references.

<a id="aea.configurations.utils._"></a>

#### `_`

```python
@replace_component_ids.register(SkillConfig)
def _(arg: SkillConfig, replacements: Dict[ComponentType,
                                           Dict[PublicId, PublicId]]) -> None
```

Replace references in a skill configuration.

<a id="aea.configurations.utils.get_latest_component_id_from_prefix"></a>

#### get`_`latest`_`component`_`id`_`from`_`prefix

```python
def get_latest_component_id_from_prefix(
        agent_config: AgentConfig,
        component_prefix: PackageIdPrefix) -> Optional[ComponentId]
```

Get component id with the greatest version in an agent configuration given its prefix.

**Arguments**:

- `agent_config`: the agent configuration.
- `component_prefix`: the package prefix.

**Returns**:

the package id with the greatest version, or None if not found.

