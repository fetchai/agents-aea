<a id="aea.skills.behaviours"></a>

# aea.skills.behaviours

This module contains the classes for specific behaviours.

<a id="aea.skills.behaviours.SimpleBehaviour"></a>

## SimpleBehaviour Objects

```python
class SimpleBehaviour(Behaviour, ABC)
```

This class implements a simple behaviour.

<a id="aea.skills.behaviours.SimpleBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(act: Optional[Callable[[], None]] = None, **kwargs: Any) -> None
```

Initialize a simple behaviour.

**Arguments**:

- `act`: the act callable.
- `kwargs`: the keyword arguments to be passed to the parent class.

<a id="aea.skills.behaviours.SimpleBehaviour.setup"></a>

#### setup

```python
def setup() -> None
```

Set the behaviour up.

<a id="aea.skills.behaviours.SimpleBehaviour.act"></a>

#### act

```python
def act() -> None
```

Do the action.

<a id="aea.skills.behaviours.SimpleBehaviour.teardown"></a>

#### teardown

```python
def teardown() -> None
```

Tear the behaviour down.

<a id="aea.skills.behaviours.CompositeBehaviour"></a>

## CompositeBehaviour Objects

```python
class CompositeBehaviour(Behaviour, ABC)
```

This class implements a composite behaviour.

<a id="aea.skills.behaviours.CyclicBehaviour"></a>

## CyclicBehaviour Objects

```python
class CyclicBehaviour(SimpleBehaviour, ABC)
```

This behaviour is executed until the agent is stopped.

<a id="aea.skills.behaviours.CyclicBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the cyclic behaviour.

<a id="aea.skills.behaviours.CyclicBehaviour.number_of_executions"></a>

#### number`_`of`_`executions

```python
@property
def number_of_executions() -> int
```

Get the number of executions.

<a id="aea.skills.behaviours.CyclicBehaviour.act_wrapper"></a>

#### act`_`wrapper

```python
def act_wrapper() -> None
```

Wrap the call of the action. This method must be called only by the framework.

<a id="aea.skills.behaviours.CyclicBehaviour.is_done"></a>

#### is`_`done

```python
def is_done() -> bool
```

Return True if the behaviour is terminated, False otherwise.

The user should implement it properly to determine the stopping condition.

**Returns**:

bool indicating status

<a id="aea.skills.behaviours.OneShotBehaviour"></a>

## OneShotBehaviour Objects

```python
class OneShotBehaviour(SimpleBehaviour, ABC)
```

This behaviour is executed only once.

<a id="aea.skills.behaviours.OneShotBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the cyclic behaviour.

<a id="aea.skills.behaviours.OneShotBehaviour.is_done"></a>

#### is`_`done

```python
def is_done() -> bool
```

Return True if the behaviour is terminated, False otherwise.

<a id="aea.skills.behaviours.OneShotBehaviour.act_wrapper"></a>

#### act`_`wrapper

```python
def act_wrapper() -> None
```

Wrap the call of the action. This method must be called only by the framework.

<a id="aea.skills.behaviours.TickerBehaviour"></a>

## TickerBehaviour Objects

```python
class TickerBehaviour(SimpleBehaviour, ABC)
```

This behaviour is executed periodically with an interval.

<a id="aea.skills.behaviours.TickerBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(tick_interval: float = 1.0,
             start_at: Optional[datetime.datetime] = None,
             **kwargs: Any) -> None
```

Initialize the ticker behaviour.

**Arguments**:

- `tick_interval`: interval of the behaviour in seconds.
- `start_at`: whether to start the behaviour with an offset.
- `kwargs`: the keyword arguments.

<a id="aea.skills.behaviours.TickerBehaviour.tick_interval"></a>

#### tick`_`interval

```python
@property
def tick_interval() -> float
```

Get the tick_interval in seconds.

<a id="aea.skills.behaviours.TickerBehaviour.start_at"></a>

#### start`_`at

```python
@property
def start_at() -> datetime.datetime
```

Get the start time.

<a id="aea.skills.behaviours.TickerBehaviour.last_act_time"></a>

#### last`_`act`_`time

```python
@property
def last_act_time() -> datetime.datetime
```

Get the last time the act method has been called.

<a id="aea.skills.behaviours.TickerBehaviour.act_wrapper"></a>

#### act`_`wrapper

```python
def act_wrapper() -> None
```

Wrap the call of the action. This method must be called only by the framework.

<a id="aea.skills.behaviours.TickerBehaviour.is_time_to_act"></a>

#### is`_`time`_`to`_`act

```python
def is_time_to_act() -> bool
```

Check whether it is time to act, according to the tick_interval constraint and the 'start at' constraint.

**Returns**:

True if it is time to act, false otherwise.

<a id="aea.skills.behaviours.SequenceBehaviour"></a>

## SequenceBehaviour Objects

```python
class SequenceBehaviour(CompositeBehaviour, ABC)
```

This behaviour executes sub-behaviour serially.

