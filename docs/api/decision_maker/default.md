<a name="aea.decision_maker.default"></a>
# aea.decision`_`maker.default

This module contains the decision maker class.

<a name="aea.decision_maker.default.SigningDialogues"></a>
## SigningDialogues Objects

```python
class SigningDialogues(BaseSigningDialogues)
```

This class keeps track of all oef_search dialogues.

<a name="aea.decision_maker.default.SigningDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs) -> None
```

Initialize dialogues.

**Arguments**:

- `agent_address`: the address of the agent for whom dialogues are maintained

**Returns**:

None

<a name="aea.decision_maker.default.StateUpdateDialogues"></a>
## StateUpdateDialogues Objects

```python
class StateUpdateDialogues(BaseStateUpdateDialogues)
```

This class keeps track of all oef_search dialogues.

<a name="aea.decision_maker.default.StateUpdateDialogues.__init__"></a>
#### `__`init`__`

```python
 | __init__(**kwargs) -> None
```

Initialize dialogues.

**Arguments**:

- `agent_address`: the address of the agent for whom dialogues are maintained

**Returns**:

None

<a name="aea.decision_maker.default.GoalPursuitReadiness"></a>
## GoalPursuitReadiness Objects

```python
class GoalPursuitReadiness()
```

The goal pursuit readiness.

<a name="aea.decision_maker.default.GoalPursuitReadiness.Status"></a>
## Status Objects

```python
class Status(Enum)
```

The enum of the readiness status.

In particular, it can be one of the following:

- Status.READY: when the agent is ready to pursuit its goal
- Status.NOT_READY: when the agent is not ready to pursuit its goal

<a name="aea.decision_maker.default.GoalPursuitReadiness.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate the goal pursuit readiness.

<a name="aea.decision_maker.default.GoalPursuitReadiness.is_ready"></a>
#### is`_`ready

```python
 | @property
 | is_ready() -> bool
```

Get the readiness.

<a name="aea.decision_maker.default.GoalPursuitReadiness.update"></a>
#### update

```python
 | update(new_status: Status) -> None
```

Update the goal pursuit readiness.

**Arguments**:

- `new_status`: the new status

**Returns**:

None

<a name="aea.decision_maker.default.OwnershipState"></a>
## OwnershipState Objects

```python
class OwnershipState(BaseOwnershipState)
```

Represent the ownership state of an agent (can proxy a ledger).

<a name="aea.decision_maker.default.OwnershipState.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate an ownership state object.

**Arguments**:

- `decision_maker`: the decision maker

<a name="aea.decision_maker.default.OwnershipState.set"></a>
#### set

```python
 | set(amount_by_currency_id: CurrencyHoldings = None, quantities_by_good_id: GoodHoldings = None, **kwargs, ,) -> None
```

Set values on the ownership state.

**Arguments**:

- `amount_by_currency_id`: the currency endowment of the agent in this state.
- `quantities_by_good_id`: the good endowment of the agent in this state.

<a name="aea.decision_maker.default.OwnershipState.apply_delta"></a>
#### apply`_`delta

```python
 | apply_delta(delta_amount_by_currency_id: Dict[str, int] = None, delta_quantities_by_good_id: Dict[str, int] = None, **kwargs, ,) -> None
```

Apply a state update to the ownership state.

This method is used to apply a raw state update without a transaction.

**Arguments**:

- `delta_amount_by_currency_id`: the delta in the currency amounts
- `delta_quantities_by_good_id`: the delta in the quantities by good

**Returns**:

None

<a name="aea.decision_maker.default.OwnershipState.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | is_initialized() -> bool
```

Get the initialization status.

<a name="aea.decision_maker.default.OwnershipState.amount_by_currency_id"></a>
#### amount`_`by`_`currency`_`id

```python
 | @property
 | amount_by_currency_id() -> CurrencyHoldings
```

Get currency holdings in this state.

<a name="aea.decision_maker.default.OwnershipState.quantities_by_good_id"></a>
#### quantities`_`by`_`good`_`id

```python
 | @property
 | quantities_by_good_id() -> GoodHoldings
```

Get good holdings in this state.

<a name="aea.decision_maker.default.OwnershipState.is_affordable_transaction"></a>
#### is`_`affordable`_`transaction

```python
 | is_affordable_transaction(terms: Terms) -> bool
```

Check if the transaction is affordable (and consistent).

E.g. check that the agent state has enough money if it is a buyer or enough holdings if it is a seller.
Note, the agent is the sender of the transaction message by design.

**Arguments**:

- `terms`: the transaction terms

**Returns**:

True if the transaction is legal wrt the current state, false otherwise.

<a name="aea.decision_maker.default.OwnershipState.is_affordable"></a>
#### is`_`affordable

```python
 | is_affordable(terms: Terms) -> bool
```

Check if the tx is affordable.

**Arguments**:

- `terms`: the transaction terms

**Returns**:

whether the transaction is affordable or not

<a name="aea.decision_maker.default.OwnershipState.update"></a>
#### update

```python
 | update(terms: Terms) -> None
```

Update the agent state from a transaction.

**Arguments**:

- `terms`: the transaction terms

**Returns**:

None

<a name="aea.decision_maker.default.OwnershipState.apply_transactions"></a>
#### apply`_`transactions

```python
 | apply_transactions(list_of_terms: List[Terms]) -> "OwnershipState"
```

