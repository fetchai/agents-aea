An AEA developer writes skills that the framework can call.

When you add a skill with the CLI, a directory is created which includes modules for the `Behaviour`, `Task`, and `Handler` classes as well as a configuration file `skill.yaml`.


## Context

The skill has a `SkillContext` object which is shared by all `Handler`, `Behaviour`, and `Task` objects. The skill context also has a link to the `AgentContext`. The `AgentContext` provides read access to AEA specific information like the public key and address of the AEA, its preferences and ownership state. It also provides access to the `OutBox`.

This means it is possible to, at any point, grab the `context` and have access to the code in other parts of the skill and the AEA.

For example, in the `ErrorHandler(Handler)` class, the code often grabs a reference to its context and by doing so can access initialised and running framework objects such as an `OutBox` for putting messages into.

``` python
self.context.outbox.put_message(to=recipient, sender=self.context.agent_address, protocol_id=DefaultMessage.protocol_id, message=DefaultSerializer().encode(reply))
``` 

Importantly, however, a skill does not have access to the context of another skill or protected AEA components like the `DecisionMaker`.


## What to code

Each of the skill classes has three methods that must be implemented. All of them include a `setup()` and `teardown()` method which the developer must implement. 

Then there is a specific method that the framework requires for each class.

### `handlers.py`

There can be none, one or more `Handler` class per skill.

`Handler` classes can receive `Message` objects of one protocol type only. However, `Handler` classes can send `Envelope` objects of any type of protocol they require.

* `handle(self, message: Message)`: is where the skill receives a `Message` of the specified protocol and decides what to do with it.


!!!	Todo
	For example.


### `behaviours.py`

Conceptually, a `Behaviour`  class contains the business logic specific to initial actions initiated by the AEA rather than reactions to other events.

There can be one or more `Behaviour` classes per skill. The developer must create a subclass from the abstract class `Behaviour` to create a new `Behaviour`.

A behaviour can be registered in two ways:

- By declaring it in the skill configuration file `skill.yaml` (see [below](#skill-config))
- In any part of the code of the skill, by enqueuing new `Behaviour` instances in the queue `context.new_behaviours`.


* `act(self)`: is how the framework calls the `Behaviour` code.

The framework supports different types of behaviours:
- `OneShotBehaviour`: this behaviour is executed only once.
- `CyclicBehaviour`: this behaviour is executed many times, 
  as long as `done()` returns `True`.)
- `TickerBehaviour`: the `act()` method is called every `tick_interval`.
 E.g. if the `TickerBehaviour` subclass is instantiated
 
There is another category of behaviours, called `CompositeBehaviour`. 
- `SequenceBehaviour`: a sequence of `Behaviour` classes, executed 
  one after the other.
- `FSMBehaviour`_`: a state machine of `State` behaviours. 
    A state is in charge of scheduling the next state.


If your behaviour fits one of the above, we suggest subclassing your
behaviour class with that behaviour class. Otherwise, you
can always subclass the general-purpose `Behaviour` class.

!!
Follows an example of a custom behaviour:

```python

from aea.skills.base import Behaviour

class HelloWorldBehaviour(OneShotBehaviour):
        
    def setup(self):
        """This method is called once, when the behaviour gets loaded."""

    def act(self): 
        """This methods is called in every iteration of the agent main loop."""
        print("Hello, World!")

    def teardown(self): 
        """This method is called once, when the behaviour is teared down."""
    

```

If we want to register this behaviour dynamically, in any part of the skill code
(i.e. wherever the skill context is available), we can write:

```python
self.context.new_behaviours.put(HelloWorldBehaviour())
```

Or, equivalently:
```python
def hello():
    print("Hello, World!")

self.context.new_behaviours.put(OneShotBehaviour(act=hello))
```

The callable passed to the `act` parameter is equivalent to the implementation
of the `act` method described above. 

The framework is then in charge of registering the behaviour and scheduling it 
for execution.

### `tasks.py`

Conceptually, a `Task` is where the developer codes any internal tasks the AEA requires.

There can be one or more `Task` classes per skill. The developer subclasses abstract class `Task` to create a new `Task`.

* `execute(self)`: is how the framework calls a `Task`. 

The `Task` class implements the [functor pattern](https://en.wikipedia.org/wiki/Function_object).
An instance of the `Task` class can be invoked as if it 
were an ordinary function. Once completed, it will store the
result in the property `result`. Raises error if the task has not been executed yet,
or an error occurred during computation.

We suggest using the `task_manager`, accessible through the skill context,
to manage long-running tasks. The task manager uses `multiprocessing` to 
schedule tasks, so be aware that the changes on the task object will 
not be updated.

Here's an example:

In `tasks.py`:
```python

from aea.skills.tasks import Task


def nth_prime_number(n: int) -> int:
    """A naive algorithm to find the n_th prime number."""
    primes = [2]
    num = 3
    while len(primes) < n:
        for p in primes:
            if num % p == 0:
                break
        else:
            primes.append(num)
        num += 2
    return primes[-1]


class LongTask(Task):

    def setup(self):
        """Set the task up before execution."""
        pass

    def execute(self, n: int):
        return nth_prime_number(n)

    def teardown(self):
        """Clean the task up after execution."""
        pass


```

In `behaviours.py`:
```python

from aea.skills.behaviours import TickerBehaviour
from packages.my_author_name.skills.my_skill.tasks import LongTask


class MyBehaviour(TickerBehaviour):

    def setup(self):
        my_task = LongTask()
        task_id = self.context.task_manager.enqueue_task(my_task, args=(10000, ))
        self.async_result = self.context.task_manager.get_task_result(task_id)  # type: multiprocessing.pool.AsyncResult

    def act(self):
        if self.async_result.ready() is False:
            print("The task is not finished yet.")
        else:
            completed_task = self.async_result.get()  # type: LongTask
            print("The result is:", completed_task.result)
            # Stop the skill
            self.context.is_active = False

    def teardown(self):
        pass


```

### Models

The developer might want to add other classes on the context level which are shared equally across the `Handler`, `Behaviour` and `Task` classes. To this end, the developer can subclass an abstract `Model`. These models are made available on the context level upon initialization of the AEA.

Say, the developer has a class called `SomeModel`
``` python
class SomeModel(Model):
    ...
```

Then, an instance of this class is available on the context level like so:
``` python
some_model = self.context.some_model
``` 

### Skill config

Each skill has a `skill.yaml` configuration file which lists all `Behaviour`, `Handler`, and `Task` objects pertaining to the skill.

It also details the protocol types used in the skill and points to shared modules, i.e. modules of type `Model`, which allow custom classes within the skill to be accessible in the skill context.

``` yaml
name: echo
authors: fetchai
version: 0.1.0
license: Apache-2.0
behaviours:
  echo:
    class_name: EchoBehaviour
    args:
      tick_interval: 1.0
handlers:
  echo:
    class_name: EchoHandler
    args:
      foo: bar
models: {}
dependencies: {}
protocols: ["fetchai/default:0.1.0"]
```


## Error skill

All top level AEA `skills` directories receive a default `error` skill that contains error handling code for a number of scenarios:

* Received envelopes with unsupported protocols 
* Received envelopes with unsupported skills (i.e. protocols for which no handler is registered)
* Envelopes with decoding errors
* Invalid messages with respect to the registered protocol

The error skill relies on the `default` protocol which provides error codes for the above.


<br />
