<a name="aea.protocols.signing.dialogues"></a>
# aea.protocols.signing.dialogues

This module contains the classes required for signing dialogue management.

- SigningDialogue: The dialogue class maintains state of a dialogue and manages it.
- SigningDialogues: The dialogues class keeps track of all dialogues.

<a name="aea.protocols.signing.dialogues.SigningDialogue"></a>
## SigningDialogue Objects

```python
class SigningDialogue(Dialogue)
```

The signing dialogue class maintains state of a dialogue and manages it.

<a name="aea.protocols.signing.dialogues.SigningDialogue.Role"></a>
## Role Objects

```python
class Role(Dialogue.Role)
```

This class defines the agent's role in a signing dialogue.

<a name="aea.protocols.signing.dialogues.SigningDialogue.EndState"></a>
## EndState Objects

```python
class EndState(Dialogue.EndState)
```

This class defines the end states of a signing dialogue.

<a name="aea.protocols.signing.dialogues.SigningDialogue.__init__"></a>
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

<a name="aea.protocols.signing.dialogues.SigningDialogue.is_valid"></a>
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

<a name="aea.protocols.signing.dialogues.SigningDialogues"></a>
## SigningDialogues Objects

```python
class SigningDialogues(Dialogues,  ABC)
```

This class keeps track of all signing dialogues.

<a name="aea.protocols.signing.dialogues.SigningDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(agent_address: Address) -> None
```

Initialize dialogues.

**Arguments**:

- `agent_address`: the address of the agent for whom dialogues are maintained

**Returns**:

None

<a name="aea.protocols.signing.dialogues.SigningDialogues.create_dialogue"></a>
#### create`_`dialogue

```python
 | create_dialogue(dialogue_label: DialogueLabel, role: Dialogue.Role) -> SigningDialogue
```

Create an instance of signing dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

the created dialogue

