<a id="aea.skills.base"></a>

# aea.skills.base

This module contains the base classes for the skills.

<a id="aea.skills.base.SkillContext"></a>

## SkillContext Objects

```python
class SkillContext()
```

This class implements the context of a skill.

<a id="aea.skills.base.SkillContext.__init__"></a>

#### `__`init`__`

```python
def __init__(agent_context: Optional[AgentContext] = None,
             skill: Optional["Skill"] = None) -> None
```

Initialize a skill context.

**Arguments**:

- `agent_context`: the agent context.
- `skill`: the skill.

<a id="aea.skills.base.SkillContext.is_abstract_component"></a>

#### is`_`abstract`_`component

```python
@property
def is_abstract_component() -> bool
```

Get if the skill is abstract.

<a id="aea.skills.base.SkillContext.logger"></a>

#### logger

```python
@property
def logger() -> Logger
```

Get the logger.

<a id="aea.skills.base.SkillContext.logger"></a>

#### logger

```python
@logger.setter
def logger(logger_: Logger) -> None
```

Set the logger.

<a id="aea.skills.base.SkillContext.data_dir"></a>

#### data`_`dir

```python
@property
def data_dir() -> str
```

Get the agent's data directory

<a id="aea.skills.base.SkillContext.set_agent_context"></a>

#### set`_`agent`_`context

```python
def set_agent_context(agent_context: AgentContext) -> None
```

Set the agent context.

<a id="aea.skills.base.SkillContext.shared_state"></a>

#### shared`_`state

```python
@property
def shared_state() -> Dict[str, Any]
```

Get the shared state dictionary.

<a id="aea.skills.base.SkillContext.agent_name"></a>

#### agent`_`name

```python
@property
def agent_name() -> str
```

Get agent name.

<a id="aea.skills.base.SkillContext.skill_id"></a>

#### skill`_`id

```python
@property
def skill_id() -> PublicId
```

Get the skill id of the skill context.

<a id="aea.skills.base.SkillContext.is_active"></a>

#### is`_`active

```python
@property
def is_active() -> bool
```

Get the status of the skill (active/not active).

<a id="aea.skills.base.SkillContext.is_active"></a>

#### is`_`active

```python
@is_active.setter
def is_active(value: bool) -> None
```

Set the status of the skill (active/not active).

<a id="aea.skills.base.SkillContext.new_behaviours"></a>

#### new`_`behaviours

```python
@property
def new_behaviours() -> "Queue[Behaviour]"
```

Queue for the new behaviours.

This queue can be used to send messages to the framework
to request the registration of a behaviour.

**Returns**:

the queue of new behaviours.

<a id="aea.skills.base.SkillContext.new_handlers"></a>

#### new`_`handlers

```python
@property
def new_handlers() -> "Queue[Handler]"
```

Queue for the new handlers.

This queue can be used to send messages to the framework
to request the registration of a handler.

**Returns**:

the queue of new handlers.

<a id="aea.skills.base.SkillContext.agent_addresses"></a>

#### agent`_`addresses

```python
@property
def agent_addresses() -> Dict[str, str]
```

Get addresses.

<a id="aea.skills.base.SkillContext.agent_address"></a>

#### agent`_`address

```python
@property
def agent_address() -> str
```

Get address.

<a id="aea.skills.base.SkillContext.public_key"></a>

#### public`_`key

```python
@property
def public_key() -> str
```

Get public key.

<a id="aea.skills.base.SkillContext.public_keys"></a>

#### public`_`keys

```python
@property
def public_keys() -> Dict[str, str]
```

Get public keys.

<a id="aea.skills.base.SkillContext.connection_status"></a>

#### connection`_`status

```python
@property
def connection_status() -> MultiplexerStatus
```

Get connection status.

<a id="aea.skills.base.SkillContext.outbox"></a>

#### outbox

```python
@property
def outbox() -> OutBox
```

Get outbox.

<a id="aea.skills.base.SkillContext.storage"></a>

#### storage

```python
@property
def storage() -> Optional[Storage]
```

Get optional storage for agent.

<a id="aea.skills.base.SkillContext.message_in_queue"></a>

#### message`_`in`_`queue

```python
@property
def message_in_queue() -> Queue
```

Get message in queue.

<a id="aea.skills.base.SkillContext.decision_maker_message_queue"></a>

#### decision`_`maker`_`message`_`queue

```python
@property
def decision_maker_message_queue() -> Queue
```

Get message queue of decision maker.

<a id="aea.skills.base.SkillContext.decision_maker_handler_context"></a>

