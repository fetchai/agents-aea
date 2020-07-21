<a name="aea.helpers.dialogue.base"></a>
# aea.helpers.dialogue.base

This module contains the classes required for dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.

<a name="aea.helpers.dialogue.base.DialogueLabel"></a>
## DialogueLabel Objects

```python
class DialogueLabel()
```

The dialogue label class acts as an identifier for dialogues.

<a name="aea.helpers.dialogue.base.DialogueLabel.__init__"></a>
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

<a name="aea.helpers.dialogue.base.DialogueLabel.dialogue_reference"></a>
#### dialogue`_`reference

```python
 | @property
 | dialogue_reference() -> Tuple[str, str]
```

Get the dialogue reference.

<a name="aea.helpers.dialogue.base.DialogueLabel.dialogue_starter_reference"></a>
#### dialogue`_`starter`_`reference

```python
 | @property
 | dialogue_starter_reference() -> str
```

Get the dialogue starter reference.

<a name="aea.helpers.dialogue.base.DialogueLabel.dialogue_responder_reference"></a>
#### dialogue`_`responder`_`reference

```python
 | @property
 | dialogue_responder_reference() -> str
```

Get the dialogue responder reference.

<a name="aea.helpers.dialogue.base.DialogueLabel.dialogue_opponent_addr"></a>
#### dialogue`_`opponent`_`addr

```python
 | @property
 | dialogue_opponent_addr() -> str
```

Get the address of the dialogue opponent.

<a name="aea.helpers.dialogue.base.DialogueLabel.dialogue_starter_addr"></a>
#### dialogue`_`starter`_`addr

```python
 | @property
 | dialogue_starter_addr() -> str
```

Get the address of the dialogue starter.

<a name="aea.helpers.dialogue.base.DialogueLabel.__eq__"></a>
#### `__`eq`__`

```python
 | __eq__(other) -> bool
```

Check for equality between two DialogueLabel objects.

<a name="aea.helpers.dialogue.base.DialogueLabel.__hash__"></a>
#### `__`hash`__`

```python
 | __hash__() -> int
```

Turn object into hash.

<a name="aea.helpers.dialogue.base.DialogueLabel.json"></a>
#### json

```python
 | @property
 | json() -> Dict
```

Return the JSON representation.

<a name="aea.helpers.dialogue.base.DialogueLabel.from_json"></a>
#### from`_`json

```python
 | @classmethod
 | from_json(cls, obj: Dict[str, str]) -> "DialogueLabel"
```

Get dialogue label from json.

<a name="aea.helpers.dialogue.base.DialogueLabel.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name="aea.helpers.dialogue.base.Dialogue"></a>
## Dialogue Objects

```python
class Dialogue(ABC)
```

The dialogue class maintains state of a dialogue and manages it.

<a name="aea.helpers.dialogue.base.Dialogue.Rules"></a>
## Rules Objects

```python
class Rules()
```

This class defines the rules for the dialogue.

<a name="aea.helpers.dialogue.base.Dialogue.Rules.__init__"></a>
#### `__`init`__`

```python
 | __init__(initial_performatives: FrozenSet[Message.Performative], terminal_performatives: FrozenSet[Message.Performative], valid_replies: Dict[Message.Performative, FrozenSet[Message.Performative]]) -> None
```

Initialize a dialogue.

**Arguments**:

- `initial_performatives`: the set of all initial performatives.
- `terminal_performatives`: the set of all terminal performatives.
- `valid_replies`: the reply structure of speech-acts.

**Returns**:

None

<a name="aea.helpers.dialogue.base.Dialogue.Rules.initial_performatives"></a>
#### initial`_`performatives

```python
 | @property
 | initial_performatives() -> FrozenSet[Message.Performative]
```

Get the performatives one of which the terminal message in the dialogue must have.

**Returns**:

the valid performatives of an terminal message

<a name="aea.helpers.dialogue.base.Dialogue.Rules.terminal_performatives"></a>
#### terminal`_`performatives

```python
 | @property
 | terminal_performatives() -> FrozenSet[Message.Performative]
```

