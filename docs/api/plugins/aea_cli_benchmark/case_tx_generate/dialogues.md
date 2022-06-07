<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues"></a>

# plugins.aea-cli-benchmark.aea`_`cli`_`benchmark.case`_`tx`_`generate.dialogues

Ledger TX generation and processing benchmark.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.SigningDialogues"></a>

## SigningDialogues Objects

```python
class SigningDialogues(BaseSigningDialogues)
```

This class keeps track of all oef_search dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.SigningDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(self_address: Address) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom dialogues are maintained

**Returns**:

None

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.FipaDialogue"></a>

## FipaDialogue Objects

```python
class FipaDialogue(BaseFipaDialogue)
```

The dialogue class maintains state of a dialogue and manages it.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.FipaDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_label: BaseDialogueLabel,
             self_address: Address,
             role: BaseDialogue.Role,
             message_class: Type[FipaMessage] = FipaMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.FipaDialogue.terms"></a>

#### terms

```python
@property
def terms() -> Terms
```

Get terms.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.FipaDialogue.terms"></a>

#### terms

```python
@terms.setter
def terms(terms: Terms) -> None
```

Set terms.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.FipaDialogues"></a>

## FipaDialogues Objects

```python
class FipaDialogues(Model, BaseFipaDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.FipaDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.LedgerApiDialogue"></a>

## LedgerApiDialogue Objects

```python
class LedgerApiDialogue(BaseLedgerApiDialogue)
```

The dialogue class maintains state of a dialogue and manages it.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.LedgerApiDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_label: BaseDialogueLabel,
             self_address: Address,
             role: BaseDialogue.Role,
             message_class: Type[LedgerApiMessage] = LedgerApiMessage) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.LedgerApiDialogue.associated_fipa_dialogue"></a>

#### associated`_`fipa`_`dialogue

```python
@property
def associated_fipa_dialogue() -> FipaDialogue
```

Get associated_fipa_dialogue.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.LedgerApiDialogue.associated_fipa_dialogue"></a>

#### associated`_`fipa`_`dialogue

```python
@associated_fipa_dialogue.setter
def associated_fipa_dialogue(fipa_dialogue: FipaDialogue) -> None
```

Set associated_fipa_dialogue

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.LedgerApiDialogues"></a>

## LedgerApiDialogues Objects

```python
class LedgerApiDialogues(Model, BaseLedgerApiDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="plugins.aea-cli-benchmark.aea_cli_benchmark.case_tx_generate.dialogues.LedgerApiDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `kwargs`: keyword arguments