#### decision`_`maker`_`handler`_`context

```python
@property
def decision_maker_handler_context() -> SimpleNamespace
```

Get decision maker handler context.

<a id="aea.skills.base.SkillContext.task_manager"></a>

#### task`_`manager

```python
@property
def task_manager() -> TaskManager
```

Get behaviours of the skill.

<a id="aea.skills.base.SkillContext.default_ledger_id"></a>

#### default`_`ledger`_`id

```python
@property
def default_ledger_id() -> str
```

Get the default ledger id.

<a id="aea.skills.base.SkillContext.currency_denominations"></a>

#### currency`_`denominations

```python
@property
def currency_denominations() -> Dict[str, str]
```

Get a dictionary mapping ledger ids to currency denominations.

<a id="aea.skills.base.SkillContext.search_service_address"></a>

#### search`_`service`_`address

```python
@property
def search_service_address() -> Address
```

Get the address of the search service.

<a id="aea.skills.base.SkillContext.decision_maker_address"></a>

#### decision`_`maker`_`address

```python
@property
def decision_maker_address() -> Address
```

Get the address of the decision maker.

<a id="aea.skills.base.SkillContext.handlers"></a>

#### handlers

```python
@property
def handlers() -> SimpleNamespace
```

Get handlers of the skill.

<a id="aea.skills.base.SkillContext.behaviours"></a>

#### behaviours

```python
@property
def behaviours() -> SimpleNamespace
```

Get behaviours of the skill.

<a id="aea.skills.base.SkillContext.namespace"></a>

#### namespace

```python
@property
def namespace() -> SimpleNamespace
```

Get the agent context namespace.

<a id="aea.skills.base.SkillContext.__getattr__"></a>

#### `__`getattr`__`

```python
def __getattr__(item: Any) -> Any
```

Get attribute.

<a id="aea.skills.base.SkillContext.send_to_skill"></a>

#### send`_`to`_`skill

```python
def send_to_skill(message_or_envelope: Union[Message, Envelope],
                  context: Optional[EnvelopeContext] = None) -> None
```

Send message or envelope to another skill.

If message passed it will be wrapped into envelope with optional envelope context.

**Arguments**:

- `message_or_envelope`: envelope to send to another skill.
- `context`: the optional envelope context

<a id="aea.skills.base.SkillComponent"></a>

## SkillComponent Objects

```python
class SkillComponent(ABC)
```

This class defines an abstract interface for skill component classes.

<a id="aea.skills.base.SkillComponent.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str,
             skill_context: SkillContext,
             configuration: Optional[SkillComponentConfiguration] = None,
             **kwargs: Any) -> None
```

Initialize a skill component.

**Arguments**:

- `name`: the name of the component.
- `configuration`: the configuration for the component.
- `skill_context`: the skill context.
- `kwargs`: the keyword arguments.

<a id="aea.skills.base.SkillComponent.name"></a>

#### name

```python
@property
def name() -> str
```

Get the name of the skill component.

<a id="aea.skills.base.SkillComponent.context"></a>

#### context

```python
@property
def context() -> SkillContext
```

Get the context of the skill component.

<a id="aea.skills.base.SkillComponent.skill_id"></a>

#### skill`_`id

```python
@property
def skill_id() -> PublicId
```

Get the skill id of the skill component.

<a id="aea.skills.base.SkillComponent.configuration"></a>

#### configuration

```python
@property
def configuration() -> SkillComponentConfiguration
```

Get the skill component configuration.

<a id="aea.skills.base.SkillComponent.config"></a>

#### config

```python
@property
def config() -> Dict[Any, Any]
```

Get the config of the skill component.

<a id="aea.skills.base.SkillComponent.setup"></a>

#### setup

```python
@abstractmethod
def setup() -> None
```

Implement the setup.

<a id="aea.skills.base.SkillComponent.teardown"></a>

#### teardown

```python
@abstractmethod
def teardown() -> None
```

Implement the teardown.

<a id="aea.skills.base.SkillComponent.parse_module"></a>

#### parse`_`module

```python
@classmethod
@abstractmethod
def parse_module(cls, path: str, configs: Dict[str,
                                               SkillComponentConfiguration],
                 skill_context: SkillContext) -> dict
