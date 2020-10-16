<a name="aea.registries.resources"></a>
# aea.registries.resources

This module contains the resources class.

<a name="aea.registries.resources.Resources"></a>
## Resources Objects

```python
class Resources()
```

This class implements the object that holds the resources of an AEA.

<a name="aea.registries.resources.Resources.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_name: str = "standalone") -> None
```

Instantiate the resources.

:return None

<a name="aea.registries.resources.Resources.agent_name"></a>
#### agent`_`name

```python
 | @property
 | agent_name() -> str
```

Get the agent name.

<a name="aea.registries.resources.Resources.component_registry"></a>
#### component`_`registry

```python
 | @property
 | component_registry() -> AgentComponentRegistry
```

Get the agent component registry.

<a name="aea.registries.resources.Resources.behaviour_registry"></a>
#### behaviour`_`registry

```python
 | @property
 | behaviour_registry() -> ComponentRegistry[Behaviour]
```

Get the behaviour registry.

<a name="aea.registries.resources.Resources.handler_registry"></a>
#### handler`_`registry

```python
 | @property
 | handler_registry() -> HandlerRegistry
```

Get the handler registry.

<a name="aea.registries.resources.Resources.model_registry"></a>
#### model`_`registry

```python
 | @property
 | model_registry() -> ComponentRegistry[Model]
```

Get the model registry.

<a name="aea.registries.resources.Resources.add_component"></a>
#### add`_`component

```python
 | add_component(component: Component)
```

Add a component to resources.

<a name="aea.registries.resources.Resources.add_protocol"></a>
#### add`_`protocol

```python
 | add_protocol(protocol: Protocol) -> None
```

Add a protocol to the set of resources.

**Arguments**:

- `protocol`: a protocol

**Returns**:

None

<a name="aea.registries.resources.Resources.get_protocol"></a>
#### get`_`protocol

```python
 | get_protocol(protocol_id: ProtocolId) -> Optional[Protocol]
```

Get protocol for given protocol id.

**Arguments**:

- `protocol_id`: the protocol id

**Returns**:

a matching protocol, if present, else None

<a name="aea.registries.resources.Resources.get_all_protocols"></a>
#### get`_`all`_`protocols

```python
 | get_all_protocols() -> List[Protocol]
```

Get the list of all the protocols.

**Returns**:

the list of protocols.

<a name="aea.registries.resources.Resources.remove_protocol"></a>
#### remove`_`protocol

```python
 | remove_protocol(protocol_id: ProtocolId) -> None
```

Remove a protocol from the set of resources.

**Arguments**:

- `protocol_id`: the protocol id for the protocol to be removed.

**Returns**:

None

<a name="aea.registries.resources.Resources.add_contract"></a>
#### add`_`contract

```python
 | add_contract(contract: Contract) -> None
```

Add a contract to the set of resources.

**Arguments**:

- `contract`: a contract

**Returns**:

None

<a name="aea.registries.resources.Resources.get_contract"></a>
#### get`_`contract

```python
 | get_contract(contract_id: ContractId) -> Optional[Contract]
```

Get contract for given contract id.

**Arguments**:

- `contract_id`: the contract id

**Returns**:

a matching contract, if present, else None

<a name="aea.registries.resources.Resources.get_all_contracts"></a>
#### get`_`all`_`contracts

```python
 | get_all_contracts() -> List[Contract]
```

Get the list of all the contracts.

**Returns**:

the list of contracts.

<a name="aea.registries.resources.Resources.remove_contract"></a>
#### remove`_`contract

```python
 | remove_contract(contract_id: ContractId) -> None
```

Remove a contract from the set of resources.

**Arguments**:

- `contract_id`: the contract id for the contract to be removed.

**Returns**:

None

<a name="aea.registries.resources.Resources.add_connection"></a>
#### add`_`connection

```python
 | add_connection(connection: Connection) -> None
