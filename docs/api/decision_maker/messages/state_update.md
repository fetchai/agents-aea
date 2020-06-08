<a name=".aea.decision_maker.messages.state_update"></a>
# aea.decision`_`maker.messages.state`_`update

The state update message module.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage"></a>
## StateUpdateMessage Objects

```python
class StateUpdateMessage(InternalMessage)
```

The state update message class.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.Performative"></a>
## Performative Objects

```python
class Performative(Enum)
```

State update performative.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.__init__"></a>
#### `__`init`__`

```python
 | __init__(performative: Performative, amount_by_currency_id: Currencies, quantities_by_good_id: Goods, **kwargs)
```

Instantiate transaction message.

**Arguments**:

- `performative`: the performative
- `amount_by_currency_id`: the amounts of currencies.
- `quantities_by_good_id`: the quantities of goods.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.performative"></a>
#### performative

```python
 | @property
 | performative() -> Performative
```

Get the performative of the message.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.amount_by_currency_id"></a>
#### amount`_`by`_`currency`_`id

```python
 | @property
 | amount_by_currency_id() -> Currencies
```

Get the amount by currency.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.quantities_by_good_id"></a>
#### quantities`_`by`_`good`_`id

```python
 | @property
 | quantities_by_good_id() -> Goods
```

Get the quantities by good id.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.exchange_params_by_currency_id"></a>
#### exchange`_`params`_`by`_`currency`_`id

```python
 | @property
 | exchange_params_by_currency_id() -> ExchangeParams
```

Get the exchange parameters by currency from the message.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.utility_params_by_good_id"></a>
#### utility`_`params`_`by`_`good`_`id

```python
 | @property
 | utility_params_by_good_id() -> UtilityParams
```

Get the utility parameters by good id.

<a name=".aea.decision_maker.messages.state_update.StateUpdateMessage.tx_fee"></a>
#### tx`_`fee

```python
 | @property
 | tx_fee() -> int
```

Get the transaction fee.