```

Parse the component module.

<a id="aea.skills.base.AbstractBehaviour"></a>

## AbstractBehaviour Objects

```python
class AbstractBehaviour(SkillComponent, ABC)
```

Abstract behaviour for periodical calls.

tick_interval: float, interval to call behaviour's act.
start_at: optional datetime, when to start periodical calls.

<a id="aea.skills.base.AbstractBehaviour.tick_interval"></a>

#### tick`_`interval

```python
@property
def tick_interval() -> float
```

Get the tick_interval in seconds.

<a id="aea.skills.base.AbstractBehaviour.start_at"></a>

#### start`_`at

```python
@property
def start_at() -> Optional[datetime.datetime]
```

Get the start time of the behaviour.

<a id="aea.skills.base.Behaviour"></a>

## Behaviour Objects

```python
class Behaviour(AbstractBehaviour, ABC)
```

This class implements an abstract behaviour.

In a subclass of Behaviour, the flag 'is_programmatically_defined'
 can be used by the developer to signal to the framework that the class
 is meant to be used programmatically; hence, in case the class is
 not declared in the configuration file but it is present in a skill
 module, the framework will just ignore this class instead of printing
 a warning message.

<a id="aea.skills.base.Behaviour.act"></a>

#### act

```python
@abstractmethod
def act() -> None
```

Implement the behaviour.

**Returns**:

None

<a id="aea.skills.base.Behaviour.is_done"></a>

#### is`_`done

```python
def is_done() -> bool
```

Return True if the behaviour is terminated, False otherwise.

<a id="aea.skills.base.Behaviour.act_wrapper"></a>

#### act`_`wrapper

```python
def act_wrapper() -> None
```

Wrap the call of the action. This method must be called only by the framework.

<a id="aea.skills.base.Behaviour.parse_module"></a>

#### parse`_`module

```python
@classmethod
def parse_module(cls, path: str,
                 behaviour_configs: Dict[str, SkillComponentConfiguration],
                 skill_context: SkillContext) -> Dict[str, "Behaviour"]
```

Parse the behaviours module.

**Arguments**:

- `path`: path to the Python module containing the Behaviour classes.
- `behaviour_configs`: a list of behaviour configurations.
- `skill_context`: the skill context

**Returns**:

a list of Behaviour.

<a id="aea.skills.base.Handler"></a>

## Handler Objects

```python
class Handler(SkillComponent, ABC)
```

This class implements an abstract behaviour.

In a subclass of Handler, the flag 'is_programmatically_defined'
 can be used by the developer to signal to the framework that the component
 is meant to be used programmatically; hence, in case the class is
 not declared in the configuration file but it is present in a skill
 module, the framework will just ignore this class instead of printing
 a warning message.

SUPPORTED_PROTOCOL is read by the framework when the handlers are loaded
 to register them as 'listeners' to the protocol identified by the specified
 public id. Whenever a message of protocol 'SUPPORTED_PROTOCOL' is sent
 to the agent, the framework will call the 'handle' method.

<a id="aea.skills.base.Handler.handle"></a>

#### handle

```python
@abstractmethod
def handle(message: Message) -> None
```

Implement the reaction to a message.

**Arguments**:

- `message`: the message

**Returns**:

None

<a id="aea.skills.base.Handler.handle_wrapper"></a>

#### handle`_`wrapper

```python
def handle_wrapper(message: Message) -> None
```

Wrap the call of the handler. This method must be called only by the framework.

<a id="aea.skills.base.Handler.parse_module"></a>

#### parse`_`module

```python
@classmethod
def parse_module(cls, path: str,
                 handler_configs: Dict[str, SkillComponentConfiguration],
                 skill_context: SkillContext) -> Dict[str, "Handler"]
```

Parse the handler module.

**Arguments**:

- `path`: path to the Python module containing the Handler class.
- `handler_configs`: the list of handler configurations.
- `skill_context`: the skill context

**Returns**:

an handler, or None if the parsing fails.

<a id="aea.skills.base.Handler.protocol_dialogues"></a>

#### protocol`_`dialogues

```python
def protocol_dialogues(attribute: Optional[str] = None)
```

Protocol dialogues.

This method must NOT be called by the framework with exception handling.
It assumes a user-behaviour whereby dialogues are stored
under specifically named attributes.

**Arguments**:

- `attribute`: attribute under which dialogue is stored

**Returns**:

dialogue

<a id="aea.skills.base.Model"></a>

## Model Objects

```python
class Model(SkillComponent, ABC)
```

This class implements an abstract model.

<a id="aea.skills.base.Model.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str,
             skill_context: SkillContext,
             configuration: Optional[SkillComponentConfiguration] = None,
             keep_terminal_state_dialogues: Optional[bool] = None,
             **kwargs: Any) -> None
```

Initialize a model.

**Arguments**:

