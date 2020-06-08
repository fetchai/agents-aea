<a name=".aea.helpers.dialogue.base"></a>
# aea.helpers.dialogue.base

This module contains the classes required for dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.

<a name=".aea.helpers.dialogue.base.DialogueLabel"></a>
## DialogueLabel Objects

```python
class DialogueLabel()
```

The dialogue label class acts as an identifier for dialogues.

<a name=".aea.helpers.dialogue.base.DialogueLabel.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_reference: Tuple[str, str], dialogue_opponent_addr: Address, dialogue_starter_addr: Address) -> None
```

Initialize a dialogue label.

**Arguments**:

- `dialogue_reference`: the reference of the dialogue.
- `dialogue_opponent_addr`: the addr of the agent with which the dialogue is kept.
- `dialogue_starter_addr`: the addr of the agent which started the dialogue.

**Returns**:

None

<a name=".aea.helpers.dialogue.base.DialogueLabel.dialogue_reference"></a>
#### dialogue`_`reference

```python
 | @property
 | dialogue_reference() -> Tuple[str, str]
```

Get the dialogue reference.

<a name=".aea.helpers.dialogue.base.DialogueLabel.dialogue_starter_reference"></a>
#### dialogue`_`starter`_`reference

```python
 | @property
 | dialogue_starter_reference() -> str
```

Get the dialogue starter reference.

<a name=".aea.helpers.dialogue.base.DialogueLabel.dialogue_responder_reference"></a>
#### dialogue`_`responder`_`reference

```python
 | @property
 | dialogue_responder_reference() -> str
```

Get the dialogue responder reference.

<a name=".aea.helpers.dialogue.base.DialogueLabel.dialogue_opponent_addr"></a>
#### dialogue`_`opponent`_`addr

```python
 | @property
 | dialogue_opponent_addr() -> str
```

Get the address of the dialogue opponent.

<a name=".aea.helpers.dialogue.base.DialogueLabel.dialogue_starter_addr"></a>
#### dialogue`_`starter`_`addr

```python
 | @property
 | dialogue_starter_addr() -> str
```

Get the address of the dialogue starter.

<a name=".aea.helpers.dialogue.base.DialogueLabel.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other) -> bool
```

Check for equality between two DialogueLabel objects.

<a name=".aea.helpers.dialogue.base.DialogueLabel.__hash__"></a>
#### `__`hash`__`

```python
 | __hash__() -> int
```

Turn object into hash.

<a name=".aea.helpers.dialogue.base.DialogueLabel.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name=".aea.helpers.dialogue.base.DialogueLabel.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict[str, str]) -> "DialogueLabel"
```

Get dialogue label from json.

<a name=".aea.helpers.dialogue.base.DialogueLabel.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name=".aea.helpers.dialogue.base.Dialogue"></a>
## Dialogue Objects

```python
class Dialogue(ABC)
```

The dialogue class maintains state of a dialogue and manages it.

<a name=".aea.helpers.dialogue.base.Dialogue.Role"></a>
## Role Objects

```python
class Role(Enum)
```

This class defines the agent's role in a dialogue.

<a name=".aea.helpers.dialogue.base.Dialogue.Role.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name=".aea.helpers.dialogue.base.Dialogue.EndState"></a>
## EndState Objects

```python
class EndState(Enum)
```

This class defines the end states of a dialogue.

<a name=".aea.helpers.dialogue.base.Dialogue.EndState.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name=".aea.helpers.dialogue.base.Dialogue.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_label: DialogueLabel, agent_address: Optional[Address] = None, role: Optional[Role] = None) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `agent_address`: the address of the agent for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogue.dialogue_label"></a>
#### dialogue`_`label

```python
 | @property
 | dialogue_label() -> DialogueLabel
```

Get the dialogue label.

**Returns**:

The dialogue label

<a name=".aea.helpers.dialogue.base.Dialogue.agent_address"></a>
#### agent`_`address

```python
 | @agent_address.setter
 | agent_address(agent_address: Address) -> None
```

Set the address of the agent for whom this dialogues is maintained.

:param: the agent address

<a name=".aea.helpers.dialogue.base.Dialogue.role"></a>
#### role

```python
 | @role.setter
 | role(role: "Role") -> None
```

Set the agent's role in the dialogue.

**Arguments**:

- `role`: the agent's role

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogue.is_self_initiated"></a>
#### is`_`self`_`initiated

```python
 | @property
 | is_self_initiated() -> bool
