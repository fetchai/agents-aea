<a name=".aea.registries.base"></a>
## aea.registries.base

This module contains registries.

<a name=".aea.registries.base.Registry"></a>
### Registry

```python
class Registry(Generic[ItemId, Item],  ABC)
```

This class implements an abstract registry.

<a name=".aea.registries.base.Registry.register"></a>
#### register

```python
 | @abstractmethod
 | register(item_id: ItemId, item: Item) -> None
```

Register an item.

**Arguments**:

- `item_id`: the public id of the item.
- `item`: the item.

**Returns**:

None
:raises: ValueError if an item is already registered with that item id.

<a name=".aea.registries.base.Registry.unregister"></a>
#### unregister

```python
 | @abstractmethod
 | unregister(item_id: ItemId) -> None
```

Unregister an item.

**Arguments**:

- `item_id`: the public id of the item.

**Returns**:

None
:raises: ValueError if no item registered with that item id.

<a name=".aea.registries.base.Registry.fetch"></a>
#### fetch

```python
 | @abstractmethod
 | fetch(item_id: ItemId) -> Optional[Item]
```

Fetch an item.

**Arguments**:

- `item_id`: the public id of the item.

**Returns**:

the Item

<a name=".aea.registries.base.Registry.fetch_all"></a>
#### fetch`_`all

```python
 | @abstractmethod
 | fetch_all() -> List[Item]
```

Fetch all the items.

**Returns**:

the list of items.

<a name=".aea.registries.base.Registry.setup"></a>
#### setup

```python
 | @abstractmethod
 | setup() -> None
```

Set up registry.

**Returns**:

None

<a name=".aea.registries.base.Registry.teardown"></a>
#### teardown

```python
 | @abstractmethod
 | teardown() -> None
```

Teardown the registry.

**Returns**:

None

<a name=".aea.registries.base.ProtocolRegistry"></a>
### ProtocolRegistry

```python
class ProtocolRegistry(Registry[PublicId, Protocol])
```

This class implements the handlers registry.

<a name=".aea.registries.base.ProtocolRegistry.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Instantiate the registry.

**Returns**:

None

<a name=".aea.registries.base.ProtocolRegistry.register"></a>
#### register

```python
 | register(item_id: PublicId, protocol: Protocol) -> None
```

Register a protocol.

**Arguments**:

- `item_id`: the public id of the protocol.
- `protocol`: the protocol object.

<a name=".aea.registries.base.ProtocolRegistry.unregister"></a>
#### unregister

```python
 | unregister(protocol_id: ProtocolId) -> None
```

Unregister a protocol.

<a name=".aea.registries.base.ProtocolRegistry.fetch"></a>
#### fetch

```python
 | fetch(protocol_id: ProtocolId) -> Optional[Protocol]
```

Fetch the protocol for the envelope.

**Arguments**:

- `protocol_id`: the protocol id

**Returns**:

the protocol id or None if the protocol is not registered

<a name=".aea.registries.base.ProtocolRegistry.fetch_all"></a>
#### fetch`_`all

```python
 | fetch_all() -> List[Protocol]
```

Fetch all the protocols.

<a name=".aea.registries.base.ProtocolRegistry.populate"></a>
#### populate

```python
 | populate(directory: str, allowed_protocols: Optional[Set[PublicId]] = None) -> None
```

Load the handlers as specified in the config and apply consistency checks.

**Arguments**:

