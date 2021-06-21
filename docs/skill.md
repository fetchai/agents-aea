<a href="../api/skills/base#skill-objects">`Skills`</a> are the core focus of the framework's extensibility as they implement business logic to deliver economic value for the AEA. They are self-contained capabilities that AEAs can dynamically take on board, in order to expand their effectiveness in different situations.

<img src="../assets/skill-components.jpg" alt="Skill components of an AEA" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

A skill encapsulates implementations of the three abstract base classes `Handler`, `Behaviour`, `Model`, and is closely related with the abstract base class `Task`:

* <a href="../api/skills/base#handler-objects">`Handler`</a>: each skill has zero, one or more `Handler` objects, each responsible for the registered messaging protocol. Handlers implement AEAs' **reactive** behaviour. If the AEA understands the protocol referenced in a received `Envelope`, the `Handler` reacts appropriately to the corresponding message. Each `Handler` is responsible for only one protocol. A `Handler` is also capable of dealing with internal messages (see next section).
* <a href="../api/skills/base#behaviour-objects">`Behaviour`</a>: zero, one or more `Behaviours` encapsulate actions which further the AEAs goal and are initiated by internals of the AEA, rather than external events. Behaviours implement AEAs' **pro-activeness**. The framework provides a number of <a href="../api/skills/behaviours">abstract base classes</a> implementing different types of behaviours (e.g. cyclic/one-shot/finite-state-machine/etc.).
* <a href="../api/skills/base#model-objects">`Model`</a>: zero, one or more `Models` that inherit from the `Model` class. `Models` encapsulate custom objects which are made accessible to any part of a skill via the `SkillContext`.
* <a href="../api/skills/tasks#task-objects">`Task`</a>: zero, one or more `Tasks` encapsulate background work internal to the AEA. `Task` differs from the other three in that it is not a part of skills, but `Task`s are declared in or from skills if a packaging approach for AEA creation is used.

A skill can read (parts of) the state of the the AEA (as summarised in the <a href="../api/context/base#agentcontext-objects">`AgentContext`</a>), and suggest actions to the AEA according to its specific logic. As such, more than one skill could exist per protocol, competing with each other in suggesting to the AEA the best course of actions to take. In technical terms this means skills are horizontally arranged.

For instance, an AEA who is trading goods, could subscribe to more than one skill, where each skill corresponds to a different trading strategy.  The skills could then read the preference and ownership state of the AEA, and independently suggest profitable transactions.

The framework places no limits on the complexity of skills. They can implement simple (e.g. `if-this-then-that`) or complex (e.g. a deep learning model or reinforcement learning agent).

The framework provides one default skill, called `error`. Additional skills can be added as packages.

## Independence of skills

Skills are `horizontally layered`, that is they run independently of each other. They also cannot access each other's state.

Two skills can communicate with each other in two ways. The skill context provides access via `self.context.shared_state` to a key-value store which allows skills to share state. A skill can also define as a callback another skill in <a href="../decision-maker-transaction">a message to the decision maker</a>.

## Context

The skill has a <a href="../api/skills/base#skillcontext-objects">`SkillContext`</a> object which is shared by all `Handler`, `Behaviour`, and `Model` objects. The skill context also has a link to the `AgentContext`. The `AgentContext` provides read access to AEA specific information like the public key and address of the AEA, its preferences and ownership state. It also provides access to the `OutBox`.

This means it is possible to, at any point, grab the `context` and have access to the code in other parts of the skill and the AEA.

For example, in the `ErrorHandler(Handler)` class, the code often grabs a reference to its context and by doing so can access initialised and running framework objects such as an `OutBox` for putting messages into.

``` python
self.context.outbox.put_message(message=reply)
``` 

Moreover, you can read/write to the _agent context namespace_ by accessing the attribute `SkillContext.namespace`.

Importantly, however, a skill does not have access to the context of another skill or protected AEA components like the `DecisionMaker`.

## What to code

Each of the skill classes has three methods that must be implemented. All of them include a `setup()` and `teardown()` method which the developer must implement. 

Then there is a specific method that the framework requires for each class.

### `handlers.py`

There can be none, one or more `Handler` class per skill.

`Handler` classes can receive `Message` objects of one protocol type only. However, `Handler` classes can send `Envelope` objects of any type of protocol they require.

* `handle(self, message: Message)`: is where the skill receives a `Message` of the specified protocol and decides what to do with it.

A handler can be registered in one way:

- By declaring it in the skill configuration file `skill.yaml` (see <a href="../skill/#skill-config">below</a>).

It is possible to register new handlers dynamically by enqueuing new
`Handler` instances in the queue `context.new_handlers`, e.g. in a skill
component we can write:

``` python
self.context.new_handlers.put(MyHandler(name="my_handler", skill_context=self.context))
```

### `behaviours.py`

Conceptually, a `Behaviour`  class contains the business logic specific to initial actions initiated by the AEA rather than reactions to other events.

