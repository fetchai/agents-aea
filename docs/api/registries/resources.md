<a name=".aea.registries.resources"></a>
## aea.registries.resources

This module contains the resources class.

<a name=".aea.registries.resources.Resources"></a>
### Resources

```python
class Resources()
```

This class implements the object that holds the resources of an AEA.

<a name=".aea.registries.resources.Resources.__init__"></a>
#### `__`init`__`

```python
 | __init__(directory: Optional[Union[str, os.PathLike]] = None)
```

Instantiate the resources.

**Arguments**:

- `directory`: the path to the directory which contains the resources
(skills, connections and protocols)

<a name=".aea.registries.resources.Resources.directory"></a>
#### directory

```python
 | @property
 | directory() -> str
```

Get the directory.

<a name=".aea.registries.resources.Resources.load"></a>
#### load

```python
 | load(agent_context: AgentContext) -> None
```

Load all the resources.

Performs the following:

- loads the agent configuration
- populates the protocols registry
- calls populate_skills()

**Arguments**:

- `agent_context`: the agent context

<a name=".aea.registries.resources.Resources.populate_skills"></a>
#### populate`_`skills

```python
 | populate_skills(directory: str, agent_context: AgentContext, allowed_skills: Optional[Set[PublicId]] = None) -> None
```

Populate skills.

Processes all allowed_skills in the directory and calls add_skill() with them.

**Arguments**:

- `directory`: the agent's resources directory.
- `agent_context`: the agent's context object
- `allowed_skills`: an optional set of allowed skills (public ids).
If None, every skill is allowed.

**Returns**:

None

<a name=".aea.registries.resources.Resources.add_skill"></a>
#### add`_`skill

```python
 | add_skill(skill: Skill) -> None
```

Add a skill to the set of resources.

**Arguments**:

- `skill`: a skill

**Returns**:

None

<a name=".aea.registries.resources.Resources.add_protocol"></a>
#### add`_`protocol

```python
 | add_protocol(protocol: Protocol) -> None
```

Add a protocol to the set of resources.

**Arguments**:

- `protocol`: a protocol

**Returns**:

None

<a name=".aea.registries.resources.Resources.get_skill"></a>
#### get`_`skill

```python
 | get_skill(skill_id: SkillId) -> Optional[Skill]
```

Get the skill.

<a name=".aea.registries.resources.Resources.get_all_skills"></a>
#### get`_`all`_`skills

```python
 | get_all_skills() -> List[Skill]
```

Get the list of all the skills.

**Returns**:

the list of skills.

<a name=".aea.registries.resources.Resources.remove_skill"></a>
#### remove`_`skill

```python
 | remove_skill(skill_id: SkillId) -> None
```

Remove a skill from the set of resources.

**Arguments**:

- `skill_id`: the skill id for the skill to be removed.

<a name=".aea.registries.resources.Resources.get_handler"></a>
#### get`_`handler

```python
 | get_handler(protocol_id: ProtocolId, skill_id: SkillId) -> Optional[Handler]
```

Get a specific handler.

**Arguments**:

- `protocol_id`: the protocol id the handler is handling
- `skill_id`: the skill id of the handler's skill

**Returns**:

the handler

<a name=".aea.registries.resources.Resources.get_handlers"></a>
#### get`_`handlers

```python
 | get_handlers(protocol_id: ProtocolId) -> List[Handler]
```

Get all handlers for a given protocol.

**Arguments**:

- `protocol_id`: the protocol id the handler is handling

**Returns**:

the list of handlers matching the protocol

<a name=".aea.registries.resources.Resources.get_behaviours"></a>
#### get`_`behaviours

```python
 | get_behaviours() -> List[Behaviour]
```

Get all behaviours.

**Returns**:

a list of behaviours

<a name=".aea.registries.resources.Resources.get_protocol"></a>
#### get`_`protocol

```python
 | get_protocol(protocol_id: ProtocolId) -> Optional[Protocol]
```

Get protocol for given protocol id.

**Returns**:

a protocol

<a name=".aea.registries.resources.Resources.setup"></a>
#### setup

```python
 | setup() -> None
```

Set up the resources.

Calls setup on all resources.

**Returns**:

None

<a name=".aea.registries.resources.Resources.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Teardown the resources.

Calls teardown on all resources.

**Returns**:

None

