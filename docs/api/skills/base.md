<a name=".aea.skills.base"></a>
## aea.skills.base

This module contains the base classes for the skills.

<a name=".aea.skills.base.SkillContext"></a>
### SkillContext

```python
class SkillContext()
```

This class implements the context of a skill.

<a name=".aea.skills.base.SkillContext.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_context: Optional[AgentContext] = None, skill: Optional["Skill"] = None)
```

Initialize a skill context.

<a name=".aea.skills.base.SkillContext.set_agent_context"></a>
#### set`_`agent`_`context

```python
 | set_agent_context(agent_context: AgentContext) -> None
```

Set the agent context.

<a name=".aea.skills.base.SkillContext.shared_state"></a>
#### shared`_`state

```python
 | @property
 | shared_state() -> Dict[str, Any]
```

Get the shared state dictionary.

<a name=".aea.skills.base.SkillContext.agent_name"></a>
#### agent`_`name

```python
 | @property
 | agent_name() -> str
```

Get agent name.

<a name=".aea.skills.base.SkillContext.skill_id"></a>
#### skill`_`id

```python
 | @property
 | skill_id() -> PublicId
```

Get the skill id of the skill context.

<a name=".aea.skills.base.SkillContext.is_active"></a>
#### is`_`active

```python
 | @is_active.setter
 | is_active(value: bool) -> None
```

Set the status of the skill (active/not active).

<a name=".aea.skills.base.SkillContext.new_behaviours"></a>
#### new`_`behaviours

```python
 | @property
 | new_behaviours() -> Queue
```

The queue for the new behaviours.

This queue can be used to send messages to the framework
to request the registration of a behaviour.

:return the queue of new behaviours.

<a name=".aea.skills.base.SkillContext.agent_addresses"></a>
#### agent`_`addresses

```python
 | @property
 | agent_addresses() -> Dict[str, str]
```

Get addresses.

<a name=".aea.skills.base.SkillContext.agent_address"></a>
#### agent`_`address

```python
 | @property
 | agent_address() -> str
```

Get address.

<a name=".aea.skills.base.SkillContext.connection_status"></a>
#### connection`_`status

```python
 | @property
 | connection_status() -> ConnectionStatus
```

Get connection status.

<a name=".aea.skills.base.SkillContext.outbox"></a>
#### outbox

```python
 | @property
 | outbox() -> OutBox
```

Get outbox.

<a name=".aea.skills.base.SkillContext.message_in_queue"></a>
#### message`_`in`_`queue

```python
 | @property
 | message_in_queue() -> Queue
```

Get message in queue.

<a name=".aea.skills.base.SkillContext.decision_maker_message_queue"></a>
#### decision`_`maker`_`message`_`queue

```python
 | @property
 | decision_maker_message_queue() -> Queue
```

Get message queue of decision maker.

<a name=".aea.skills.base.SkillContext.decision_maker_handler_context"></a>
#### decision`_`maker`_`handler`_`context

```python
 | @property
 | decision_maker_handler_context() -> SimpleNamespace
```

Get decision maker handler context.

<a name=".aea.skills.base.SkillContext.task_manager"></a>
#### task`_`manager

```python
 | @property
 | task_manager() -> TaskManager
```

Get behaviours of the skill.

<a name=".aea.skills.base.SkillContext.ledger_apis"></a>
#### ledger`_`apis

```python
 | @property
 | ledger_apis() -> LedgerApis
```

Get ledger APIs.

<a name=".aea.skills.base.SkillContext.search_service_address"></a>
#### search`_`service`_`address

```python
 | @property
 | search_service_address() -> Address
```

Get the address of the search service.

<a name=".aea.skills.base.SkillContext.handlers"></a>
#### handlers

```python
 | @property
 | handlers() -> SimpleNamespace
```

Get handlers of the skill.

<a name=".aea.skills.base.SkillContext.behaviours"></a>
#### behaviours

```python
 | @property
 | behaviours() -> SimpleNamespace
```

Get behaviours of the skill.

<a name=".aea.skills.base.SkillContext.contracts"></a>
#### contracts

```python
 | @property
 | contracts() -> SimpleNamespace
