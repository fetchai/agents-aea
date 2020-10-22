<a name="packages.fetchai.protocols.signing.dialogues"></a>
# packages.fetchai.protocols.signing.dialogues

This module contains the classes required for signing dialogue management.

- SigningDialogue: The dialogue class maintains state of a dialogue and manages it.
- SigningDialogues: The dialogues class keeps track of all dialogues.

<a name="packages.fetchai.protocols.signing.dialogues.SigningDialogue"></a>
## SigningDialogue Objects

```python
class SigningDialogue(Dialogue)
```

The signing dialogue class maintains state of a dialogue and manages it.

<a name="packages.fetchai.protocols.signing.dialogues.SigningDialogue.Role"></a>
## Role Objects

```python
class Role(Dialogue.Role)
```

This class defines the agent's role in a signing dialogue.

<a name="packages.fetchai.protocols.signing.dialogues.SigningDialogue.EndState"></a>
## EndState Objects

```python
class EndState(Dialogue.EndState)
```

This class defines the end states of a signing dialogue.

<a name="packages.fetchai.protocols.signing.dialogues.SigningDialogue.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_label: DialogueLabel, self_address: Address, role: Dialogue.Role, message_class: Type[SigningMessage] = SigningMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

None

<a name="packages.fetchai.protocols.signing.dialogues.SigningDialogues"></a>
## SigningDialogues Objects

```python
class SigningDialogues(Dialogues,  ABC)
```

This class keeps track of all signing dialogues.

<a name="packages.fetchai.protocols.signing.dialogues.SigningDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(self_address: Address, role_from_first_message: Callable[[Message, Address], Dialogue.Role], dialogue_class: Type[SigningDialogue] = SigningDialogue) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom dialogues are maintained

**Returns**:

None

