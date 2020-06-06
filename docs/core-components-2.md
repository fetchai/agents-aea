The AEA framework consists of several core elements, some which are required to run an AEA and others which are optional.

## The advanced elements AEAs use

In <a href="../core-components-1/">Core Components - Part 1</a> we discussed the elements each AEA uses. We will now look at some of the advanced elements each AEA uses.

### Decision Maker

The `DecisionMaker` can be thought off like a wallet manager plus "economic brain" of the AEA. It is responsible for the AEA's crypto-economic security and goal management, and it contains the preference and ownership representation of the AEA.


Skills communicate with the decision maker via `InternalMessages`. There exist two types of these: `TransactionMessage` and `StateUpdateMessage`.

The `StateUpdateMessage` is used to initialize the decision maker with preferences and ownership states. It can also be used to update the ownership states in the decision maker if the settlement of transaction takes place off chain.

The `TransactionMessage` is used by skills to propose a transaction to the decision-maker. It can be used either for settling the transaction on-chain or to sign a transaction to be used within a negotiation.

An `InternalMessage`, say `tx_msg` is sent to the decision maker like so from any skill:
```
self.context.decision_maker_message_queue.put_nowait(tx_msg)
```

The decision maker processes messages and can accept or reject them.

To process `InternalMessages` from the decision maker in a given skill you need to create a `TransactionHandler` like so:

``` python
class TransactionHandler(Handler):

	protocol_id = InternalMessage.protocol_id

	def handle(self, message: Message):
		"""
		Handle an internal message.

		:param message: the internal message from the decision maker.
		"""
		# code to handle the message
```

The framework implements a default `DecisionMaker`. You can implement your own and mount it. To do so, define a single python file in core of the project and point to it in the agent configuration file. The below implements a very basic decision maker:

``` python
```

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For examples how to use these concepts have a look at the `tac_` skills. These functionalities are experimental and subject to change.
</p>
</div>

### Wallet

The wallet contains the private-public key pairs used by the AEA.

### Identity

The identity is an abstraction that represents the identity of an AEA in the Open Economic Framework, backed by public-key cryptography. It contains the AEA's addresses as well as its name.

The identity can be accessed in a skill via the <a href="../api/context/base/">agent context</a>.

## Optional elements AEAs use

### Ledger APIs

<!-- 
Ledger APIs are special types of connections. In particular, they must implement a protocol compatible 
 -->

AEAs use Ledger APIs to communicate with public ledgers.

### Contracts

Contracts wrap smart contracts for third-party decentralized ledgers. In particular, they provide wrappers around the API or ABI of a smart contract.

Contracts can be added as packages.

<!-- ## Filter

`Filter` routes messages to the correct `Handler` via `Resource`. It also holds a reference to the currently active `Behaviour` and `Task` instances.

By default for every skill, each `Handler`, `Behaviour` and `Task` is registered in the `Filter`. However, note that skills can de-active and re-activate themselves.

The `Filter` also routes internal messages from the `DecisionMaker` to the respective `Handler` in the skills.

## Resource 

The `Resource` component is made up of `Registries` for each type of resource (e.g. `Protocol`, `Handler`, `Behaviour`, `Task`). 

Message Envelopes travel through the `Filter` which in turn fetches the correct `Handler` from the `Registry`.

Specific `Registry` classes are in the `registries/base.py` module.

* `ProtocolRegistry`.
* `HandlerRegistry`. 
* `BehaviourRegistry`.
* `TaskRegistry`.
 -->

## Next steps

### Recommended

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../thermometer-skills-step-by-step/">Trade between two AEAs</a>

<br />

