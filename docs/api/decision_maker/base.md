<a name=".aea.decision_maker.base"></a>
## aea.decision`_`maker.base

This module contains the decision maker class.

<a name=".aea.decision_maker.base.OwnershipState"></a>
### OwnershipState

```python
class OwnershipState(ABC)
```

Represent the ownership state of an agent.

<a name=".aea.decision_maker.base.OwnershipState.set"></a>
#### set

```python
 | @abstractmethod
 | set(**kwargs) -> None
```

Set values on the ownership state.

**Arguments**:

- `kwargs`: the relevant keyword arguments

**Returns**:

None

<a name=".aea.decision_maker.base.OwnershipState.apply_delta"></a>
#### apply`_`delta

```python
 | @abstractmethod
 | apply_delta(**kwargs) -> None
```

Apply a state update to the ownership state.

This method is used to apply a raw state update without a transaction.

**Arguments**:

- `kwargs`: the relevant keyword arguments

**Returns**:

None

<a name=".aea.decision_maker.base.OwnershipState.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | @abstractmethod
 | is_initialized() -> bool
```

Get the initialization status.

<a name=".aea.decision_maker.base.OwnershipState.is_affordable_transaction"></a>
#### is`_`affordable`_`transaction

```python
 | @abstractmethod
 | is_affordable_transaction(tx_message: TransactionMessage) -> bool
```

Check if the transaction is affordable (and consistent).

**Arguments**:

- `tx_message`: the transaction message

**Returns**:

True if the transaction is legal wrt the current state, false otherwise.

<a name=".aea.decision_maker.base.OwnershipState.apply_transactions"></a>
#### apply`_`transactions

```python
 | @abstractmethod
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
 | @abstractmethod
 | __copy__() -> "OwnershipState"
```

Copy the object.

<a name=".aea.decision_maker.base.LedgerStateProxy"></a>
### LedgerStateProxy

```python
class LedgerStateProxy(ABC)
```

Class to represent a proxy to a ledger state.

<a name=".aea.decision_maker.base.LedgerStateProxy.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | @abstractmethod
 | is_initialized() -> bool
```

Get the initialization status.

<a name=".aea.decision_maker.base.LedgerStateProxy.is_affordable_transaction"></a>
#### is`_`affordable`_`transaction

```python
 | @abstractmethod
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
class Preferences(ABC)
```

Class to represent the preferences.

<a name=".aea.decision_maker.base.Preferences.set"></a>
#### set

```python
 | @abstractmethod
 | set(**kwargs, ,) -> None
```

Set values on the preferences.

**Arguments**:

- `kwargs`: the relevant key word arguments

<a name=".aea.decision_maker.base.Preferences.is_initialized"></a>
#### is`_`initialized

```python
 | @property
 | @abstractmethod
 | is_initialized() -> bool
```

Get the initialization status.

Returns True if exchange_params_by_currency_id and utility_params_by_good_id are not None.

<a name=".aea.decision_maker.base.Preferences.marginal_utility"></a>
#### marginal`_`utility

```python
 | @abstractmethod
 | marginal_utility(ownership_state: OwnershipState, **kwargs, ,) -> float
```

Compute the marginal utility.

**Arguments**:

- `ownership_state`: the ownership state against which to compute the marginal utility.
- `kwargs`: optional keyword argyments

**Returns**:

the marginal utility score

<a name=".aea.decision_maker.base.Preferences.utility_diff_from_transaction"></a>
#### utility`_`diff`_`from`_`transaction

```python
 | @abstractmethod
 | utility_diff_from_transaction(ownership_state: OwnershipState, tx_message: TransactionMessage) -> float
```

Simulate a transaction and get the resulting utility difference (taking into account the fee).

**Arguments**:

- `ownership_state`: the ownership state against which to apply the transaction.
- `tx_message`: a transaction message.

**Returns**:

the score.

<a name=".aea.decision_maker.base.Preferences.__copy__"></a>
#### `__`copy`__`

```python
 | @abstractmethod
 | __copy__() -> "Preferences"
```

Copy the object.

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

<a name=".aea.decision_maker.base.DecisionMakerHandler"></a>
### DecisionMakerHandler

```python
class DecisionMakerHandler(ABC)
```

This class implements the decision maker.

<a name=".aea.decision_maker.base.DecisionMakerHandler.__init__"></a>
#### `__`init`__`

```python
 | __init__(identity: Identity, wallet: Wallet, **kwargs)
```

Initialize the decision maker handler.

**Arguments**:

- `identity`: the identity
- `wallet`: the wallet
- `kwargs`: the key word arguments

<a name=".aea.decision_maker.base.DecisionMakerHandler.identity"></a>
#### identity

```python
 | @property
 | identity() -> Identity
```

The identity of the agent.

<a name=".aea.decision_maker.base.DecisionMakerHandler.wallet"></a>
#### wallet

```python
 | @property
 | wallet() -> Wallet
```

The wallet of the agent.

<a name=".aea.decision_maker.base.DecisionMakerHandler.context"></a>
#### context

```python
 | @property
 | context() -> SimpleNamespace
```

Get the context.

<a name=".aea.decision_maker.base.DecisionMakerHandler.message_out_queue"></a>
#### message`_`out`_`queue

```python
 | @property
 | message_out_queue() -> AsyncFriendlyQueue
```

Get (out) queue.

<a name=".aea.decision_maker.base.DecisionMakerHandler.handle"></a>
#### handle

```python
 | @abstractmethod
 | handle(message: InternalMessage) -> None
```

Handle an internal message from the skills.

**Arguments**:

- `message`: the internal message

**Returns**:

None

<a name=".aea.decision_maker.base.DecisionMaker"></a>
### DecisionMaker

```python
class DecisionMaker()
```

This class implements the decision maker.

<a name=".aea.decision_maker.base.DecisionMaker.__init__"></a>
#### `__`init`__`

```python
 | __init__(decision_maker_handler: DecisionMakerHandler)
```

Initialize the decision maker.

**Arguments**:

- `agent_name`: the agent name
- `decision_maker_handler`: the decision maker handler

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
 | message_out_queue() -> AsyncFriendlyQueue
```

Get (out) queue.

<a name=".aea.decision_maker.base.DecisionMaker.decision_maker_handler"></a>
#### decision`_`maker`_`handler

```python
 | @property
 | decision_maker_handler() -> DecisionMakerHandler
```

Get the decision maker handler.

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

