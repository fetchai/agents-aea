<a name=".aea.helpers.dialogue.base"></a>
## aea.helpers.dialogue.base

This module contains the classes required for dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.

<a name=".aea.helpers.dialogue.base.DialogueLabel"></a>
### DialogueLabel

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
### Dialogue

```python
class Dialogue()
```

The dialogue class maintains state of a dialogue and manages it.

<a name=".aea.helpers.dialogue.base.Dialogue.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_label: DialogueLabel) -> None
```

Initialize a dialogue label.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogue.dialogue_label"></a>
#### dialogue`_`label

```python
 | @property
 | dialogue_label() -> DialogueLabel
```

Get the dialogue lable.

<a name=".aea.helpers.dialogue.base.Dialogue.is_self_initiated"></a>
#### is`_`self`_`initiated

```python
 | @property
 | is_self_initiated() -> bool
```

Check whether the agent initiated the dialogue.

<a name=".aea.helpers.dialogue.base.Dialogue.last_incoming_message"></a>
#### last`_`incoming`_`message

```python
 | @property
 | last_incoming_message() -> Optional[Message]
```

Get the last incoming message.

<a name=".aea.helpers.dialogue.base.Dialogue.last_outgoing_message"></a>
#### last`_`outgoing`_`message

```python
 | @property
 | last_outgoing_message() -> Optional[Message]
```

Get the last incoming message.

<a name=".aea.helpers.dialogue.base.Dialogue.outgoing_extend"></a>
#### outgoing`_`extend

```python
 | outgoing_extend(message: "Message") -> None
```

Extend the list of messages which keeps track of outgoing messages.

**Arguments**:

- `message`: a message to be added

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogue.incoming_extend"></a>
#### incoming`_`extend

```python
 | incoming_extend(message: "Message") -> None
```

Extend the list of messages which keeps track of incoming messages.

**Arguments**:

- `messages`: a message to be added

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogues"></a>
### Dialogues

```python
class Dialogues()
```

The dialogues class keeps track of all dialogues.

<a name=".aea.helpers.dialogue.base.Dialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__() -> None
```

Initialize dialogues.

**Returns**:

None

<a name=".aea.helpers.dialogue.base.Dialogues.dialogues"></a>
#### dialogues

```python
 | @property
 | dialogues() -> Dict[DialogueLabel, Dialogue]
```

Get dictionary of dialogues in which the agent is engaged in.

<a name=".aea.helpers.dialogue.base.Dialogues.is_permitted_for_new_dialogue"></a>
#### is`_`permitted`_`for`_`new`_`dialogue

```python
 | @abstractmethod
 | is_permitted_for_new_dialogue(msg: Message) -> bool
```

Check whether an agent message is permitted for a new dialogue.

**Arguments**:

- `msg`: the agent message

**Returns**:

a boolean indicating whether the message is permitted for a new dialogue

<a name=".aea.helpers.dialogue.base.Dialogues.is_belonging_to_registered_dialogue"></a>
#### is`_`belonging`_`to`_`registered`_`dialogue

```python
 | @abstractmethod
 | is_belonging_to_registered_dialogue(msg: Message, agent_addr: Address) -> bool
```

Check whether an agent message is part of a registered dialogue.

**Arguments**:

- `msg`: the agent message
- `agent_addr`: the address of the agent

**Returns**:

boolean indicating whether the message belongs to a registered dialogue

<a name=".aea.helpers.dialogue.base.Dialogues.get_dialogue"></a>
#### get`_`dialogue

```python
 | @abstractmethod
 | get_dialogue(msg: Message, agent_addr: Address) -> Dialogue
```

Retrieve dialogue.

**Arguments**:

- `msg`: the agent message
- `agent_addr`: the address of the agent

**Returns**:

the dialogue