Get the performatives one of which the terminal message in the dialogue must have.

**Returns**:

the valid performatives of an terminal message

<a name="aea.helpers.dialogue.base.Dialogue.Rules.valid_replies"></a>
#### valid`_`replies

```python
 | @property
 | valid_replies() -> Dict[Message.Performative, FrozenSet[Message.Performative]]
```

Get all the valid performatives which are a valid replies to performatives.

**Returns**:

the full valid reply structure.

<a name="aea.helpers.dialogue.base.Dialogue.Rules.get_valid_replies"></a>
#### get`_`valid`_`replies

```python
 | get_valid_replies(performative: Message.Performative) -> FrozenSet[Message.Performative]
```

Given a `performative`, return the list of performatives which are its valid replies in a dialogue.

**Arguments**:

- `performative`: the performative in a message

**Returns**:

list of valid performative replies

<a name="aea.helpers.dialogue.base.Dialogue.Role"></a>
## Role Objects

```python
class Role(Enum)
```

This class defines the agent's role in a dialogue.

<a name="aea.helpers.dialogue.base.Dialogue.Role.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name="aea.helpers.dialogue.base.Dialogue.EndState"></a>
## EndState Objects

```python
class EndState(Enum)
```

This class defines the end states of a dialogue.

<a name="aea.helpers.dialogue.base.Dialogue.EndState.__str__"></a>
#### `__`str`__`

```python
 | __str__()
```

Get the string representation.

<a name="aea.helpers.dialogue.base.Dialogue.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_label: DialogueLabel, message_class: Optional[Type[Message]] = None, agent_address: Optional[Address] = None, role: Optional[Role] = None, rules: Optional[Rules] = None) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `agent_address`: the address of the agent for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `rules`: the rules of the dialogue

**Returns**:

None

<a name="aea.helpers.dialogue.base.Dialogue.dialogue_label"></a>
#### dialogue`_`label

```python
 | @property
 | dialogue_label() -> DialogueLabel
```

Get the dialogue label.

**Returns**:

The dialogue label

<a name="aea.helpers.dialogue.base.Dialogue.agent_address"></a>
#### agent`_`address

```python
 | @property
 | agent_address() -> Address
```

Get the address of the agent for whom this dialogues is maintained.

**Returns**:

the agent address

<a name="aea.helpers.dialogue.base.Dialogue.agent_address"></a>
#### agent`_`address

```python
 | @agent_address.setter
 | agent_address(agent_address: Address) -> None
```

Set the address of the agent for whom this dialogues is maintained.

:param: the agent address

<a name="aea.helpers.dialogue.base.Dialogue.role"></a>
#### role

```python
 | @property
 | role() -> "Role"
```

Get the agent's role in the dialogue.

**Returns**:

the agent's role

<a name="aea.helpers.dialogue.base.Dialogue.role"></a>
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

<a name="aea.helpers.dialogue.base.Dialogue.rules"></a>
#### rules

```python
 | @property
 | rules() -> "Rules"
```

Get the dialogue rules.

**Returns**:

the rules

<a name="aea.helpers.dialogue.base.Dialogue.is_self_initiated"></a>
#### is`_`self`_`initiated

```python
 | @property
 | is_self_initiated() -> bool
```

Check whether the agent initiated the dialogue.

**Returns**:

True if the agent initiated the dialogue, False otherwise

<a name="aea.helpers.dialogue.base.Dialogue.last_incoming_message"></a>
#### last`_`incoming`_`message

```python
 | @property
 | last_incoming_message() -> Optional[Message]
```

Get the last incoming message.

**Returns**:

the last incoming message if it exists, None otherwise

<a name="aea.helpers.dialogue.base.Dialogue.last_outgoing_message"></a>
#### last`_`outgoing`_`message

```python
 | @property
 | last_outgoing_message() -> Optional[Message]
```

Get the last outgoing message.

**Returns**:

the last outgoing message if it exists, None otherwise

<a name="aea.helpers.dialogue.base.Dialogue.last_message"></a>
#### last`_`message

