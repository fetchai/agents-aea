This document describes some of the limitations of `v1` of the AEA framework and tradeoffs made in its design.

### Rejected ideas:

#### Handlers implemented as behaviours:

Handlers can be considered a special cases of a "behaviour that listens for specific events to happen".

One could implement `Handler` classes in terms of `Behaviours`, after having implemented the feature that behaviours can be activated after an event happens (e.g. receiving a message of a certain protocol).

This was rejected in favour of a clear separation of concerns, and to avoid purely reactive (handlers) and proactive (behaviours) components to be conflated into one concept. The proposal would also add complexity to behaviour development.


#### Multiple versions of the same package

The framework does not allow for the usage of multiple versions of the same package in a given project.

Although one could re-engineer the project to allow for this, it does introduce significant additional complexities. Furthermore, Python modules are by design only allowed to exist as one version in a given process. Hence, it seems sensible to maintain this approach in the AEA.


### Potential extensions, considered yet not decided:


#### Alternative skill design

For very simple skills, the splitting of skills into `Behaviour`, `Handler`, `Model` and `Task` classes can add unnecessary complexity to the framework and a counter-intuitive responsibility split. The splitting also implies the framework needs to introduce the `SkillContext` object to allow for access to data across the skill. Furthermore, the framework requires implementing all functionality in `SkillComponent` classes `Handler`, `Behaviour` or `Model`. This approach is consistent and transparent, however it creates a lot of boiler plate code for simple skills.

Hence, for some use cases it would be useful to have a single `Skill` class with abstract methods `setup`, `act`, `handle` and `teardown`. Then the developer can decide how to split up their code.

```
class SkillTemplate(SimpleSkill):

    protocol_ids: Optional[List[PublicId]] = None

    def setup():
        # setup skill

    def handle(message: Message):
        # handle messages

    def act():
        for b in behaviours:
            b.act()
    
    def teardown():
        # teardown skill
```

Alternatively, we could use decorators to let a developer define whether a function is part of a handler or behaviour. That way, a single file with a number of functions could implement a skill. (Behind the scenes this would utilise a number of virtual `Behaviour` and `Handler` classes provided by the framework).

The downside of this approach is that it does not advocate for much modularity on the skill level. Part of the role of a framework is to propose a common way to do things. The above approach can cause for a larger degree of heterogeneity in the skill design which makes it harder for developers to understand each others' code.

The separation between all four base classes does exist both in convention *and* at the code level. Handlers deal with skill-external events (messages), behaviours deal with scheduled events (ticks), models represent data and tasks are used to manage long-running business logic.

By adopting strong convention around skill development we allow for the framework to take a more active role in providing guarantees. E.g. handlers' and behaviours' execution can be limited to avoid them being blocking, models can be persisted and recreated, tasks can be executed with different task backends. The opinionated approach is thought to allow for better scaling.


#### Further modularity for skill level code

Currently we have three levels of modularity:

- PyPI packages
- framework packages: protocols, contracts, connections and skills
- framework plugins: CLI, ledger

We could consider having a fourth level: common behaviours, handlers, models exposed as modules which can then speed up skill development.


#### "promise" pattern:

Given the asynchronous nature of the framework, it is often hard to implement reactions to specific messages, without making a "fat" handler. Take the example of a handler for a certain type of message `A` for a certain protocol `p`. The handler for protocol `p` would look something like this:
```
class PHandler:
...
def handle(msg):
    if message type is A:
        self._handle_a(msg)
```

