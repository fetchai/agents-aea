<a name="packages.fetchai.protocols.state_update.message"></a>
# packages.fetchai.protocols.state`_`update.message

This module contains state_update's message definition.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage"></a>
## StateUpdateMessage Objects

```python
class StateUpdateMessage(Message)
```

A protocol for state updates to the decision maker state.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.Performative"></a>
## Performative Objects

```python
class Performative(Message.Performative)
```

Performatives for the state_update protocol.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.Performative.__str__"></a>
#### `__`str`__`

```python
 | __str__() -> str
```

Get the string representation.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(performative: Performative, dialogue_reference: Tuple[str, str] = ("", ""), message_id: int = 1, target: int = 0, **kwargs: Any, ,)
```

Initialise an instance of StateUpdateMessage.

**Arguments**:

- `message_id`: the message id.
- `dialogue_reference`: the dialogue reference.
- `target`: the message target.
- `performative`: the message performative.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.valid_performatives"></a>
#### valid`_`performatives

```python
 | @property
 | valid_performatives() -> Set[str]
```

Get valid performatives.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.dialogue_reference"></a>
#### dialogue`_`reference

```python
 | @property
 | dialogue_reference() -> Tuple[str, str]
```

Get the dialogue_reference of the message.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.message_id"></a>
#### message`_`id

```python
 | @property
 | message_id() -> int
```

Get the message_id of the message.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.performative"></a>
#### performative

```python
 | @property
 | performative() -> Performative
```

Get the performative of the message.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.target"></a>
#### target

```python
 | @property
 | target() -> int
```

Get the target of the message.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.amount_by_currency_id"></a>
#### amount`_`by`_`currency`_`id

```python
 | @property
 | amount_by_currency_id() -> Dict[str, int]
```

Get the 'amount_by_currency_id' content from the message.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.exchange_params_by_currency_id"></a>
#### exchange`_`params`_`by`_`currency`_`id

```python
 | @property
 | exchange_params_by_currency_id() -> Dict[str, float]
```

Get the 'exchange_params_by_currency_id' content from the message.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.quantities_by_good_id"></a>
#### quantities`_`by`_`good`_`id

```python
 | @property
 | quantities_by_good_id() -> Dict[str, int]
```

Get the 'quantities_by_good_id' content from the message.

<a name="packages.fetchai.protocols.state_update.message.StateUpdateMessage.utility_params_by_good_id"></a>
#### utility`_`params`_`by`_`good`_`id

```python
 | @property
 | utility_params_by_good_id() -> Dict[str, float]
```

Get the 'utility_params_by_good_id' content from the message.

