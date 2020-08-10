<a name="aea.protocols.default.dialogues"></a>
# aea.protocols.default.dialogues

This module contains the classes required for default dialogue management.

- DefaultDialogue: The dialogue class maintains state of a dialogue and manages it.
- DefaultDialogues: The dialogues class keeps track of all dialogues.

<a name="aea.protocols.default.dialogues.DefaultDialogue"></a>
## DefaultDialogue Objects

```python
class DefaultDialogue(Dialogue)
```

The default dialogue class maintains state of a dialogue and manages it.

<a name="aea.protocols.default.dialogues.DefaultDialogue.Role"></a>
## Role Objects

```python
class Role(Dialogue.Role)
```

This class defines the agent's role in a default dialogue.

<a name="aea.protocols.default.dialogues.DefaultDialogue.EndState"></a>
## EndState Objects

```python
class EndState(Dialogue.EndState)
```

This class defines the end states of a default dialogue.

<a name="aea.protocols.default.dialogues.DefaultDialogue.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_label: DialogueLabel, agent_address: Optional[Address] = None, role: Optional[Dialogue.Role] = None) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `agent_address`: the address of the agent for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

None

<a name="aea.protocols.default.dialogues.DefaultDialogue.is_valid"></a>
#### is`_`valid

```python
 | is_valid(message: Message) -> bool
```

Check whether 'message' is a valid next message in the dialogue.

These rules capture specific constraints designed for dialogues which are instances of a concrete sub-class of this class.
Override this method with your additional dialogue rules.

**Arguments**:

- `message`: the message to be validated

**Returns**:

True if valid, False otherwise

<a name="aea.protocols.default.dialogues.DefaultDialogues"></a>
## DefaultDialogues Objects

```python
class DefaultDialogues(Dialogues,  ABC)
```

This class keeps track of all default dialogues.

<a name="aea.protocols.default.dialogues.DefaultDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_address: Address) -> None
```

Initialize dialogues.

**Arguments**:

- `agent_address`: the address of the agent for whom dialogues are maintained

**Returns**:

None

<a name="aea.protocols.default.dialogues.DefaultDialogues.create_dialogue"></a>
#### create`_`dialogue

```python
 | create_dialogue(dialogue_label: DialogueLabel, role: Dialogue.Role) -> DefaultDialogue
```

Create an instance of default dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

the created dialogue