```python
 | @property
 | last_message() -> Optional[Message]
```

Get the last message.

**Returns**:

the last message if it exists, None otherwise

<a name="aea.helpers.dialogue.base.Dialogue.get_message"></a>
#### get`_`message

```python
 | get_message(message_id_to_find: int) -> Optional[Message]
```

Get the message whose id is 'message_id'.

**Arguments**:

- `message_id_to_find`: the id of the message

**Returns**:

the message if it exists, None otherwise

<a name="aea.helpers.dialogue.base.Dialogue.is_empty"></a>
#### is`_`empty

```python
 | @property
 | is_empty() -> bool
```

Check whether the dialogue is empty.

**Returns**:

True if empty, False otherwise

<a name="aea.helpers.dialogue.base.Dialogue.update"></a>
#### update

```python
 | update(message: Message) -> bool
```

Extend the list of incoming/outgoing messages with 'message', if 'message' is valid.

**Arguments**:

- `message`: a message to be added

**Returns**:

True if message successfully added, false otherwise

<a name="aea.helpers.dialogue.base.Dialogue.reply"></a>
#### reply

```python
 | reply(target_message: Message, performative, **kwargs) -> Message
```

Reply to the 'target_message' in this dialogue with a message with 'performative', and contents from kwargs.

**Arguments**:

- `target_message`: the message to reply to.
- `performative`: the performative of the reply message.
- `kwargs`: the content of the reply message.

**Returns**:

the reply message if it was successfully added as a reply, None otherwise.

<a name="aea.helpers.dialogue.base.Dialogue.is_valid_next_message"></a>
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

<a name="aea.helpers.dialogue.base.Dialogue.update_dialogue_label"></a>
#### update`_`dialogue`_`label

```python
 | update_dialogue_label(final_dialogue_label: DialogueLabel) -> None
```

Update the dialogue label of the dialogue.

**Arguments**:

- `final_dialogue_label`: the final dialogue label

<a name="aea.helpers.dialogue.base.Dialogue.is_valid"></a>
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

<a name="aea.helpers.dialogue.base.Dialogue.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

**Returns**:

The string representation of the dialogue

<a name="aea.helpers.dialogue.base.DialogueStats"></a>
## DialogueStats Objects

```python
class DialogueStats(ABC)
```

Class to handle statistics on default dialogues.

<a name="aea.helpers.dialogue.base.DialogueStats.__init__"></a>
#### `__`init`__`

```python
 | __init__(end_states: FrozenSet[Dialogue.EndState]) -> None
```

Initialize a StatsManager.

**Arguments**:

- `end_states`: the list of dialogue endstates

<a name="aea.helpers.dialogue.base.DialogueStats.self_initiated"></a>
#### self`_`initiated

```python
 | @property
 | self_initiated() -> Dict[Dialogue.EndState, int]
```

Get the stats dictionary on self initiated dialogues.

<a name="aea.helpers.dialogue.base.DialogueStats.other_initiated"></a>
#### other`_`initiated

```python
 | @property
 | other_initiated() -> Dict[Dialogue.EndState, int]
```

Get the stats dictionary on other initiated dialogues.

<a name="aea.helpers.dialogue.base.DialogueStats.add_dialogue_endstate"></a>
#### add`_`dialogue`_`endstate

```python
 | add_dialogue_endstate(end_state: Dialogue.EndState, is_self_initiated: bool) -> None
```

Add dialogue endstate stats.

**Arguments**:

- `end_state`: the end state of the dialogue
- `is_self_initiated`: whether the dialogue is initiated by the agent or the opponent

**Returns**:

None

<a name="aea.helpers.dialogue.base.Dialogues"></a>
## Dialogues Objects

```python
class Dialogues(ABC)
```

The dialogues class keeps track of all dialogues for an agent.