<a id="aea.skills.behaviours.SequenceBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(behaviour_sequence: List[Behaviour], **kwargs: Any) -> None
```

Initialize the sequence behaviour.

**Arguments**:

- `behaviour_sequence`: the sequence of behaviour.
- `kwargs`: the keyword arguments

<a id="aea.skills.behaviours.SequenceBehaviour.current_behaviour"></a>

#### current`_`behaviour

```python
@property
def current_behaviour() -> Optional[Behaviour]
```

Get the current behaviour.

If None, the sequence behaviour can be considered done.

**Returns**:

current behaviour or None

<a id="aea.skills.behaviours.SequenceBehaviour.act"></a>

#### act

```python
def act() -> None
```

Implement the behaviour.

<a id="aea.skills.behaviours.SequenceBehaviour.is_done"></a>

#### is`_`done

```python
def is_done() -> bool
```

Return True if the behaviour is terminated, False otherwise.

<a id="aea.skills.behaviours.State"></a>

## State Objects

```python
class State(SimpleBehaviour, ABC)
```

A state of a FSMBehaviour.

A State behaviour is a simple behaviour with a
special property 'event' that is opportunely set
by the implementer. The event is read by the framework
when the behaviour is done in order to pick the
transition to trigger.

<a id="aea.skills.behaviours.State.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize a state of the state machine.

<a id="aea.skills.behaviours.State.event"></a>

#### event

```python
@property
def event() -> Optional[str]
```

Get the event to be triggered at the end of the behaviour.

<a id="aea.skills.behaviours.State.is_done"></a>

#### is`_`done

```python
@abstractmethod
def is_done() -> bool
```

Return True if the behaviour is terminated, False otherwise.

<a id="aea.skills.behaviours.State.reset"></a>

#### reset

```python
def reset() -> None
```

Reset initial conditions.

<a id="aea.skills.behaviours.FSMBehaviour"></a>

## FSMBehaviour Objects

```python
class FSMBehaviour(CompositeBehaviour, ABC)
```

This class implements a finite-state machine behaviour.

<a id="aea.skills.behaviours.FSMBehaviour.__init__"></a>

#### `__`init`__`

```python
def __init__(**kwargs: Any) -> None
```

Initialize the finite-state machine behaviour.

<a id="aea.skills.behaviours.FSMBehaviour.is_started"></a>

#### is`_`started

```python
@property
def is_started() -> bool
```

Check if the behaviour is started.

<a id="aea.skills.behaviours.FSMBehaviour.register_state"></a>

#### register`_`state

```python
def register_state(name: str, state: State, initial: bool = False) -> None
```

Register a state.

**Arguments**:

- `name`: the name of the state.
- `state`: the behaviour in that state.
- `initial`: whether the state is an initial state.

**Raises**:

- `ValueError`: if a state with the provided name already exists.

<a id="aea.skills.behaviours.FSMBehaviour.register_final_state"></a>

#### register`_`final`_`state

```python
def register_final_state(name: str, state: State) -> None
```

Register a final state.

**Arguments**:

- `name`: the name of the state.
- `state`: the state.

**Raises**:

- `ValueError`: if a state with the provided name already exists.

<a id="aea.skills.behaviours.FSMBehaviour.unregister_state"></a>

#### unregister`_`state

```python
def unregister_state(name: str) -> None
```

Unregister a state.

**Arguments**:

- `name`: the state name to unregister.

**Raises**:

- `ValueError`: if the state is not registered.

<a id="aea.skills.behaviours.FSMBehaviour.states"></a>

#### states

```python
@property
def states() -> Set[str]
```

Get all the state names.

<a id="aea.skills.behaviours.FSMBehaviour.initial_state"></a>

#### initial`_`state

```python
@property
def initial_state() -> Optional[str]
```

Get the initial state name.

<a id="aea.skills.behaviours.FSMBehaviour.initial_state"></a>

#### initial`_`state

```python
@initial_state.setter
def initial_state(name: str) -> None
```

Set the initial state.

<a id="aea.skills.behaviours.FSMBehaviour.final_states"></a>

#### final`_`states

```python
@property
def final_states() -> Set[str]
```

Get the final state names.

<a id="aea.skills.behaviours.FSMBehaviour.get_state"></a>

#### get`_`state

```python
def get_state(name: str) -> Optional[State]
```

Get a state from its name.

<a id="aea.skills.behaviours.FSMBehaviour.act"></a>

#### act

```python
def act() -> None
```

Implement the behaviour.

<a id="aea.skills.behaviours.FSMBehaviour.is_done"></a>

#### is`_`done

```python
def is_done() -> bool
```

Return True if the behaviour is terminated, False otherwise.

<a id="aea.skills.behaviours.FSMBehaviour.register_transition"></a>

#### register`_`transition

```python
def register_transition(source: str,
                        destination: str,
                        event: Optional[str] = None) -> None
```

Register a transition.

No sanity check is done.

**Arguments**:

- `source`: the source state name.
- `destination`: the destination state name.
- `event`: the event.

**Raises**:

- `ValueError`: if a transition from source with event is already present.

<a id="aea.skills.behaviours.FSMBehaviour.unregister_transition"></a>

#### unregister`_`transition

```python
def unregister_transition(source: str,
                          destination: str,
                          event: Optional[str] = None) -> None
```

Unregister a transition.

**Arguments**:

- `source`: the source state name.
- `destination`: the destination state name.
- `event`: the event.

**Raises**:

- `ValueError`: if a transition from source with event is not present.