```

Check whether the agent initiated the dialogue.

**Returns**:

True if the agent initiated the dialogue, False otherwise

<a name=".aea.helpers.dialogue.base.Dialogue.last_incoming_message"></a>
#### last`_`incoming`_`message

```python
 | @property
 | last_incoming_message() -> Optional[Message]
```

Get the last incoming message.

**Returns**:

the last incoming message if it exists, None otherwise

<a name=".aea.helpers.dialogue.base.Dialogue.last_outgoing_message"></a>
#### last`_`outgoing`_`message

```python
 | @property
 | last_outgoing_message() -> Optional[Message]
```

Get the last outgoing message.

**Returns**:

the last outgoing message if it exists, None otherwise

<a name=".aea.helpers.dialogue.base.Dialogue.last_message"></a>
#### last`_`message

```python
 | @property
 | last_message() -> Optional[Message]
```

Get the last message.

**Returns**:

the last message if it exists, None otherwise

<a name=".aea.helpers.dialogue.base.Dialogue.get_message"></a>
#### get`_`message

```python
 | get_message(message_id_to_find: int) -> Optional[Message]
```

Get the message whose id is 'message_id'.

**Arguments**:

- `message_id_to_find`: the id of the message

**Returns**:

the message if it exists, None otherwise

<a name=".aea.helpers.dialogue.base.Dialogue.is_empty"></a>
#### is`_`empty

```python
 | @property
 | is_empty() -> bool
```

Check whether the dialogue is empty

**Returns**:

True if empty, False otherwise

<a name=".aea.helpers.dialogue.base.Dialogue.update"></a>
#### update

```python
 | update(message: Message) -> bool
```

Extend the list of incoming/outgoing messages with 'message', if 'message' is valid

**Arguments**:

- `message`: a message to be added

**Returns**:

True if message successfully added, false otherwise

<a name=".aea.helpers.dialogue.base.Dialogue.is_valid_next_message"></a>
#### is`_`valid`_`next`_`message

```python
 | is_valid_next_message(message: Message) -> bool
```

Check whether 'message' is a valid next message in this dialogue.

The evaluation of a message validity involves performing several categories of checks.
Each category of checks resides in a separate method.

Currently, basic rules are fundamental structural constraints,
additional rules are applied for the time being, and more specific rules are captured in the is_valid method.

**Arguments**:

- `message`: the message to be validated

**Returns**:

True if yes, False otherwise.

<a name=".aea.helpers.dialogue.base.Dialogue.initial_performative"></a>
#### initial`_`performative

```python
 | @abstractmethod
 | initial_performative() -> Enum
```

Get the performative which the initial message in the dialogue must have

**Returns**:

the performative of the initial message

<a name=".aea.helpers.dialogue.base.Dialogue.get_replies"></a>
#### get`_`replies

```python
 | @abstractmethod
 | get_replies(performative: Enum) -> FrozenSet
```

Given a `performative`, return the list of performatives which are its valid replies in a dialogue

**Arguments**:

- `performative`: the performative in a message

**Returns**:

list of valid performative replies

<a name=".aea.helpers.dialogue.base.Dialogue.is_valid"></a>
#### is`_`valid

```python
 | @abstractmethod
 | is_valid(message: Message) -> bool
```

Check whether 'message' is a valid next message in the dialogue.

These rules capture specific constraints designed for dialogues which are instance of a concrete sub-class of this class.

**Arguments**:

- `message`: the message to be validated

**Returns**:

True if valid, False otherwise.

<a name=".aea.helpers.dialogue.base.Dialogue.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

**Returns**:

The string representation of the dialogue

<a name=".aea.helpers.dialogue.base.Dialogue.outgoing_extend"></a>
#### outgoing`_`extend

```python
 | outgoing_extend(message: Message) -> None
```

UNSAFE TO USE - IS DEPRECATED - USE update(message) METHOD INSTEAD
Extend the list of outgoing messages with 'message'

**Arguments**:

- `message`: a message to be added

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogue.incoming_extend"></a>
#### incoming`_`extend

```python
 | incoming_extend(message: Message) -> None
```

UNSAFE TO USE - IS DEPRECATED - USE update(message) METHOD INSTEAD
Extend the list of incoming messages with 'message'

**Arguments**:

- `message`: a message to be added

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogues"></a>
## Dialogues Objects

```python
class Dialogues(ABC)
```

The dialogues class keeps track of all dialogues for an agent.

<a name=".aea.helpers.dialogue.base.Dialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_address: Address = "") -> None
```

Initialize dialogues.

**Arguments**:

