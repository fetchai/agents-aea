An agent developer writes skill code that the framework can call.

When you add a skill with the cli, a directory is created which includes modules for the `Behaviour,` `Task`, and `Handler` classes.




## Context

The skill has a `context` object which is shared by all `Handler`, `Behaviour`, and `Task` objects. The skill context has a link to the agent context also.

This means it is possible to, at any point, grab the `context` and have access to the code in other parts of the skill.

For example, in the `ErrorHandler(Handler)` class, the code often grabs a reference to its context and by doing so can access initialised and running framework objects such as a `MailBox` for putting messages into.

``` python
self.context.outbox.put_message(to=envelope.sender, sender=self.context.agent_public_key,protocol_id=DefaultMessage.protocol_id, message=DefaultSerializer().encode(reply))
``` 

## What to code

Each of the skill classes has two methods that must be implemented. All of them include a `teardown()` method which the developer must implement. Then there is a specific method for each class that the framework requires.

### `handler.py`

At the current time, each skill has exactly one `Handler` class.

* `handle_envelope(self, Envelope)`: is where the skill receives a message contained within an `Envelope` and decides what to do with it.

!!!	Todo
	For example.

!!!	Note
	Handlers only deal with incoming messages. Outbound messages do not need handling.


### `behaviours.py`

Conceptually, a `Behaviour`  class is where the developer codes the business logic that interacts with other agents in the framework.

There can be one or more `Behaviour` classes per skill. The developer subclasses abstract class `Behaviour` to create a new `Behaviour`.

* `act(self)`: is how the framework calls the `Behaviour` code. 

!!!	Todo
	For example.


### `tasks.py`

Conceptually, a `Task` is where the developer codes any internal tasks the agent requires.

There can be one or more `Task` classes per skill. The developer subclasses abstract class `Task` to create a new `Task`.

* `execute(self)`: is how the framework calls a `Task`. 

!!!	Todo
	For example.


### `shared.py`

This class will allow communication with new custom classes. 

!!!	Note
	Coming soon.


## Error skill

All top level AEA `skills` directories receive a default `error` skill that contains error handling code for a number of scenarios.

* Received envelopes with unsupported protocols 
* Received envelopes with unsupported skills.
* Envelopes with decoding errors.
* Invalid messages with respect to the registered protocol.

The error skill relies on the `default` protocol which provides error codes for the above.


<br />