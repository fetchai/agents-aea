<a name="aea.decision_maker.default"></a>
# aea.decision`_`maker.default

This module contains the decision maker class.

<a name="aea.decision_maker.default.DecisionMakerHandler"></a>
## DecisionMakerHandler Objects

```python
class DecisionMakerHandler(BaseDecisionMakerHandler)
```

This class implements the decision maker.

<a name="aea.decision_maker.default.DecisionMakerHandler.SigningDialogues"></a>
## SigningDialogues Objects

```python
class SigningDialogues(BaseSigningDialogues)
```

This class keeps track of all oef_search dialogues.

<a name="aea.decision_maker.default.DecisionMakerHandler.SigningDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(self_address: Address, **kwargs: Any) -> None
```

Initialize dialogues.

**Arguments**:

- `self_address`: the address of the entity for whom dialogues are maintained
- `kwargs`: the keyword arguments

<a name="aea.decision_maker.default.DecisionMakerHandler.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, wallet: Wallet, config: Dict[str, Any]) -> None
```

Initialize the decision maker.

**Arguments**:

- `identity`: the identity
- `wallet`: the wallet
- `config`: the user defined configuration of the handler

<a name="aea.decision_maker.default.DecisionMakerHandler.handle"></a>
#### handle

```python
 | handle(message: Message) -> None
```

Handle an internal message from the skills.

**Arguments**:

- `message`: the internal message

