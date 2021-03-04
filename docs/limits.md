This document describes some of the limitations of v1 of the AEA framework and tradeoffs made.

### Rejected ideas:

#### Handlers implemented as behaviours:

Handlers can we considered a special cases of a "behaviour that listens for specific events to happen".

One could implement `Handler` classes in terms of `Behaviours`, after having implemented the feature that behaviour can be activated after an event happens (e.g. receiving message of a certain protocol).

This was rejected as the current split seems more helpful in how the classes are used. ...


#### Multiple versions of the same package

The framework currently does not allow the usage of multiple versions of the same package in a given project.

Although one could reengineer the project to allow for this, it does introduce additional complexities. It also violates the idea of versioning itself. Python modules are also by design only allowed to exist as one version in a given process. Hence, it seems sensible to maintain this approach in the AEA.


### Potential extensions, considered yet not decided:

#### "promise" pattern:

- Given the asynchronous nature of the framework, it is often hard to implement reactions to specific messages, without making a "fat" handler.
- Say I have a handler for a certain type of message A for a certain protocol p. I'll likely have a handler for protocol p:
```
class PHandler:
...
def handle(msg):
    if message type is A:
        self._handle_a(msg)
```

However, I'd like to overwrite this handler reaction with another callback. I would be able to do the following:

```
# callable that handles the reply
def my_callback(msg):
    # handle reply

self.context.outbox.put_message(message, handler_func=my_callback, failure_func=...)
```

This feature would introduce additional complexity for the framework to correctly wire up the callbacks and messages with the dialogues.


#### CLI plugin mechanism

It would be useful to let the user to define custom commands for their AEA project, or make it available for anyone via a plug-in mechanism. We can draw inspiration from other Python frameworks.

#### CLI using standard lib

Removing the click dependency from the CLI would further reduce the dependencies in the AEA framework which is overall desirable. It comes at the overhead of implementing this.


#### Meta data vs configurations

The current approach uses `yaml` files to specify both meta data and configuration. It would be desirable to introduce the following separation:

- package metadata
- package default (developer) configuration
- package default (user) configuration

A user can only configure a subset of the configuration. The developer should be able to define these constraints for the user. Similarly, a developer cannot modify all fields in a package, some of them are determined by the framework.


#### Configuring agent goal setup

By default, the agent's goals are implicitly defined by its skills and configurations thereof. This is because the default decision maker signs every message and transaction presented to it.

It is already possible to design a custom decision maker. However, more work needs to be done to understand how to improve the usability and configuration of the decision maker.


#### Connection status monitoring

Currently, connections are responsible for managing their own status. Developers writing connections must take care to properly set its connection status at all times and manage any disconnection. It would potentially be desirable to offer different policies to deal with connection problems on the multiplexer level:

- disconnect one, keep others alive
- disconnect all
- try reconnect indefinitely


#### Agent snapshots on teardown or error

Currently, it is not possible to take full snapshots. It would be desirable to offer this possibility. It could be implemented by letting developers specify which dialogues and what additional data should be persisted on teardown or error.


#### Alternative ways to implement skills

The current skills package requires implementing all functionality in SkillComponent classes Handler, Behaviour or Model. This approach is consistent and transparent, however it creates a lot of boiler plate code for simple skills.

It would potentially be desirable to offer less verbose ways of defining skills.


#### Dialogues management

The current implementation of Dialogues is verbose. Developers often need to subclass `Dialogues` and `Dialogue` classes.

#### Instantiate multiple instances of the same class of SkillComponent

Currently, configuration and metadata of a package are conflated macking it not straightforward to run one package component with multiple sets of configuration.

#### Containerized Agents

...virtual envs...divergent versions possible...

## ACN

### Agent mobility on ACN:

- If a peer-client or full client switches peer, then the DHT is not updated properly. Address!