- `name`: the name of the component.
- `configuration`: the configuration for the component.
- `skill_context`: the skill context.
- `keep_terminal_state_dialogues`: specify do dialogues in terminal state should stay or not
- `kwargs`: the keyword arguments.

<a id="aea.skills.base.Model.setup"></a>

#### setup

```python
def setup() -> None
```

Set the class up.

<a id="aea.skills.base.Model.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear the class down.

<a id="aea.skills.base.Model.parse_module"></a>

#### parse`_`module

```python
@classmethod
def parse_module(cls, path: str,
                 model_configs: Dict[str, SkillComponentConfiguration],
                 skill_context: SkillContext) -> Dict[str, "Model"]
```

Parse the model module.

**Arguments**:

- `path`: path to the Python skill module.
- `model_configs`: a list of model configurations.
- `skill_context`: the skill context

**Returns**:

a list of Model.

<a id="aea.skills.base.Skill"></a>

## Skill Objects

```python
class Skill(Component)
```

This class implements a skill.

<a id="aea.skills.base.Skill.__init__"></a>

#### `__`init`__`

```python
def __init__(configuration: SkillConfig,
             skill_context: Optional[SkillContext] = None,
             handlers: Optional[Dict[str, Handler]] = None,
             behaviours: Optional[Dict[str, Behaviour]] = None,
             models: Optional[Dict[str, Model]] = None,
             **kwargs: Any)
```

Initialize a skill.

**Arguments**:

- `configuration`: the skill configuration.
- `skill_context`: the skill context.
- `handlers`: dictionary of handlers.
- `behaviours`: dictionary of behaviours.
- `models`: dictionary of models.
- `kwargs`: the keyword arguments.

<a id="aea.skills.base.Skill.skill_context"></a>

#### skill`_`context

```python
@property
def skill_context() -> SkillContext
```

Get the skill context.

<a id="aea.skills.base.Skill.handlers"></a>

#### handlers

```python
@property
def handlers() -> Dict[str, Handler]
```

Get the handlers.

<a id="aea.skills.base.Skill.behaviours"></a>

#### behaviours

```python
@property
def behaviours() -> Dict[str, Behaviour]
```

Get the handlers.

<a id="aea.skills.base.Skill.models"></a>

#### models

```python
@property
def models() -> Dict[str, Model]
```

Get the handlers.

<a id="aea.skills.base.Skill.from_dir"></a>

#### from`_`dir

```python
@classmethod
def from_dir(cls, directory: str, agent_context: AgentContext,
             **kwargs: Any) -> "Skill"
```

Load the skill from a directory.

**Arguments**:

- `directory`: the directory to the skill package.
- `agent_context`: the skill context.
- `kwargs`: the keyword arguments.

**Returns**:

the skill object.

<a id="aea.skills.base.Skill.logger"></a>

#### logger

```python
@property
def logger() -> Logger
```

Get the logger.

In the case of a skill, return the
logger provided by the skill context.

**Returns**:

the logger

<a id="aea.skills.base.Skill.logger"></a>

#### logger

```python
@logger.setter
def logger(*args: str) -> None
```

Set the logger.

<a id="aea.skills.base.Skill.from_config"></a>

#### from`_`config

```python
@classmethod
def from_config(cls, configuration: SkillConfig, agent_context: AgentContext,
                **kwargs: Any) -> "Skill"
```

Load the skill from configuration.

**Arguments**:

- `configuration`: a skill configuration. Must be associated with a directory.
- `agent_context`: the agent context.
- `kwargs`: the keyword arguments.

**Returns**:

the skill.

<a id="aea.skills.base._SkillComponentLoadingItem"></a>

## `_`SkillComponentLoadingItem Objects

```python
class _SkillComponentLoadingItem()
```

Class to represent a triple (component name, component configuration, component class).

<a id="aea.skills.base._SkillComponentLoadingItem.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str, config: SkillComponentConfiguration,
             class_: Type[SkillComponent], type_: _SKILL_COMPONENT_TYPES)
```

Initialize the item.

<a id="aea.skills.base._SkillComponentLoader"></a>

## `_`SkillComponentLoader Objects

```python
class _SkillComponentLoader()
```

This class implements the loading policy for skill components.

<a id="aea.skills.base._SkillComponentLoader.__init__"></a>

#### `__`init`__`

```python
def __init__(configuration: SkillConfig, skill_context: SkillContext,
             **kwargs: Any)
```

Initialize the helper class.

<a id="aea.skills.base._SkillComponentLoader.load_skill"></a>

#### load`_`skill

```python
def load_skill() -> Skill
```

Load the skill.