- `directory`: the filepath to the agent's resource directory.
- `allowed_protocols`: an optional set of allowed protocols (public ids_.
If None, every protocol is allowed.

**Returns**:

None

<a name=".aea.registries.base.ProtocolRegistry.setup"></a>
#### setup

```python
 | setup() -> None
```

Set up the registry.

**Returns**:

None

<a name=".aea.registries.base.ProtocolRegistry.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Teardown the registry.

**Returns**:

None

<a name=".aea.registries.base.ComponentRegistry"></a>
### ComponentRegistry

```python
class ComponentRegistry(
    Registry[Tuple[SkillId, str], SkillComponentType],  Generic[SkillComponentType])
```

This class implements a generic registry for skill components.

<a name=".aea.registries.base.ComponentRegistry.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Instantiate the registry.

**Returns**:

None

<a name=".aea.registries.base.ComponentRegistry.register"></a>
#### register

```python
 | register(item_id: Tuple[SkillId, str], item: SkillComponentType) -> None
```

Register a item.

**Arguments**:

- `item_id`: a pair (skill id, item name).
- `item`: the item to register.

**Returns**:

None
:raises: ValueError if an item is already registered with that item id.

<a name=".aea.registries.base.ComponentRegistry.unregister"></a>
#### unregister

```python
 | unregister(item_id: Tuple[SkillId, str]) -> None
```

Unregister a item.

**Arguments**:

- `item_id`: a pair (skill id, item name).

**Returns**:

None
:raises: ValueError if no item registered with that item id.

<a name=".aea.registries.base.ComponentRegistry.fetch"></a>
#### fetch

```python
 | fetch(item_id: Tuple[SkillId, str]) -> Optional[SkillComponentType]
```

Fetch an item.

**Arguments**:

- `item_id`: the public id of the item.

**Returns**:

the Item

<a name=".aea.registries.base.ComponentRegistry.fetch_by_skill"></a>
#### fetch`_`by`_`skill

```python
 | fetch_by_skill(skill_id: SkillId) -> List[Item]
```

Fetch all the items of a given skill.

<a name=".aea.registries.base.ComponentRegistry.fetch_all"></a>
#### fetch`_`all

```python
 | fetch_all() -> List[SkillComponentType]
```

Fetch all the items.

<a name=".aea.registries.base.ComponentRegistry.unregister_by_skill"></a>
#### unregister`_`by`_`skill

```python
 | unregister_by_skill(skill_id: SkillId) -> None
```

Unregister all the components by skill.

<a name=".aea.registries.base.ComponentRegistry.setup"></a>
#### setup

```python
 | setup() -> None
```

Set up the items in the registry.

**Returns**:

None

<a name=".aea.registries.base.ComponentRegistry.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Teardown the registry.

**Returns**:

None

<a name=".aea.registries.base.HandlerRegistry"></a>
### HandlerRegistry

```python
class HandlerRegistry(ComponentRegistry[Handler])
```

This class implements the handlers registry.

<a name=".aea.registries.base.HandlerRegistry.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Instantiate the registry.

**Returns**:

None

<a name=".aea.registries.base.HandlerRegistry.register"></a>
#### register

```python
 | register(item_id: Tuple[SkillId, str], item: Handler) -> None
```

Register a handler.

**Arguments**:

- `item_id`: the item id.
- `item`: the handler.

**Returns**:

None

**Raises**:

- `ValueError`: if the protocol is None, or an item with pair (skill_id, protocol_id_ already exists.

<a name=".aea.registries.base.HandlerRegistry.unregister"></a>
#### unregister

```python
 | unregister(item_id: Tuple[SkillId, str]) -> None
```

Unregister a item.

**Arguments**:

- `item_id`: a pair (skill id, item name).

**Returns**:

None
:raises: ValueError if no item is registered with that item id.

<a name=".aea.registries.base.HandlerRegistry.unregister_by_skill"></a>
#### unregister`_`by`_`skill

```python
 | unregister_by_skill(skill_id: SkillId) -> None
```

Unregister all the components by skill.

<a name=".aea.registries.base.HandlerRegistry.fetch_by_protocol"></a>
#### fetch`_`by`_`protocol

```python
 | fetch_by_protocol(protocol_id: ProtocolId) -> List[Handler]
```

Fetch the handler by the pair protocol id and skill id.

**Arguments**:

- `protocol_id`: the protocol id

**Returns**:

the handlers registered for the protocol_id and skill_id

<a name=".aea.registries.base.HandlerRegistry.fetch_by_protocol_and_skill"></a>
#### fetch`_`by`_`protocol`_`and`_`skill

```python
 | fetch_by_protocol_and_skill(protocol_id: ProtocolId, skill_id: SkillId) -> Optional[Handler]
```

Fetch the handler by the pair protocol id and skill id.

**Arguments**:

- `protocol_id`: the protocol id
- `skill_id`: the skill id.

**Returns**:

the handlers registered for the protocol_id and skill_id

<a name=".aea.registries.base.HandlerRegistry.fetch_internal_handler"></a>
#### fetch`_`internal`_`handler

```python
 | fetch_internal_handler(skill_id: SkillId) -> Optional[Handler]
```

Fetch the internal handler.

**Arguments**:

- `skill_id`: the skill id

**Returns**:

the internal handler registered for the skill id

<a name=".aea.registries.base.Resources"></a>
### Resources

```python
class Resources()
```

This class implements the resources of an AEA.

<a name=".aea.registries.base.Resources.__init__"></a>
#### `__`init`__`

```python
 | __init__(directory: Optional[Union[str, os.PathLike]] = None)
```

Instantiate the resources.

<a name=".aea.registries.base.Resources.directory"></a>
#### directory

```python
 | @property
 | directory() -> str
```

Get the directory.

<a name=".aea.registries.base.Resources.load"></a>
#### load

```python
 | load(agent_context: AgentContext) -> None
```

Load all the resources.

<a name=".aea.registries.base.Resources.populate_skills"></a>
#### populate`_`skills

```python
 | populate_skills(directory: str, agent_context: AgentContext, allowed_skills: Optional[Set[PublicId]] = None) -> None
```

Populate skills.

**Arguments**:

- `directory`: the agent's resources directory.
- `agent_context`: the agent's context object
- `allowed_skills`: an optional set of allowed skills (public ids).
If None, every skill is allowed.

**Returns**:

None

<a name=".aea.registries.base.Resources.add_skill"></a>
#### add`_`skill

```python
 | add_skill(skill: Skill)
```

Add a skill to the set of resources.

<a name=".aea.registries.base.Resources.add_protocol"></a>
#### add`_`protocol

```python
 | add_protocol(protocol: Protocol)
```

Add a protocol to the set of resources.

<a name=".aea.registries.base.Resources.get_skill"></a>
#### get`_`skill

```python
 | get_skill(skill_id: SkillId) -> Optional[Skill]
```

Get the skill.

<a name=".aea.registries.base.Resources.get_all_skills"></a>
#### get`_`all`_`skills

```python
 | get_all_skills() -> List[Skill]
```

Get the list of all the skills.

**Returns**:

the list of skills.

<a name=".aea.registries.base.Resources.remove_skill"></a>
#### remove`_`skill

```python
 | remove_skill(skill_id: SkillId)
```

Remove a skill from the set of resources.

<a name=".aea.registries.base.Resources.setup"></a>
#### setup

```python
 | setup()
```

Set up the resources.

**Returns**:

None

<a name=".aea.registries.base.Resources.teardown"></a>
#### teardown

```python
 | teardown()
```

Teardown the resources.

**Returns**:

None

<a name=".aea.registries.base.Filter"></a>
### Filter

```python
class Filter()
```

This class implements the filter of an AEA.

<a name=".aea.registries.base.Filter.__init__"></a>
#### `__`init`__`

```python
 | __init__(resources: Resources, decision_maker_out_queue: Queue)
```

Instantiate the filter.

**Arguments**:

- `resources`: the resources
- `decision_maker_out_queue`: the decision maker queue

<a name=".aea.registries.base.Filter.resources"></a>
#### resources

```python
 | @property
 | resources() -> Resources
```

Get resources.

<a name=".aea.registries.base.Filter.decision_maker_out_queue"></a>
#### decision`_`maker`_`out`_`queue

```python
 | @property
 | decision_maker_out_queue() -> Queue
```

Get decision maker (out) queue.

<a name=".aea.registries.base.Filter.get_active_handlers"></a>
#### get`_`active`_`handlers

```python
 | get_active_handlers(protocol_id: PublicId, envelope_context: Optional[EnvelopeContext]) -> List[Handler]
```

Get active handlers.

**Arguments**:

- `protocol_id`: the protocol id
:param envelope context: the envelope context

**Returns**:

the list of handlers currently active

<a name=".aea.registries.base.Filter.get_active_behaviours"></a>
#### get`_`active`_`behaviours

```python
 | get_active_behaviours() -> List[Behaviour]
```

Get the active behaviours.

**Returns**:

the list of behaviours currently active

<a name=".aea.registries.base.Filter.handle_internal_messages"></a>
#### handle`_`internal`_`messages

```python
 | handle_internal_messages() -> None
```

Handle the messages from the decision maker.

**Returns**:

None