There can be one or more `Behaviour` classes per skill. The developer must create a subclass from the abstract class `Behaviour` to create a new `Behaviour`.

* `act(self)`: is how the framework calls the `Behaviour` code.

A behaviour can be registered in two ways:

- By declaring it in the skill configuration file `skill.yaml` (see <a href="../skill/#skill-config">below</a>)
- In any part of the code of the skill, by enqueuing new `Behaviour` instances in the queue `context.new_behaviours`. In that case, `setup`is not called by the framework, as the behaviour will be added after the AEA setup is complete.

The framework supports different types of behaviours:

- <a href="../api/skills/behaviours#oneshotbehaviour-objects">`OneShotBehaviour`</a>: this behaviour is executed only once.
- <a href="../api/skills/behaviours#tickerbehaviour-objects">`TickerBehaviour`</a>: the `act()` method is called every `tick_interval`. E.g. if the `TickerBehaviour` subclass is instantiated
 
There is another category of behaviours, called <a href="../api/skills/behaviours#compositebehaviour-objects">`CompositeBehaviour`</a>:

- <a href="../api/skills/behaviours#sequencebehaviour-objects">`SequenceBehaviour`</a>: a sequence of `Behaviour` classes, executed 
  one after the other.
- <a href="../api/skills/behaviours#fsmbehaviour-objects">`FSMBehaviour`</a>: a state machine of `State` behaviours. A state is in charge of scheduling the next state.


If your behaviour fits one of the above, we suggest subclassing your
behaviour class with that behaviour class. Otherwise, you
can always subclass the general-purpose `Behaviour` class.

Follows an example of a custom behaviour:

``` python

from aea.skills.behaviours import OneShotBehaviour

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

``` python
self.context.new_behaviours.put(HelloWorldBehaviour(name="hello_world", skill_context=self.context))
```

Or, equivalently to the previous two code blocks:
``` python
def hello():
    print("Hello, World!")

self.context.new_behaviours.put(OneShotBehaviour(act=hello, name="hello_world", skill_context=self.context))
```

The callable passed to the `act` parameter is equivalent to the implementation
of the `act` method described above. 

The framework is then in charge of registering the behaviour and scheduling it 
for execution.

### `tasks.py`

Conceptually, a `Task` is where the developer codes any internal tasks the AEA requires.

There can be one or more `Task` classes per skill. The developer subclasses abstract class `Task` to create a new `Task`.

* `execute(self)`: is how the framework calls a `Task`. 

The `Task` class implements the <a href="https://en.wikipedia.org/wiki/Function_object" target="_blank">functor pattern</a>.
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
``` python

from aea.skills.tasks import Task


def nth_prime_number(n: int) -> int:
    """A naive algorithm to find the n_th prime number."""
    assert n > 0
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

    def execute(self, n: int):
        return nth_prime_number(n)

    def teardown(self):
        """Clean the task up after execution."""


```

In `behaviours.py`:
``` python

from aea.skills.behaviours import TickerBehaviour
from packages.my_author_name.skills.my_skill.tasks import LongTask


class MyBehaviour(TickerBehaviour):

    def setup(self):
        """Setup behaviour."""
        my_task = LongTask()
        task_id = self.context.task_manager.enqueue_task(my_task, args=(10000, ))
        self.async_result = self.context.task_manager.get_task_result(task_id)  # type: multiprocessing.pool.AsyncResult

    def act(self):
        """Act implementation."""
        if self.async_result.ready() is False:
            print("The task is not finished yet.")
        else:
            completed_task = self.async_result.get()  # type: LongTask
            print("The result is:", completed_task.result)
            # Stop the skill
            self.context.is_active = False

    def teardown(self):
        """Teardown behaviour."""


```

### Models

The developer might want to add other classes on the context level which are shared equally across the `Handler`, `Behaviour` and `Task` classes. To this end, the developer can subclass an abstract <a href="../api/skills/base#model-objects">`Model`</a>. These models are made available on the context level upon initialization of the AEA.

Say, the developer has a class called `SomeModel`
``` python
class SomeModel(Model):
    ...
```

Then, an instance of this class is available on the context level like so:
``` python
some_model = self.context.some_model
``` 

### Skill configuration

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
protocols:
- fetchai/default:1.0.0
```


## Error skill

All AEAs have a default `error` skill that contains error handling code for a number of scenarios:

* Received envelopes with unsupported protocols 
* Received envelopes with unsupported skills (i.e. protocols for which no handler is registered)
* Envelopes with decoding errors
* Invalid messages with respect to the registered protocol

The error skill relies on the `fetchai/default:1.0.0` protocol which provides error codes for the above.


## Custom Error handler

The framework implements a default <a href="../api/error_handler/default#errorhandler-objects">`ErrorHandler`</a>. 
You can implement your own and mount it. The easiest way to do this is to run the following command to scaffold a custom `ErrorHandler`:

``` bash
aea scaffold error-handler
```

Now you will see a file called `error_handler.py` in the AEA project root.
You can then implement your own custom logic to process messages. 


<br />