```

Add a connection to the set of resources.

**Arguments**:

- `connection`: a connection

**Returns**:

None

<a name="aea.registries.resources.Resources.get_connection"></a>
#### get`_`connection

```python
 | get_connection(connection_id: ConnectionId) -> Optional[Connection]
```

Get connection for given connection id.

**Arguments**:

- `connection_id`: the connection id

**Returns**:

a matching connection, if present, else None

<a name="aea.registries.resources.Resources.get_all_connections"></a>
#### get`_`all`_`connections

```python
 | get_all_connections() -> List[Connection]
```

Get the list of all the connections.

**Returns**:

the list of connections.

<a name="aea.registries.resources.Resources.remove_connection"></a>
#### remove`_`connection

```python
 | remove_connection(connection_id: ConnectionId) -> None
```

Remove a connection from the set of resources.

**Arguments**:

- `connection_id`: the connection id for the connection to be removed.

**Returns**:

None

<a name="aea.registries.resources.Resources.add_skill"></a>
#### add`_`skill

```python
 | add_skill(skill: Skill) -> None
```

Add a skill to the set of resources.

**Arguments**:

- `skill`: a skill

**Returns**:

None

<a name="aea.registries.resources.Resources.get_skill"></a>
#### get`_`skill

```python
 | get_skill(skill_id: SkillId) -> Optional[Skill]
```

Get the skill for a given skill id.

**Arguments**:

- `skill_id`: the skill id

**Returns**:

a matching skill, if present, else None

<a name="aea.registries.resources.Resources.get_all_skills"></a>
#### get`_`all`_`skills

```python
 | get_all_skills() -> List[Skill]
```

Get the list of all the skills.

**Returns**:

the list of skills.

<a name="aea.registries.resources.Resources.remove_skill"></a>
#### remove`_`skill

```python
 | remove_skill(skill_id: SkillId) -> None
```

Remove a skill from the set of resources.

**Arguments**:

- `skill_id`: the skill id for the skill to be removed.

**Returns**:

None

<a name="aea.registries.resources.Resources.get_handler"></a>
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

<a name="aea.registries.resources.Resources.get_handlers"></a>
#### get`_`handlers

```python
 | get_handlers(protocol_id: ProtocolId) -> List[Handler]
```

Get all handlers for a given protocol.

**Arguments**:

- `protocol_id`: the protocol id the handler is handling

**Returns**:

the list of handlers matching the protocol

<a name="aea.registries.resources.Resources.get_all_handlers"></a>
#### get`_`all`_`handlers

```python
 | get_all_handlers() -> List[Handler]
```

Get all handlers from all skills.

**Returns**:

the list of handlers

<a name="aea.registries.resources.Resources.get_behaviour"></a>
#### get`_`behaviour

```python
 | get_behaviour(skill_id: SkillId, behaviour_name: str) -> Optional[Behaviour]
```

Get a specific behaviours for a given skill.

**Arguments**:

- `skill_id`: the skill id
- `behaviour_name`: the behaviour name

**Returns**:

the behaviour, if it is present, else None

<a name="aea.registries.resources.Resources.get_behaviours"></a>
#### get`_`behaviours

```python
 | get_behaviours(skill_id: SkillId) -> List[Behaviour]
```

Get all behaviours for a given skill.

**Arguments**:

- `skill_id`: the skill id

**Returns**:

the list of behaviours of the skill

<a name="aea.registries.resources.Resources.get_all_behaviours"></a>
#### get`_`all`_`behaviours

```python
 | get_all_behaviours() -> List[Behaviour]
```

Get all behaviours from all skills.

**Returns**:

the list of all behaviours

<a name="aea.registries.resources.Resources.setup"></a>
#### setup

```python
 | setup() -> None
```

Set up the resources.

Calls setup on all resources.

**Returns**:

None

<a name="aea.registries.resources.Resources.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Teardown the resources.

Calls teardown on all resources.

**Returns**:

None

