<a name=".aea.decision_maker.base"></a>
## aea.decision`_`maker.base

This module contains the decision maker class.

<a name=".aea.decision_maker.base.GoalPursuitReadiness"></a>
### GoalPursuitReadiness

```python
class GoalPursuitReadiness()
```

The goal pursuit readiness.

<a name=".aea.decision_maker.base.GoalPursuitReadiness.Status"></a>
### Status

```python
class Status(Enum)
```

The enum of the readiness status.

In particular, it can be one of the following:

- Status.READY: when the agent is ready to pursuit its goal
- Status.NOT_READY: when the agent is not ready to pursuit its goal

<a name=".aea.decision_maker.base.GoalPursuitReadiness.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate the goal pursuit readiness.

<a name=".aea.decision_maker.base.GoalPursuitReadiness.is_ready"></a>
#### is`_`ready

```python
 | @property
 | is_ready() -> bool
```

Get the readiness.

<a name=".aea.decision_maker.base.GoalPursuitReadiness.update"></a>
#### update

```python
 | update(new_status: Status) -> None
```

Update the goal pursuit readiness.

**Arguments**:

- `new_status`: the new status

**Returns**:

None

<a name=".aea.decision_maker.base.OwnershipState"></a>
### OwnershipState

```python
class OwnershipState()
```

Represent the ownership state of an agent.

<a name=".aea.decision_maker.base.OwnershipState.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate an ownership state object.

**Arguments**:

- `decision_maker`: the decision maker

<a name=".aea.decision_maker.base.OwnershipState.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | is_initialized() -> bool
```

Get the initialization status.

<a name=".aea.decision_maker.base.OwnershipState.amount_by_currency_id"></a>
#### amount`_`by`_`currency`_`id

```python
 | @property
 | amount_by_currency_id() -> CurrencyHoldings
```

Get currency holdings in this state.

<a name=".aea.decision_maker.base.OwnershipState.quantities_by_good_id"></a>
#### quantities`_`by`_`good`_`id

```python
 | @property
 | quantities_by_good_id() -> GoodHoldings
```

Get good holdings in this state.

<a name=".aea.decision_maker.base.OwnershipState.is_affordable_transaction"></a>
#### is`_`affordable`_`transaction

```python
 | is_affordable_transaction(tx_message: TransactionMessage) -> bool
```

Check if the transaction is affordable (and consistent).

E.g. check that the agent state has enough money if it is a buyer or enough holdings if it is a seller.
Note, the agent is the sender of the transaction message by design.

**Arguments**:

- `tx_message`: the transaction message

**Returns**:

True if the transaction is legal wrt the current state, false otherwise.

<a name=".aea.decision_maker.base.OwnershipState.apply_transactions"></a>
#### apply`_`transactions

```python
 | apply_transactions(transactions: List[TransactionMessage]) -> "OwnershipState"
```

Apply a list of transactions to (a copy of) the current state.

**Arguments**:

- `transactions`: the sequence of transaction messages.

**Returns**:

the final state.

<a name=".aea.decision_maker.base.OwnershipState.__copy__"></a>
#### `__`copy`__`

```python
 | __copy__() -> "OwnershipState"
```

Copy the object.

<a name=".aea.decision_maker.base.LedgerStateProxy"></a>
### LedgerStateProxy

```python
class LedgerStateProxy()
```

Class to represent a proxy to a ledger state.

<a name=".aea.decision_maker.base.LedgerStateProxy.__init__"></a>
#### `__`init`__`

```python
 | __init__(ledger_apis: LedgerApis)
```

Instantiate a ledger state proxy.

<a name=".aea.decision_maker.base.LedgerStateProxy.ledger_apis"></a>
#### ledger`_`apis

```python
 | @property
 | ledger_apis() -> LedgerApis
```

Get the ledger_apis.

<a name=".aea.decision_maker.base.LedgerStateProxy.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | is_initialized() -> bool
```

Get the initialization status.

<a name=".aea.decision_maker.base.LedgerStateProxy.is_affordable_transaction"></a>
#### is`_`affordable`_`transaction

```python
 | is_affordable_transaction(tx_message: TransactionMessage) -> bool
```

Check if the transaction is affordable on the default ledger.

**Arguments**:

- `tx_message`: the transaction message

**Returns**:

whether the transaction is affordable on the ledger

