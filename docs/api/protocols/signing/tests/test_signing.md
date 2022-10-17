<a id="packages.open_aea.protocols.signing.tests.test_signing"></a>

# packages.open`_`aea.protocols.signing.tests.test`_`signing

This module contains tests for transaction.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestSigningMessage"></a>

## TestSigningMessage Objects

```python
class TestSigningMessage()
```

Test the signing message module.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestSigningMessage.setup_class"></a>

#### setup`_`class

```python
@classmethod
def setup_class(cls)
```

Setup class for test case.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestSigningMessage.test_sign_transaction"></a>

#### test`_`sign`_`transaction

```python
def test_sign_transaction()
```

Test for an error for a sign transaction message.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestSigningMessage.test_sign_message"></a>

#### test`_`sign`_`message

```python
def test_sign_message()
```

Test for an error for a sign transaction message.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestSigningMessage.test_signed_transaction"></a>

#### test`_`signed`_`transaction

```python
def test_signed_transaction()
```

Test for an error for a signed transaction.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestSigningMessage.test_signed_message"></a>

#### test`_`signed`_`message

```python
def test_signed_message()
```

Test for an error for a signed message.

<a id="packages.open_aea.protocols.signing.tests.test_signing.TestSigningMessage.test_error_message"></a>

#### test`_`error`_`message

```python
def test_error_message()
```

Test for an error for an error message.

<a id="packages.open_aea.protocols.signing.tests.test_signing.test_consistency_check_negative"></a>

#### test`_`consistency`_`check`_`negative

```python
def test_consistency_check_negative()
```

Test the consistency check, negative case.

<a id="packages.open_aea.protocols.signing.tests.test_signing.test_serialization_negative"></a>

#### test`_`serialization`_`negative

```python
def test_serialization_negative()
```

Test serialization when performative is not recognized.

<a id="packages.open_aea.protocols.signing.tests.test_signing.test_dialogues"></a>

#### test`_`dialogues

```python
def test_dialogues()
```

Test intiaontiation of dialogues.

<a id="packages.open_aea.protocols.signing.tests.test_signing.SigningDialogue"></a>

## SigningDialogue Objects

```python
class SigningDialogue(BaseSigningDialogue)
```

The dialogue class maintains state of a dialogue and manages it.

<a id="packages.open_aea.protocols.signing.tests.test_signing.SigningDialogue.__init__"></a>

#### `__`init`__`

```python
def __init__(dialogue_label: DialogueLabel, self_address: Address, role: BaseDialogue.Role, message_class: Type[SigningMessage]) -> None
```

Initialize a dialogue.

**Arguments**:

- `dialogue_label`: the identifier of the dialogue
- `self_address`: the address of the entity for whom this dialogue is maintained
- `role`: the role of the agent this dialogue is maintained for
- `message_class`: the message class

<a id="packages.open_aea.protocols.signing.tests.test_signing.SigningDialogues"></a>

## SigningDialogues Objects

```python
class SigningDialogues(BaseSigningDialogues)
```

The dialogues class keeps track of all dialogues.

<a id="packages.open_aea.protocols.signing.tests.test_signing.SigningDialogues.__init__"></a>

#### `__`init`__`

```python
def __init__(self_address: Address) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom this dialogues is maintained