```

Get contracts the skill has access to.

<a name=".aea.skills.base.SkillContext.namespace"></a>
#### namespace

```python
 | @property
 | namespace() -> SimpleNamespace
```

Get the agent context namespace.

<a name=".aea.skills.base.SkillContext.__getattr__"></a>
#### `__`getattr`__`

```python
 | __getattr__(item) -> Any
```

Get attribute.

<a name=".aea.skills.base.SkillComponent"></a>
### SkillComponent

```python
class SkillComponent(ABC)
```

This class defines an abstract interface for skill component classes.

<a name=".aea.skills.base.SkillComponent.__init__"></a>
#### `__`init`__`

```python
 | __init__(name: str, skill_context: SkillContext, configuration: Optional[SkillComponentConfiguration] = None, **kwargs, ,)
```

Initialize a skill component.

**Arguments**:

- `name`: the name of the component.
- `configuration`: the configuration for the component.
- `skill_context`: the skill context.

<a name=".aea.skills.base.SkillComponent.name"></a>
#### name

```python
 | @property
 | name() -> str
```

Get the name of the skill component.

<a name=".aea.skills.base.SkillComponent.context"></a>
#### context

```python
 | @property
 | context() -> SkillContext
```

Get the context of the skill component.

<a name=".aea.skills.base.SkillComponent.skill_id"></a>
#### skill`_`id

```python
 | @property
 | skill_id() -> PublicId
```

Get the skill id of the skill component.

<a name=".aea.skills.base.SkillComponent.configuration"></a>
#### configuration

```python
 | @property
 | configuration() -> SkillComponentConfiguration
```

Get the skill component configuration.

<a name=".aea.skills.base.SkillComponent.config"></a>
#### config

```python
 | @property
 | config() -> Dict[Any, Any]
```

Get the config of the skill component.

<a name=".aea.skills.base.SkillComponent.setup"></a>
#### setup

```python
 | @abstractmethod
 | setup() -> None
```

Implement the setup.

**Returns**:

None

<a name=".aea.skills.base.SkillComponent.teardown"></a>
#### teardown

```python
 | @abstractmethod
 | teardown() -> None
```

Implement the teardown.

**Returns**:

None

<a name=".aea.skills.base.SkillComponent.parse_module"></a>
#### parse`_`module

```python
 | @classmethod
 | @abstractmethod
 | parse_module(cls, path: str, configs: Dict[str, SkillComponentConfiguration], skill_context: SkillContext)
```

Parse the component module.

<a name=".aea.skills.base.AbstractBehaviour"></a>
### AbstractBehaviour

```python
class AbstractBehaviour(SkillComponent,  ABC)
```

Abstract behaviour for periodical calls.

tick_interval: float, interval to call behaviour's act.
start_at: optional datetime, when to start periodical calls.

<a name=".aea.skills.base.Behaviour"></a>
### Behaviour

```python
class Behaviour(AbstractBehaviour,  ABC)
```

This class implements an abstract behaviour.

<a name=".aea.skills.base.Behaviour.act"></a>
#### act

```python
 | @abstractmethod
 | act() -> None
```

Implement the behaviour.

**Returns**:

None

<a name=".aea.skills.base.Behaviour.is_done"></a>
#### is`_`done

```python
 | is_done() -> bool
```

Return True if the behaviour is terminated, False otherwise.

<a name=".aea.skills.base.Behaviour.act_wrapper"></a>
#### act`_`wrapper

```python
 | act_wrapper() -> None
```

Wrap the call of the action. This method must be called only by the framework.

<a name=".aea.skills.base.Behaviour.parse_module"></a>
#### parse`_`module

```python
 | @classmethod
 | parse_module(cls, path: str, behaviour_configs: Dict[str, SkillComponentConfiguration], skill_context: SkillContext) -> Dict[str, "Behaviour"]
```

Parse the behaviours module.

**Arguments**:

- `path`: path to the Python module containing the Behaviour classes.
- `behaviour_configs`: a list of behaviour configurations.
- `skill_context`: the skill context

**Returns**:

a list of Behaviour.

<a name=".aea.skills.base.Handler"></a>
### Handler

```python
class Handler(SkillComponent,  ABC)
```

This class implements an abstract behaviour.

<a name=".aea.skills.base.Handler.handle"></a>
#### handle

```python
 | @abstractmethod
 | handle(message: Message) -> None
