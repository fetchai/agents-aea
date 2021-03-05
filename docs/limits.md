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

This feature would introduce additional complexity for the framework to correctly wire up the callbacks and messages with the dialogues. Consider [this in context](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)


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

Currently, configuration and metadata of a package are conflated macking it not straightforward to run one package component with multiple sets of configuration. It could be desirable to configure an agent to run a given package with multiple different configurations. This can also be problemativ with respect to component to component messaging which currently relies on component ids, which are bound to the package and not its instance.

#### Containerized Agents

Agent management, especially when many of them live on the same host, can be cumbersome. The framework should provide more utilities for these large-scale use cases. But a proper isolation of the agent environment is something that helps also simple use cases.


A new software architecture, somehow inspired to the Docker system. The CLI only involves the initialization of the building of the agent (think of it as the specification of the Dockerfile: the Agentfile), but the actual build and run are done by the AEA engine, a daemon process analogous of the Docker Engine, which exposes APIs for these operations.


...virtual envs...divergent versions possible...

Users and developers would potentially like to run many AEAs of different versions and with differences in the versions of their dependencies. It is not possible to import different versions of the same Python (PyPI) package in the same process in a clean way. However, in different processes this is trivial with virtual environments. It would be desirable to consider this in the context of a container solution for agents.

#### Dependency light version of the AEA framework

The `v1` of the Python AEA implementation makes every effort to minimise the amount of third-party dependencies. However, some dependencies remain to lower development time.

It would be desirable to further reduce the dependencies, and potentially have an implementation that only relies on the Python standard library.

This could be taken further, and a reduced spec version for [micropython](https://micropython.org) could be designed.

#### Compiled AEA

Python is not a compiled language. However, various projects attempt this, e.g. [http://nuitka.net/doc/user-manual.html](http://nuitka.net/doc/user-manual.html) and it would be desirable to explore how useful this would be in the context of AEA.

#### DID integration

It would be great to integrate https://www.w3.org/TR/did-core/ in the framework design, specifically identification of packages (most urgently protocols). Other projects and standards worth reviewing in the context (also identity):

- [ERC 725: Ethereum Identity Standard](https://docs.ethhub.io/built-on-ethereum/identity/ERC725/) and [here](https://erc725alliance.org)
- [ERC 735: Claim Holder](ethereum/EIPs#735)

#### Optimise protocol schemas and messages

The focus of protocol development was on extensibility and compatibility, not on optimisation. For instance, the dialogue references use inefficient string representations.

#### Constraints on primitive types in protocols

The protocol generator currently does not support custom constraints. Add support for custom constraints for the protocol generator.

Support for custom constraints on types in protocol specification and generator could be added.

Example constraints:

- strings following specific regular expression format (e.g. all lower case, any arbitrary regex format)
- max number of elements on lists/sets
- keys in one dict type be equal to keys in another dict type
- other logical constraints, e.g. as supported in ontological languages

There are many types of constraints that could be supported in specification and generator. One could perhaps add support based on the popularity of specific constraints form users/developers.

Support for bounds (i.e. min, max) for numerical types (i.e. int and float) in protocol specification.

Example syntax:

pt:int[0, ]
pt:float[1.0, 10.0]
pt:int[-1000, 1000]
pt:float[, 0]
This would automatically enable support for signed/unsigned int and float.
This syntax would allow for unbounded positive/negative/both, or arbitrary bounds to be placed on numerical types.

Currently, the developer has to specify a custom type to implement any constraints on primitive types.

#### Framework internal messages

The activation/deactivation of skills and addition/removal of components is implemented in a "passive" way - the skill posts a request in its skill context queue (in the case of new behaviours), or it just sets a flag (in case of activation/deactivation of skills).

One could consider that a skill can send requests to the framework, via the internal protocol, to modify its resources or its status. The Decision Maker or the Filter can be the components that take such actions.

This is a further small but meaningful step toward an actor-based model for agent internals.

## ACN

### Agent mobility on ACN:

- If a peer-client or full client switches peer, then the DHT is not updated properly. Address!

### Mailbox connection

The two available connections `p2p_libp2p` and `p2p_libp2p_client` imply that the agent is continuously connected and therefore must have uninterupted network access and the resources to maintain a connection.

For more lightweight implementations, a mailbox connection is desirable, as outlined in the ACN documentation.


