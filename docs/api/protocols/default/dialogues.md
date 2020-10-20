<a name="packages.fetchai.protocols.default.dialogues"></a>
# packages.fetchai.protocols.default.dialogues

This module contains the classes required for default dialogue management.

- DefaultDialogue: The dialogue class maintains state of a dialogue and manages it.
- DefaultDialogues: The dialogues class keeps track of all dialogues.

<a name="packages.fetchai.protocols.default.dialogues.DefaultDialogue"></a>
## DefaultDialogue Objects

```python
class DefaultDialogue(Dialogue)
```

The default dialogue class maintains state of a dialogue and manages it.

<a name="packages.fetchai.protocols.default.dialogues.DefaultDialogue.Role"></a>
## Role Objects

```python
class Role(Dialogue.Role)
```

This class defines the agent's role in a default dialogue.

<a name="packages.fetchai.protocols.default.dialogues.DefaultDialogue.EndState"></a>
## EndState Objects

```python
class EndState(Dialogue.EndState)
```

This class defines the end states of a default dialogue.

<a name="packages.fetchai.protocols.default.dialogues.DefaultDialogue.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_label: DialogueLabel, self_address: Address, role: Dialogue.Role, message_class: Type[DefaultMessage] = DefaultMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

None

<a name="packages.fetchai.protocols.default.dialogues.DefaultDialogues"></a>
## DefaultDialogues Objects

```python
class DefaultDialogues(Dialogues,  ABC)
```

This class keeps track of all default dialogues.

<a name="packages.fetchai.protocols.default.dialogues.DefaultDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(self_address: Address, role_from_first_message: Callable[[Message, Address], Dialogue.Role], dialogue_class: Type[DefaultDialogue] = DefaultDialogue) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom dialogues are maintained

**Returns**:

None