```

Implement the reaction to a message.

**Arguments**:

- `message`: the message

**Returns**:

None

<a name=".aea.skills.base.Handler.parse_module"></a>
#### parse`_`module

```python
 | @classmethod
 | parse_module(cls, path: str, handler_configs: Dict[str, SkillComponentConfiguration], skill_context: SkillContext) -> Dict[str, "Handler"]
```

Parse the handler module.

**Arguments**:

- `path`: path to the Python module containing the Handler class.
- `handler_configs`: the list of handler configurations.
- `skill_context`: the skill context

**Returns**:

an handler, or None if the parsing fails.

<a name=".aea.skills.base.Model"></a>
### Model

```python
class Model(SkillComponent,  ABC)
```

This class implements an abstract model.

<a name=".aea.skills.base.Model.setup"></a>
#### setup

```python
 | setup() -> None
```

Set the class up.

<a name=".aea.skills.base.Model.teardown"></a>
#### teardown

```python
 | teardown() -> None
```

Tear the class down.

<a name=".aea.skills.base.Model.parse_module"></a>
#### parse`_`module

```python
 | @classmethod
 | parse_module(cls, path: str, model_configs: Dict[str, SkillComponentConfiguration], skill_context: SkillContext) -> Dict[str, "Model"]
```

Parse the tasks module.

**Arguments**:

- `path`: path to the Python skill module.
- `model_configs`: a list of model configurations.
- `skill_context`: the skill context

**Returns**:

a list of Model.

<a name=".aea.skills.base.Skill"></a>
### Skill

```python
class Skill(Component)
```

This class implements a skill.

<a name=".aea.skills.base.Skill.__init__"></a>
#### `__`init`__`

```python
 | __init__(configuration: SkillConfig, skill_context: Optional[SkillContext] = None, handlers: Optional[Dict[str, Handler]] = None, behaviours: Optional[Dict[str, Behaviour]] = None, models: Optional[Dict[str, Model]] = None)
```

Initialize a skill.

**Arguments**:

- `configuration`: the skill configuration.

<a name=".aea.skills.base.Skill.contracts"></a>
#### contracts

```python
 | @property
 | contracts() -> Dict[str, Contract]
```

Get the contracts associated with the skill.

<a name=".aea.skills.base.Skill.inject_contracts"></a>
#### inject`_`contracts

```python
 | inject_contracts(contracts: Dict[str, Contract]) -> None
```

Add the contracts to the skill.

<a name=".aea.skills.base.Skill.skill_context"></a>
#### skill`_`context

```python
 | @property
 | skill_context() -> SkillContext
```

Get the skill context.

<a name=".aea.skills.base.Skill.handlers"></a>
#### handlers

```python
 | @property
 | handlers() -> Dict[str, Handler]
```

Get the handlers.

<a name=".aea.skills.base.Skill.behaviours"></a>
#### behaviours

```python
 | @property
 | behaviours() -> Dict[str, Behaviour]
```

Get the handlers.

<a name=".aea.skills.base.Skill.models"></a>
#### models

```python
 | @property
 | models() -> Dict[str, Model]
```

Get the handlers.

<a name=".aea.skills.base.Skill.from_dir"></a>
#### from`_`dir

```python
 | @classmethod
 | from_dir(cls, directory: str, skill_context: Optional[SkillContext] = None) -> "Skill"
```

Load the skill from a directory.

**Arguments**:

- `directory`: the directory to the skill package.
- `skill_context`: the skill context

**Returns**:

the skill object.

<a name=".aea.skills.base.Skill.from_config"></a>
#### from`_`config

```python
 | @classmethod
 | from_config(cls, configuration: SkillConfig, skill_context: Optional[SkillContext] = None) -> "Skill"
```

Load the skill from configuration.

**Arguments**:

- `configuration`: a skill configuration. Must be associated with a directory.

**Returns**:

the skill.

