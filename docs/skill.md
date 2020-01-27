An AEA developer writes skills that the framework can call.

When you add a skill with the CLI, a directory is created which includes modules for the `Behaviour,` `Task`, and `Handler` classes as well as a configuration file `skill.yaml`.


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

* `act(self)`: is how the framework calls the `Behaviour` code.

!!!	Todo
	For example.


### `tasks.py`

Conceptually, a `Task` is where the developer codes any internal tasks the AEA requires.

There can be one or more `Task` classes per skill. The developer subclasses abstract class `Task` to create a new `Task`.

* `execute(self)`: is how the framework calls a `Task`. 

!!!	Todo
	For example.

### Shared classes

The developer might want to add other classes on the context level which are shared equally across the `Handler`, `Behaviour` and `Task` classes. To this end the developer can subclass an abstract `SharedClass`. These shared classes are made available on the context level upon initialization of the AEA.

Say, the developer has a class called `SomeClass`
``` python
class SomeClass(SharedClass):
    ...
```

Then, an instance of this class is available on the context level like so:
``` python
some_class = self.context.some_class
``` 

### Skill config

Each skill has a `skill.yaml` configuration file which lists all `Behaviour`, `Handler`, and `Task` objects pertaining to the skill.

It also details the protocol types used in the skill and points to shared modules, i.e. modules of type `SharedClass`, which allow custom classes within the skill to be accessible in the skill context.

``` yaml
name: echo
authors: fetchai
version: 0.1.0
license: Apache 2.0
behaviours:
  echo:
    class_name: EchoBehaviour
    args:
      foo: bar
handlers:
  echo:
    class_name: EchoHandler
    args:
      foo: bar
      bar: foo
tasks:
  echo:
    class_name: EchoTask
    args:
      foo: bar
      bar: foo
shared_classes: {}
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