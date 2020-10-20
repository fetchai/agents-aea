<a name="packages.fetchai.protocols.state_update.dialogues"></a>
# packages.fetchai.protocols.state`_`update.dialogues

This module contains the classes required for state_update dialogue management.

- StateUpdateDialogue: The dialogue class maintains state of a dialogue and manages it.
- StateUpdateDialogues: The dialogues class keeps track of all dialogues.

<a name="packages.fetchai.protocols.state_update.dialogues.StateUpdateDialogue"></a>
## StateUpdateDialogue Objects

```python
class StateUpdateDialogue(Dialogue)
```

The state_update dialogue class maintains state of a dialogue and manages it.

<a name="packages.fetchai.protocols.state_update.dialogues.StateUpdateDialogue.Role"></a>
## Role Objects

```python
class Role(Dialogue.Role)
```

This class defines the agent's role in a state_update dialogue.

<a name="packages.fetchai.protocols.state_update.dialogues.StateUpdateDialogue.EndState"></a>
## EndState Objects

```python
class EndState(Dialogue.EndState)
```

This class defines the end states of a state_update dialogue.

<a name="packages.fetchai.protocols.state_update.dialogues.StateUpdateDialogue.__init__"></a>
#### `__`init`__`

```python
 | __init__(dialogue_label: DialogueLabel, self_address: Address, role: Dialogue.Role, message_class: Type[StateUpdateMessage] = StateUpdateMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for

**Returns**:

None

<a name="packages.fetchai.protocols.state_update.dialogues.StateUpdateDialogues"></a>
## StateUpdateDialogues Objects

```python
class StateUpdateDialogues(Dialogues,  ABC)
```

This class keeps track of all state_update dialogues.

<a name="packages.fetchai.protocols.state_update.dialogues.StateUpdateDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(self_address: Address, role_from_first_message: Callable[[Message, Address], Dialogue.Role], dialogue_class: Type[StateUpdateDialogue] = StateUpdateDialogue) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom dialogues are maintained

**Returns**:

None