<a name=".aea.decision_maker.base.Preferences"></a>
### Preferences

```python
class Preferences()
```

Class to represent the preferences.

<a name=".aea.decision_maker.base.Preferences.__init__"></a>
#### `__`init`__`

```python
 | __init__()
```

Instantiate an agent preference object.

<a name=".aea.decision_maker.base.Preferences.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | is_initialized() -> bool
```

Get the initialization status.

Returns True if exchange_params_by_currency_id and utility_params_by_good_id are not None.

<a name=".aea.decision_maker.base.Preferences.exchange_params_by_currency_id"></a>
#### exchange`_`params`_`by`_`currency`_`id

```python
 | @property
 | exchange_params_by_currency_id() -> ExchangeParams
```

Get exchange parameter for each currency.

<a name=".aea.decision_maker.base.Preferences.utility_params_by_good_id"></a>
#### utility`_`params`_`by`_`good`_`id

```python
 | @property
 | utility_params_by_good_id() -> UtilityParams
```

Get utility parameter for each good.

<a name=".aea.decision_maker.base.Preferences.transaction_fees"></a>
#### transaction`_`fees

```python
 | @property
 | transaction_fees() -> Dict[str, int]
```

Get the transaction fee.

<a name=".aea.decision_maker.base.Preferences.logarithmic_utility"></a>
#### logarithmic`_`utility

```python
 | logarithmic_utility(quantities_by_good_id: GoodHoldings) -> float
```

Compute agent's utility given her utility function params and a good bundle.

**Arguments**:

- `quantities_by_good_id`: the good holdings (dictionary) with the identifier (key) and quantity (value) for each good

**Returns**:

utility value

<a name=".aea.decision_maker.base.Preferences.linear_utility"></a>
#### linear`_`utility

```python
 | linear_utility(amount_by_currency_id: CurrencyHoldings) -> float
```

Compute agent's utility given her utility function params and a currency bundle.

**Arguments**:

- `amount_by_currency_id`: the currency holdings (dictionary) with the identifier (key) and quantity (value) for each currency

**Returns**:

utility value

<a name=".aea.decision_maker.base.Preferences.utility"></a>
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

<a name=".aea.decision_maker.base.Preferences.marginal_utility"></a>
#### marginal`_`utility

```python
 | marginal_utility(ownership_state: OwnershipState, delta_quantities_by_good_id: Optional[GoodHoldings] = None, delta_amount_by_currency_id: Optional[CurrencyHoldings] = None) -> float
```

Compute the marginal utility.

**Arguments**:

- `ownership_state`: the ownership state against which to compute the marginal utility.
- `delta_quantities_by_good_id`: the change in good holdings
- `delta_amount_by_currency_id`: the change in money holdings

**Returns**:

the marginal utility score

<a name=".aea.decision_maker.base.Preferences.utility_diff_from_transaction"></a>
#### utility`_`diff`_`from`_`transaction

```python
 | utility_diff_from_transaction(ownership_state: OwnershipState, tx_message: TransactionMessage) -> float
```

Simulate a transaction and get the resulting utility difference (taking into account the fee).

**Arguments**:

- `ownership_state`: the ownership state against which to apply the transaction.
- `tx_message`: a transaction message.

**Returns**:

the score.

<a name=".aea.decision_maker.base.ProtectedQueue"></a>
### ProtectedQueue

```python
class ProtectedQueue(Queue)
```

A wrapper of a queue to protect which object can read from it.

<a name=".aea.decision_maker.base.ProtectedQueue.__init__"></a>
#### `__`init`__`

```python
 | __init__(access_code: str)
```

Initialize the protected queue.

**Arguments**:

- `access_code`: the access code to read from the queue

<a name=".aea.decision_maker.base.ProtectedQueue.put"></a>
#### put

```python
 | put(internal_message: Optional[InternalMessage], block=True, timeout=None) -> None
```

Put an internal message on the queue.

If optional args block is true and timeout is None (the default),
block if necessary until a free slot is available. If timeout is
a positive number, it blocks at most timeout seconds and raises
the Full exception if no free slot was available within that time.
Otherwise (block is false), put an item on the queue if a free slot
is immediately available, else raise the Full exception (timeout is
ignored in that case).

**Arguments**:

- `internal_message`: the internal message to put on the queue
:raises: ValueError, if the item is not an internal message

**Returns**:

None

<a name=".aea.decision_maker.base.ProtectedQueue.put_nowait"></a>
#### put`_`nowait

```python
 | put_nowait(internal_message: Optional[InternalMessage]) -> None