However, it could be helpful to overwrite this handler reaction with another callback (e.g. consider <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise" target="_blank">this in context</a>):
```
# callable that handles the reply
def my_callback(msg):
    # handle reply

self.context.outbox.put_message(message, handler_func=my_callback, failure_func=...)
```

This feature would introduce additional complexity for the framework to correctly wire up the callbacks and messages with the dialogues.


#### CLI using standard lib

Removing the click dependency from the CLI would further reduce the dependencies in the AEA framework which is overall desirable.


#### Meta data vs configurations

The current approach uses `yaml` files to specify both meta data and component configuration. It would be desirable to introduce the following separation:

- package metadata
- package default developer configuration
- package default user configuration

A user can only configure a subset of the configuration. The developer should be able to define these constraints for the user. Similarly, a developer cannot modify all fields in a package, some of them are determined by the framework.


#### Configuring agent goal setup

By default, the agent's goals are implicitly defined by its skills and the configurations thereof. This is because the default decision maker signs every message and transaction presented to it.

It is already possible to design a custom decision maker. However, more work needs to be done to understand how to improve the usability and configuration of the decision maker. In this context different types of decision makers can be implemented for the developer/user.


#### Connection status monitoring

Currently, connections are responsible for managing their own status after they have been "connected" by the `Multiplexer`. Developers writing connections must take care to properly set its connection status at all times and manage any disconnection. It would potentially be desirable to offer different policies to deal with connection problems on the multiplexer level:

- disconnect one, keep others alive
- disconnect all
- try reconnect indefinitely


#### Agent snapshots on teardown or error

Currently, the developer must implement snapshots on the component level. It would be desirable if the framework offered more help to persist the agent state on teardown or error.


#### Dialogues management

The current implementation of Dialogues is verbose. Developers often need to subclass `Dialogues` and `Dialogue` classes. More effort can be made to simplify and streamline dialogues management.

#### Instantiate multiple instances of the same class of `SkillComponent`

Currently, configuration and metadata of a package are conflated making it not straightforward to run one package component with multiple sets of configuration. It could be desirable to configure an agent to run a given package with multiple different configurations.

This feature could be problematic with respect to component to component messaging which currently relies on component ids, which are bound to the package and not its instance.

#### Containerized Agents

Agent management, especially when many of them live on the same host, can be cumbersome. The framework should provide more utilities for these large-scale use cases. But a proper isolation of the agent environment is something that helps also simple use cases.

A new software architecture, somehow inspired to the Docker system. The CLI only involves the initialization of the building of the agent (think of it as the specification of the `Dockerfile`: the `Agentfile`), but the actual build and run are done by the AEA engine, a daemon process analogous of the Docker Engine, which exposes APIs for these operations.

Users and developers would potentially like to run many AEAs of different versions and with differences in the versions of their dependencies. It is not possible to import different versions of the same Python (PyPI) package in the same process in a clean way. However, in different processes this is trivial with virtual environments. It would be desirable to consider this in the context of a container solution for agents.

#### Dependency light version of the AEA framework

The `v1` of the Python AEA implementation makes every effort to minimise the amount of third-party dependencies. However, some dependencies remain to lower development time.

It would be desirable to further reduce the dependencies, and potentially have an implementation that only relies on the Python standard library.

This could be taken further, and a reduced spec version for <a href="https://micropython.org" target="_blank">micropython</a> could be designed.

#### Compiled AEA

Python is not a compiled language. However, various projects attempt this, e.g. <a href="https://nuitka.net/doc/user-manual.html" target="_blank">Nuitka</a> and it would be desirable to explore how useful and practical this would be in the context of AEA.

#### DID integration

It would be great to integrate <a href="https://www.w3.org/TR/did-core/" target="_blank">DID</a> in the framework design, specifically identification of packages (most urgently protocols). Other projects and standards worth reviewing in the context (in particular with respect to identity):

- <a href="https://docs.ethhub.io/built-on-ethereum/identity/ERC725/" target="_blank">ERC 725: Ethereum Identity Standard</a> and <a href="https://erc725alliance.org" target="_blank">here</a>.
- <a href="https://github.com/ethereum/eips/issues/735" target="_blank">ERC 735: Claim Holder</a>

#### Optimise protocol schemas and messages

The focus of protocol development was on extensibility and compatibility, not on optimisation. For instance, the dialogue references use inefficient string representations.

#### Constraints on primitive types in protocols

The protocol generator currently does not support custom constraints. The framework could add support for custom constraints for the protocol generator and specification.

There are many types of constraints that could be supported in specification and generator. One could perhaps add support based on the popularity of specific constraints from users/developers.

Example constraints:

- strings following specific regular expression format (e.g. all lower case, any arbitrary regex format)
- max number of elements on lists/sets
- keys in one `dict` type be equal to keys in another `dict` type
- other logical constraints, e.g. as supported in ontological languages
- support for bounds (i.e. min, max) for numerical types (i.e. `int` and `float`) in protocol specification.

Example syntax:

- `pt:int[0, ]`
- `pt:float[1.0, 10.0]`
- `pt:int[-1000, 1000]`
- `pt:float[, 0]`

This would automatically enable support for signed/unsigned `int` and `float`. This syntax would allow for unbounded positive/negative/both, or arbitrary bounds to be placed on numerical types.

Currently, the developer has to specify a custom type to implement any constraints on primitive types.


#### Subprotocols & multi-party interactions

Protocols can be allowed to depend on each other. Similarly, protocols might have multiple parties.

Furthermore, a turn-taking function that specifies who's turn it is at any given point in the dialogue could be added.

Then the current `fipa` setup is a specific case of turn-taking where the turn shifts after a player sends a single move (unique-reply). But generally, it does not have to be like this. Players could be allowed to send multiple messages until the turn shifts, or until they send specific speech-acts (multiple-replies).


#### Timeouts in protocols

Protocols currently do not implement the concept of timeouts. We leave it to the skill developer to implement any time-specific protocol rules.


#### Framework internal messages

The activation/deactivation of skills and addition/removal of components is implemented in a "passive" way - the skill posts a request in its skill context queue (in the case of new behaviours), or it just sets a flag (in case of activation/deactivation of skills).

One could consider that a skill can send requests to the framework, via the internal protocol, to modify its resources or its status. The `DecisionMaker` or the `Filter` can be the components that take such actions.

This is a further small but meaningful step toward an actor-based model for agent internals.

#### Ledger transaction management

Currently, the framework does not manage any aspect of submitting multiple transactions to the ledgers. This responsibility is left to skills. Additionally, the ledger APIs/contract APIs take the ledger as a reference to determine the nonce for a transaction. If a new transaction is sent before a previous transaction has been processed then the nonce will not be incremented correctly for the second transaction. This can lead to submissions of multiple transactions with the same nonce, and therefore failure of subsequent transactions.

A naive approach would involve manually incrementing the nonce and then submitting transactions into the pool with the correct nonce for eventual inclusion. The problem with this approach is that any failure of a transaction will cause non of the subsequent transactions to be processed for some ledgers (https://ethereum.stackexchange.com/questions/2808/what-happens-when-a-transaction-nonce-is-too-high). To recover from a transaction failure not only the failed transaction would need to be handled, but potentially also all subsequent transactions. It is easy to see that logic required to recover from a transaction failure early in a sequence can be arbitrarily complex (involving potentially new negotiations between agents, new signatures having to be generated etc.).

A further problem with the naive approach is that it (imperfectly) replicates the ledger state (with respect to (subset of state of) a specific account).

A simple solution looks as follows: each time a transaction is constructed (requiring a new nonce) the transaction construction is queued until all previous transactions have been included in the ledger or failed. This way, at any one time the agent has only at most one transaction pending with the ledger. Benefits: simple to understand and maintain, transaction only enter the mempool when they are ready for inclusion which has privacy benefits over submitting a whole sequence of transaction at once. Downside: at most one transaction per block.

This approach is currently used and implemented across all the reference skills.

Related, the topic of latency in transactions. State channels provide a solution. E.g. <a href="https://github.com/perun-network/go-perun" target="_blank">Perun</a>. There could also be an interesting overlap with our protocols here.


#### Unsolved problems in `Multiplexer` - `AgentLoop` interplay

Problem 1: connection generates too many messages in a short amount of time, that are not consumed by the multiplexer
Solution: Can be solved by slowing down connections receive method called, controlled by the inbox messages amount
Side effects: Most of the connections should have an internal queue because there is no synchronization between internal logic and multiplexer connection `receive` calls.


Problem 2: the send method can take a long time (because send retries logic in connection)
Solution: Currently, we apply timeouts on send. Other solutions could be considered, like parallelisation.


Problem 3: too many messages are produced by a skill.
Solution: Raise an exception on outbox is full or slow down agent loop?


## ACN

### Agent mobility on ACN

If a peer-client or full client switches peer, then the DHT is not updated properly at the moment under certain conditions.

### Mailbox connection

The two available connections `p2p_libp2p` and `p2p_libp2p_client` imply that the agent is continuously connected and therefore must have uninterrupted network access and the resources to maintain a connection.

For more lightweight implementations, a mailbox connection is desirable, as outlined in the ACN documentation.


