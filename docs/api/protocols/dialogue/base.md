<a id="aea.protocols.dialogue.base"></a>

# aea.protocols.dialogue.base

This module contains the classes required for dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.

<a id="aea.protocols.dialogue.base.InvalidDialogueMessage"></a>

## InvalidDialogueMessage Objects

```python
class InvalidDialogueMessage(Exception)
```

Exception for adding invalid message to a dialogue.

<a id="aea.protocols.dialogue.base.DialogueLabel"></a>

## DialogueLabel Objects

```python
class DialogueLabel()
```

The dialogue label class acts as an identifier for dialogues.

<a id="aea.protocols.dialogue.base.DialogueLabel.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_reference: Tuple[str,
                                       str], dialogue_opponent_addr: Address,
             dialogue_starter_addr: Address) -> None
```

Initialize a dialogue label.

**Arguments**:

- `dialogue_reference`: the reference of the dialogue.
- `dialogue_opponent_addr`: the addr of the agent with which the dialogue is kept.
- `dialogue_starter_addr`: the addr of the agent which started the dialogue.

<a id="aea.protocols.dialogue.base.DialogueLabel.dialogue_reference"></a>

#### dialogue`_`reference

```python
@property
def dialogue_reference() -> Tuple[str, str]
```

Get the dialogue reference.

<a id="aea.protocols.dialogue.base.DialogueLabel.dialogue_starter_reference"></a>

#### dialogue`_`starter`_`reference

```python
@property
def dialogue_starter_reference() -> str
```

Get the dialogue starter reference.

<a id="aea.protocols.dialogue.base.DialogueLabel.dialogue_responder_reference"></a>

#### dialogue`_`responder`_`reference

```python
@property
def dialogue_responder_reference() -> str
```

Get the dialogue responder reference.

<a id="aea.protocols.dialogue.base.DialogueLabel.dialogue_opponent_addr"></a>

#### dialogue`_`opponent`_`addr

```python
@property
def dialogue_opponent_addr() -> str
```

Get the address of the dialogue opponent.

<a id="aea.protocols.dialogue.base.DialogueLabel.dialogue_starter_addr"></a>

#### dialogue`_`starter`_`addr

```python
@property
def dialogue_starter_addr() -> str
```

Get the address of the dialogue starter.

<a id="aea.protocols.dialogue.base.DialogueLabel.__eq__"></a>

#### `__`eq`__`

```python
def __eq__(other: Any) -> bool
```

Check for equality between two DialogueLabel objects.

<a id="aea.protocols.dialogue.base.DialogueLabel.__hash__"></a>

#### `__`hash`__`

```python
def __hash__() -> int
```

Turn object into hash.

<a id="aea.protocols.dialogue.base.DialogueLabel.json"></a>

#### json

```python
@property
def json() -> Dict
```

Return the JSON representation.

<a id="aea.protocols.dialogue.base.DialogueLabel.from_json"></a>

#### from`_`json

```python
@classmethod
def from_json(cls, obj: Dict[str, str]) -> "DialogueLabel"
```

Get dialogue label from json.

<a id="aea.protocols.dialogue.base.DialogueLabel.is_complete"></a>

#### is`_`complete

```python
def is_complete() -> bool
```

Check if the dialogue label is complete.

<a id="aea.protocols.dialogue.base.DialogueLabel.get_incomplete_version"></a>

#### get`_`incomplete`_`version

```python
def get_incomplete_version() -> "DialogueLabel"
```

Get the incomplete version of the label.

<a id="aea.protocols.dialogue.base.DialogueLabel.get_both_versions"></a>

#### get`_`both`_`versions

```python
def get_both_versions() -> Tuple["DialogueLabel", Optional["DialogueLabel"]]
```

Get the incomplete and complete versions of the label.

<a id="aea.protocols.dialogue.base.DialogueLabel.__str__"></a>

#### `__`str`__`

```python
def __str__() -> str
```

Get the string representation.

<a id="aea.protocols.dialogue.base.DialogueLabel.from_str"></a>

#### from`_`str

```python
@classmethod
def from_str(cls, obj: str) -> "DialogueLabel"
```

Get the dialogue label from string representation.

<a id="aea.protocols.dialogue.base._DialogueMeta"></a>

## `_`DialogueMeta Objects

```python
class _DialogueMeta(type)
```

Metaclass for Dialogue.

Creates class level Rules instance to share among instances

<a id="aea.protocols.dialogue.base._DialogueMeta.__new__"></a>

#### `__`new`__`

```python
def __new__(cls, name: str, bases: Tuple[Type], dct: Dict) -> "_DialogueMeta"
```

Construct a new type.

<a id="aea.protocols.dialogue.base.Dialogue"></a>

## Dialogue Objects

