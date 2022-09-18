<a id="aea.registries.base"></a>

# aea.registries.base

This module contains registries.

<a id="aea.registries.base.Registry"></a>

## Registry Objects

```python
class Registry(Generic[ItemId, Item], WithLogger, ABC)
```

This class implements an abstract registry.

<a id="aea.registries.base.Registry.__init__"></a>

#### `__`init`__`

```python
def __init__(agent_name: str = "standalone") -> None
```

Initialize the registry.

**Arguments**:

- `agent_name`: the name of the agent

<a id="aea.registries.base.Registry.register"></a>

#### register

```python
@abstractmethod
def register(item_id: ItemId,
             item: Item,
             is_dynamically_added: bool = False) -> None
```

Register an item.

**Arguments**:

- `item_id`: the public id of the item.
- `item`: the item.
- `is_dynamically_added`: whether or not the item is dynamically added.

**Raises**:

- `ValueError`: if an item is already registered with that item id.

**Returns**:

None

<a id="aea.registries.base.Registry.unregister"></a>

#### unregister

```python
@abstractmethod
def unregister(item_id: ItemId) -> Optional[Item]
```

Unregister an item.

**Arguments**:

- `item_id`: the public id of the item.

**Raises**:

- `ValueError`: if no item registered with that item id.

**Returns**:

the item

<a id="aea.registries.base.Registry.fetch"></a>

#### fetch

```python
@abstractmethod
def fetch(item_id: ItemId) -> Optional[Item]
```

Fetch an item.

**Arguments**:

- `item_id`: the public id of the item.

**Returns**:

the Item

<a id="aea.registries.base.Registry.fetch_all"></a>

#### fetch`_`all

```python
@abstractmethod
def fetch_all() -> List[Item]
```

Fetch all the items.

**Returns**:

the list of items.

<a id="aea.registries.base.Registry.ids"></a>

#### ids

```python
@abstractmethod
def ids() -> Set[ItemId]
```

Return the set of all the used item ids.

**Returns**:

the set of item ids.

<a id="aea.registries.base.Registry.setup"></a>

#### setup

```python
@abstractmethod
def setup() -> None
```

Set up registry.

**Returns**:

None

<a id="aea.registries.base.Registry.teardown"></a>

#### teardown

```python
@abstractmethod
def teardown() -> None
```

Teardown the registry.

**Returns**:

None

<a id="aea.registries.base.PublicIdRegistry"></a>

## PublicIdRegistry Objects

```python
class PublicIdRegistry(Generic[Item], Registry[PublicId, Item])
```

This class implement a registry whose keys are public ids.

In particular, it is able to handle the case when the public id
points to the 'latest' version of a package.

<a id="aea.registries.base.PublicIdRegistry.__init__"></a>

#### `__`init`__`

```python
def __init__() -> None
```

Initialize the registry.

<a id="aea.registries.base.PublicIdRegistry.register"></a>

#### register

```python
def register(public_id: PublicId,
             item: Item,
             is_dynamically_added: bool = False) -> None
```

Register an item.

<a id="aea.registries.base.PublicIdRegistry.unregister"></a>

#### unregister

```python
def unregister(public_id: PublicId) -> Item
```

Unregister an item.

<a id="aea.registries.base.PublicIdRegistry.fetch"></a>

#### fetch

```python
def fetch(public_id: PublicId) -> Optional[Item]
```

Fetch an item associated with a public id.

**Arguments**:

- `public_id`: the public id.

**Returns**:

an item, or None if the key is not present.

<a id="aea.registries.base.PublicIdRegistry.fetch_all"></a>

#### fetch`_`all

```python
def fetch_all() -> List[Item]
```

Fetch all the items.

<a id="aea.registries.base.PublicIdRegistry.ids"></a>

#### ids

```python
def ids() -> Set[PublicId]
```

Get all the item ids.

<a id="aea.registries.base.PublicIdRegistry.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the items.

<a id="aea.registries.base.PublicIdRegistry.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear down the items.

<a id="aea.registries.base.AgentComponentRegistry"></a>

## AgentComponentRegistry Objects

```python
class AgentComponentRegistry(Registry[ComponentId, Component])
```

This class implements a simple dictionary-based registry for agent components.

<a id="aea.registries.base.AgentComponentRegistry.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Instantiate the registry.

**Arguments**:

- `kwargs`: kwargs

<a id="aea.registries.base.AgentComponentRegistry.register"></a>

#### register

```python
def register(component_id: ComponentId,
             component: Component,
             is_dynamically_added: bool = False) -> None
```

Register a component.

**Arguments**:

- `component_id`: the id of the component.
- `component`: the component object.
- `is_dynamically_added`: whether or not the item is dynamically added.

<a id="aea.registries.base.AgentComponentRegistry.unregister"></a>

#### unregister

```python
def unregister(component_id: ComponentId) -> Optional[Component]
```

Unregister a component.

**Arguments**:

- `component_id`: the ComponentId

**Returns**:

the item

<a id="aea.registries.base.AgentComponentRegistry.fetch"></a>

#### fetch

```python
def fetch(component_id: ComponentId) -> Optional[Component]
```

Fetch the component by id.

**Arguments**:

- `component_id`: the contract id

**Returns**:

the component or None if the component is not registered

<a id="aea.registries.base.AgentComponentRegistry.fetch_all"></a>

#### fetch`_`all

```python
def fetch_all() -> List[Component]
```

Fetch all the components.

**Returns**:

the list of registered components.

<a id="aea.registries.base.AgentComponentRegistry.fetch_by_type"></a>

#### fetch`_`by`_`type

```python
def fetch_by_type(component_type: ComponentType) -> List[Component]
```

Fetch all the components by a given type..

**Arguments**:

- `component_type`: a component type

**Returns**:

the list of registered components of a given type.

<a id="aea.registries.base.AgentComponentRegistry.ids"></a>

#### ids

```python
def ids() -> Set[ComponentId]
```

Get the item ids.

<a id="aea.registries.base.AgentComponentRegistry.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the registry.

<a id="aea.registries.base.AgentComponentRegistry.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Teardown the registry.

<a id="aea.registries.base.ComponentRegistry"></a>

## ComponentRegistry Objects

```python
class ComponentRegistry(Registry[Tuple[PublicId, str], SkillComponentType],
                        Generic[SkillComponentType])
```

This class implements a generic registry for skill components.

<a id="aea.registries.base.ComponentRegistry.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Instantiate the registry.

**Arguments**:

- `kwargs`: kwargs

<a id="aea.registries.base.ComponentRegistry.register"></a>

#### register

```python
def register(item_id: Tuple[PublicId, str],
             item: SkillComponentType,
             is_dynamically_added: bool = False) -> None
```

Register a item.

**Arguments**:

- `item_id`: a pair (skill id, item name).
- `item`: the item to register.
- `is_dynamically_added`: whether or not the item is dynamically added.

**Raises**:

- `ValueError`: if an item is already registered with that item id.

<a id="aea.registries.base.ComponentRegistry.unregister"></a>

#### unregister

```python
def unregister(item_id: Tuple[PublicId, str]) -> Optional[SkillComponentType]
```

Unregister a item.

**Arguments**:

- `item_id`: a pair (skill id, item name).

**Returns**:

skill component

<a id="aea.registries.base.ComponentRegistry.fetch"></a>

#### fetch

```python
def fetch(item_id: Tuple[PublicId, str]) -> Optional[SkillComponentType]
```

Fetch an item.

**Arguments**:

- `item_id`: the public id of the item.

**Returns**:

the Item

<a id="aea.registries.base.ComponentRegistry.fetch_by_skill"></a>

#### fetch`_`by`_`skill

```python
def fetch_by_skill(skill_id: PublicId) -> List[SkillComponentType]
```

Fetch all the items of a given skill.

<a id="aea.registries.base.ComponentRegistry.fetch_all"></a>

#### fetch`_`all

```python
def fetch_all() -> List[SkillComponentType]
```

Fetch all the items.

<a id="aea.registries.base.ComponentRegistry.unregister_by_skill"></a>

#### unregister`_`by`_`skill

```python
def unregister_by_skill(skill_id: PublicId) -> None
```

Unregister all the components by skill.

<a id="aea.registries.base.ComponentRegistry.ids"></a>

#### ids

```python
def ids() -> Set[Tuple[PublicId, str]]
```

Get the item ids.

<a id="aea.registries.base.ComponentRegistry.setup"></a>

#### setup

```python
def setup() -> None
```

Set up the items in the registry.

<a id="aea.registries.base.ComponentRegistry.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Teardown the registry.

<a id="aea.registries.base.HandlerRegistry"></a>

## HandlerRegistry Objects

```python
class HandlerRegistry(ComponentRegistry[Handler])
```

This class implements the handlers registry.

<a id="aea.registries.base.HandlerRegistry.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Instantiate the registry.

**Arguments**:

- `kwargs`: kwargs

<a id="aea.registries.base.HandlerRegistry.register"></a>

#### register

```python
def register(item_id: Tuple[PublicId, str],
             item: Handler,
             is_dynamically_added: bool = False) -> None
```

Register a handler.

**Arguments**:

- `item_id`: the item id.
- `item`: the handler.
- `is_dynamically_added`: whether or not the item is dynamically added.

**Raises**:

- `ValueError`: if the protocol is None, or an item with pair (skill_id, protocol_id_ already exists.

<a id="aea.registries.base.HandlerRegistry.unregister"></a>

#### unregister

```python
def unregister(item_id: Tuple[PublicId, str]) -> Handler
```

Unregister a item.

**Arguments**:

- `item_id`: a pair (skill id, item name).

**Returns**:

the unregistered handler

<a id="aea.registries.base.HandlerRegistry.unregister_by_skill"></a>

#### unregister`_`by`_`skill

```python
def unregister_by_skill(skill_id: PublicId) -> None
```

Unregister all the components by skill.

<a id="aea.registries.base.HandlerRegistry.fetch_by_protocol"></a>

#### fetch`_`by`_`protocol

```python
def fetch_by_protocol(protocol_id: PublicId) -> List[Handler]
```

Fetch the handler by the pair protocol id and skill id.

**Arguments**:

- `protocol_id`: the protocol id

**Returns**:

the handlers registered for the protocol_id and skill_id

<a id="aea.registries.base.HandlerRegistry.fetch_by_protocol_and_skill"></a>

#### fetch`_`by`_`protocol`_`and`_`skill

```python
def fetch_by_protocol_and_skill(protocol_id: PublicId,
                                skill_id: PublicId) -> Optional[Handler]
```

Fetch the handler by the pair protocol id and skill id.

**Arguments**:

- `protocol_id`: the protocol id
- `skill_id`: the skill id.

**Returns**:

the handlers registered for the protocol_id and skill_id