```

Put an internal message on the queue.

Equivalent to put(item, False).

**Arguments**:

- `internal_message`: the internal message to put on the queue
:raises: ValueError, if the item is not an internal message

**Returns**:

None

<a name=".aea.decision_maker.base.ProtectedQueue.get"></a>
#### get

```python
 | get(block=True, timeout=None) -> None
```

Inaccessible get method.

:raises: ValueError, access not permitted.

**Returns**:

None

<a name=".aea.decision_maker.base.ProtectedQueue.get_nowait"></a>
#### get`_`nowait

```python
 | get_nowait() -> None
```

Inaccessible get_nowait method.

:raises: ValueError, access not permitted.

**Returns**:

None

<a name=".aea.decision_maker.base.ProtectedQueue.protected_get"></a>
#### protected`_`get

```python
 | protected_get(access_code: str, block=True, timeout=None) -> Optional[InternalMessage]
```

Access protected get method.

**Arguments**:

- `access_code`: the access code
- `block`: If optional args block is true and timeout is None (the default), block if necessary until an item is available.
- `timeout`: If timeout is a positive number, it blocks at most timeout seconds and raises the Empty exception if no item was available within that time.
:raises: ValueError, if caller is not permitted

**Returns**:

internal message

<a name=".aea.decision_maker.base.DecisionMaker"></a>
### DecisionMaker

```python
class DecisionMaker()
```

This class implements the decision maker.

<a name=".aea.decision_maker.base.DecisionMaker.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, wallet: Wallet, ledger_apis: LedgerApis)
```

Initialize the decision maker.

**Arguments**:

- `identity`: the identity
- `wallet`: the wallet
- `ledger_apis`: the ledger apis

<a name=".aea.decision_maker.base.DecisionMaker.message_in_queue"></a>
#### message`_`in`_`queue

```python
 | @property
 | message_in_queue() -> ProtectedQueue
```

Get (in) queue.

<a name=".aea.decision_maker.base.DecisionMaker.message_out_queue"></a>
#### message`_`out`_`queue

```python
 | @property
 | message_out_queue() -> Queue
```

Get (out) queue.

<a name=".aea.decision_maker.base.DecisionMaker.wallet"></a>
#### wallet

```python
 | @property
 | wallet() -> Wallet
```

Get wallet.

<a name=".aea.decision_maker.base.DecisionMaker.ledger_apis"></a>
#### ledger`_`apis

```python
 | @property
 | ledger_apis() -> LedgerApis
```

Get ledger apis.

<a name=".aea.decision_maker.base.DecisionMaker.ownership_state"></a>
#### ownership`_`state

```python
 | @property
 | ownership_state() -> OwnershipState
```

Get ownership state.

<a name=".aea.decision_maker.base.DecisionMaker.ledger_state_proxy"></a>
#### ledger`_`state`_`proxy

```python
 | @property
 | ledger_state_proxy() -> LedgerStateProxy
```

Get ledger state proxy.

<a name=".aea.decision_maker.base.DecisionMaker.preferences"></a>
#### preferences

```python
 | @property
 | preferences() -> Preferences
```

Get preferences.

<a name=".aea.decision_maker.base.DecisionMaker.goal_pursuit_readiness"></a>
#### goal`_`pursuit`_`readiness

```python
 | @property
 | goal_pursuit_readiness() -> GoalPursuitReadiness
```

Get readiness of agent to pursuit its goals.

<a name=".aea.decision_maker.base.DecisionMaker.start"></a>
#### start

```python
 | start() -> None
```

Start the decision maker.

<a name=".aea.decision_maker.base.DecisionMaker.stop"></a>
#### stop

```python
 | stop() -> None
```

Stop the decision maker.

<a name=".aea.decision_maker.base.DecisionMaker.execute"></a>
#### execute

```python
 | execute() -> None
```

Execute the decision maker.

Performs the following while not stopped:

- gets internal messages from the in queue and calls handle() on them

**Returns**:

None

<a name=".aea.decision_maker.base.DecisionMaker.handle"></a>
#### handle

```python
 | handle(message: InternalMessage) -> None
```

Handle an internal message from the skills.

**Arguments**:

- `message`: the internal message

**Returns**:

None

