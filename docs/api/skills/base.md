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