<a name="aea.helpers.dialogue.base.Dialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_address: Address, end_states: FrozenSet[Dialogue.EndState], message_class: Optional[Type[Message]] = None, dialogue_class: Optional[Type[Dialogue]] = None, role_from_first_message: Optional[Callable[[Message], Dialogue.Role]] = None) -> None
```

Initialize dialogues.

**Arguments**:

- `agent_address`: the address of the agent for whom dialogues are maintained
- `end_states`: the list of dialogue endstates

**Returns**:

None

<a name="aea.helpers.dialogue.base.Dialogues.dialogues"></a>
#### dialogues

```python
 | @property
 | dialogues() -> Dict[DialogueLabel, Dialogue]
```

Get dictionary of dialogues in which the agent engages.

<a name="aea.helpers.dialogue.base.Dialogues.agent_address"></a>
#### agent`_`address

```python
 | @property
 | agent_address() -> Address
```

Get the address of the agent for whom dialogues are maintained.

<a name="aea.helpers.dialogue.base.Dialogues.dialogue_stats"></a>
#### dialogue`_`stats

```python
 | @property
 | dialogue_stats() -> DialogueStats
```

Get the dialogue statistics.

**Returns**:

dialogue stats object

<a name="aea.helpers.dialogue.base.Dialogues.new_self_initiated_dialogue_reference"></a>
#### new`_`self`_`initiated`_`dialogue`_`reference

```python
 | new_self_initiated_dialogue_reference() -> Tuple[str, str]
```

Return a dialogue label for a new self initiated dialogue.

**Returns**:

the next nonce

<a name="aea.helpers.dialogue.base.Dialogues.create"></a>
#### create

```python
 | create(counterparty: Address, performative: Message.Performative, **kwargs, ,) -> Tuple[Message, Dialogue]
```

Create a dialogue with 'counterparty', with an initial message whose performative is 'performative' and contents are from 'kwargs'.

**Arguments**:

- `counterparty`: the counterparty of the dialogue.
- `performative`: the performative of the initial message.
- `kwargs`: the content of the initial message.

**Returns**:

the initial message and the dialogue.

<a name="aea.helpers.dialogue.base.Dialogues.update"></a>
#### update

```python
 | update(message: Message) -> Optional[Dialogue]
```

Update the state of dialogues with a new incoming message.

If the message is for a new dialogue, a new dialogue is created with 'message' as its first message, and returned.
If the message is addressed to an existing dialogue, the dialogue is retrieved, extended with this message and returned.
If there are any errors, e.g. the message dialogue reference does not exists or the message is invalid w.r.t. the dialogue, return None.

**Arguments**:

- `message`: a new message

**Returns**:

the new or existing dialogue the message is intended for, or None in case of any errors.

<a name="aea.helpers.dialogue.base.Dialogues.get_dialogue"></a>
#### get`_`dialogue

```python
 | get_dialogue(message: Message) -> Optional[Dialogue]
```

Retrieve the dialogue 'message' belongs to.

**Arguments**:

- `message`: a message

**Returns**:

the dialogue, or None in case such a dialogue does not exist

<a name="aea.helpers.dialogue.base.Dialogues.get_dialogue_from_label"></a>
#### get`_`dialogue`_`from`_`label

```python
 | get_dialogue_from_label(dialogue_label: DialogueLabel) -> Optional[Dialogue]
```

Retrieve a dialogue based on its label.

**Arguments**:

- `dialogue_label`: the dialogue label

**Returns**:

the dialogue if present

<a name="aea.helpers.dialogue.base.Dialogues.create_dialogue"></a>
#### create`_`dialogue

```python
 | @abstractmethod
 | create_dialogue(dialogue_label: DialogueLabel, role: Dialogue.Role) -> Dialogue
```

THIS METHOD IS DEPRECATED AND WILL BE REMOVED IN THE NEXT VERSION. USE THE NEW CONSTRUCTOR ARGUMENTS INSTEAD.

Create a dialogue instance.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

the created dialogue

<a name="aea.helpers.dialogue.base.Dialogues.role_from_first_message"></a>
#### role`_`from`_`first`_`message

```python
 | @staticmethod
 | role_from_first_message(message: Message) -> Dialogue.Role
```

Infer the role of the agent from an incoming or outgoing first message.

**Arguments**:

- `message`: an incoming/outgoing first message

**Returns**:

the agent's role