- `agent_address`: the address of the agent for whom dialogues are maintained

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogues.dialogues"></a>
#### dialogues

```python
 | @property
 | dialogues() -> Dict[DialogueLabel, Dialogue]
```

Get dictionary of dialogues in which the agent engages.

<a name=".aea.helpers.dialogue.base.Dialogues.agent_address"></a>
#### agent`_`address

```python
 | @property
 | agent_address() -> Address
```

Get the address of the agent for whom dialogues are maintained.

<a name=".aea.helpers.dialogue.base.Dialogues.new_self_initiated_dialogue_reference"></a>
#### new`_`self`_`initiated`_`dialogue`_`reference

```python
 | new_self_initiated_dialogue_reference() -> Tuple[str, str]
```

Return a dialogue label for a new self initiated dialogue

**Returns**:

the next nonce

<a name=".aea.helpers.dialogue.base.Dialogues.update"></a>
#### update

```python
 | update(message: Message) -> Optional[Dialogue]
```

Update the state of dialogues with a new message.

If the message is for a new dialogue, a new dialogue is created with 'message' as its first message and returned.
If the message is addressed to an existing dialogue, the dialogue is retrieved, extended with this message and returned.
If there are any errors, e.g. the message dialogue reference does not exists or the message is invalid w.r.t. the dialogue, return None.

**Arguments**:

- `message`: a new message

**Returns**:

the new or existing dialogue the message is intended for, or None in case of any errors.

<a name=".aea.helpers.dialogue.base.Dialogues.create_dialogue"></a>
#### create`_`dialogue

```python
 | @abstractmethod
 | create_dialogue(dialogue_label: DialogueLabel, role: Dialogue.Role) -> Dialogue
```

Create a dialogue instance.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

the created dialogue

<a name=".aea.helpers.dialogue.base.Dialogues.role_from_first_message"></a>
#### role`_`from`_`first`_`message

```python
 | @staticmethod
 | @abstractmethod
 | role_from_first_message(message: Message) -> Dialogue.Role
```

Infer the role of the agent from an incoming or outgoing first message

**Arguments**:

- `message`: an incoming/outgoing first message

**Returns**:

the agent's role

<a name=".aea.helpers.dialogue.base.Dialogues.is_belonging_to_registered_dialogue"></a>
#### is`_`belonging`_`to`_`registered`_`dialogue

```python
 | is_belonging_to_registered_dialogue(msg: Message, agent_addr: Address) -> bool
```

DEPRECATED

Check whether an agent message is part of a registered dialogue.

**Arguments**:

- `msg`: the agent message
- `agent_addr`: the address of the agent

**Returns**:

boolean indicating whether the message belongs to a registered dialogue

<a name=".aea.helpers.dialogue.base.Dialogues.is_permitted_for_new_dialogue"></a>
#### is`_`permitted`_`for`_`new`_`dialogue

```python
 | is_permitted_for_new_dialogue(msg: Message) -> bool
```

DEPRECATED

Check whether an agent message is permitted for a new dialogue.

**Arguments**:

- `msg`: the agent message

**Returns**:

a boolean indicating whether the message is permitted for a new dialogue

<a name=".aea.helpers.dialogue.base.Dialogues.get_dialogue"></a>
#### get`_`dialogue

```python
 | get_dialogue(msg: Message, address: Address) -> Dialogue
```

DEPRECATED

Retrieve dialogue.

**Arguments**:

- `fipa_msg`: the fipa message
- `agent_addr`: the address of the agent

**Returns**:

the dialogue

<a name=".aea.helpers.dialogue.base.Dialogues.create_self_initiated"></a>
#### create`_`self`_`initiated

```python
 | create_self_initiated(dialogue_opponent_addr: Address, role: Dialogue.Role) -> Dialogue
```

DEPRECATED

Create a self initiated dialogue.

**Arguments**:

- `dialogue_opponent_addr`: the pbk of the agent with which the dialogue is kept.
- `role`: the agent's role

**Returns**:

the created dialogue.

<a name=".aea.helpers.dialogue.base.Dialogues.create_opponent_initiated"></a>
#### create`_`opponent`_`initiated

```python
 | create_opponent_initiated(dialogue_opponent_addr: Address, dialogue_reference: Tuple[str, str], role: Dialogue.Role) -> Dialogue
```

DEPRECATED

Create an opponent initiated dialogue.

**Arguments**:

- `dialogue_opponent_addr`: the address of the agent with which the dialogue is kept.
- `dialogue_reference`: the reference of the dialogue.
- `role`: the agent's role

**Returns**:

the created dialogue