Apply a list of transactions to (a copy of) the current state.

**Arguments**:

- `list_of_terms`: the sequence of transaction terms.

**Returns**:

the final state.

<a name="aea.decision_maker.default.OwnershipState.__copy__"></a>
#### `__`copy`__`

```python
 | __copy__() -> "OwnershipState"
```

Copy the object.

<a name="aea.decision_maker.default.Preferences"></a>
## Preferences Objects

```python
class Preferences(BasePreferences)
```

Class to represent the preferences.

<a name="aea.decision_maker.default.Preferences.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate an agent preference object.

<a name="aea.decision_maker.default.Preferences.set"></a>
#### set

```python
 | set(exchange_params_by_currency_id: ExchangeParams = None, utility_params_by_good_id: UtilityParams = None, **kwargs, ,) -> None
```

Set values on the preferences.

**Arguments**:

- `exchange_params_by_currency_id`: the exchange params.
- `utility_params_by_good_id`: the utility params for every asset.

<a name="aea.decision_maker.default.Preferences.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | is_initialized() -> bool
```

Get the initialization status.

Returns True if exchange_params_by_currency_id and utility_params_by_good_id are not None.

<a name="aea.decision_maker.default.Preferences.exchange_params_by_currency_id"></a>
#### exchange`_`params`_`by`_`currency`_`id

```python
 | @property
 | exchange_params_by_currency_id() -> ExchangeParams
```

Get exchange parameter for each currency.

<a name="aea.decision_maker.default.Preferences.utility_params_by_good_id"></a>
#### utility`_`params`_`by`_`good`_`id

```python
 | @property
 | utility_params_by_good_id() -> UtilityParams
```

Get utility parameter for each good.

<a name="aea.decision_maker.default.Preferences.logarithmic_utility"></a>
#### logarithmic`_`utility

```python
 | logarithmic_utility(quantities_by_good_id: GoodHoldings) -> float
```

Compute agent's utility given her utility function params and a good bundle.

**Arguments**:

- `quantities_by_good_id`: the good holdings (dictionary) with the identifier (key) and quantity (value) for each good

**Returns**:

utility value

<a name="aea.decision_maker.default.Preferences.linear_utility"></a>
#### linear`_`utility

```python
 | linear_utility(amount_by_currency_id: CurrencyHoldings) -> float
```

Compute agent's utility given her utility function params and a currency bundle.

**Arguments**:

- `amount_by_currency_id`: the currency holdings (dictionary) with the identifier (key) and quantity (value) for each currency

**Returns**:

utility value

<a name="aea.decision_maker.default.Preferences.utility"></a>
#### utility

```python
 | utility(quantities_by_good_id: GoodHoldings, amount_by_currency_id: CurrencyHoldings) -> float
```

Compute the utility given the good and currency holdings.

**Arguments**:

- `quantities_by_good_id`: the good holdings
- `amount_by_currency_id`: the currency holdings

**Returns**:

the utility value.

<a name="aea.decision_maker.default.Preferences.marginal_utility"></a>
#### marginal`_`utility

```python
 | marginal_utility(ownership_state: BaseOwnershipState, delta_quantities_by_good_id: Optional[GoodHoldings] = None, delta_amount_by_currency_id: Optional[CurrencyHoldings] = None, **kwargs, ,) -> float
```

Compute the marginal utility.

**Arguments**:

- `ownership_state`: the ownership state against which to compute the marginal utility.
- `delta_quantities_by_good_id`: the change in good holdings
- `delta_amount_by_currency_id`: the change in money holdings

**Returns**:

the marginal utility score

<a name="aea.decision_maker.default.Preferences.utility_diff_from_transaction"></a>
#### utility`_`diff`_`from`_`transaction

```python
 | utility_diff_from_transaction(ownership_state: BaseOwnershipState, terms: Terms) -> float
```

Simulate a transaction and get the resulting utility difference (taking into account the fee).

**Arguments**:

- `ownership_state`: the ownership state against which to apply the transaction.
- `terms`: the transaction terms.

**Returns**:

the score.

<a name="aea.decision_maker.default.Preferences.is_utility_enhancing"></a>
#### is`_`utility`_`enhancing

```python
 | is_utility_enhancing(ownership_state: BaseOwnershipState, terms: Terms) -> bool
```

Check if the tx is utility enhancing.

**Arguments**:

- `ownership_state`: the ownership state against which to apply the transaction.
- `terms`: the transaction terms

**Returns**:

whether the transaction is utility enhancing or not

<a name="aea.decision_maker.default.Preferences.__copy__"></a>
#### `__`copy`__`

```python
 | __copy__() -> "Preferences"
```

Copy the object.

<a name="aea.decision_maker.default.DecisionMakerHandler"></a>
## DecisionMakerHandler Objects

```python
class DecisionMakerHandler(BaseDecisionMakerHandler)
```

This class implements the decision maker.

<a name="aea.decision_maker.default.DecisionMakerHandler.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, wallet: Wallet)
```

Initialize the decision maker.

**Arguments**:

- `identity`: the identity
- `wallet`: the wallet

<a name="aea.decision_maker.default.DecisionMakerHandler.handle"></a>
#### handle

```python
 | handle(message: Message) -> None
```

Handle an internal message from the skills.

**Arguments**:

- `message`: the internal message

**Returns**:

None

