The AEA framework consists of several core elements, some which are required to run an AEA and others which are optional.

## The advanced elements AEAs use

In <a href="../core-components-1/">Core Components - Part 1</a> we discussed the elements each AEA uses. We will now look at some of the advanced elements each AEA uses.

### Decision Maker

The `DecisionMaker` component manages global agent state updates proposed by the skills and processes the resulting ledger transactions.

It is responsible for the AEA's crypto-economic security and goal management, and it contains the preference and ownership representation of the AEA.

Skills communicate with the decision maker via `InternalMessages`. There exist two types of these: `TransactionMessage` and `StateUpdateMessage`.

The `StateUpdateMessage` is used to initialize the decision maker with preferences and ownership states. It can also be used to update the ownership states in the decision maker if the settlement of transaction takes place off chain.

The `TransactionMessage` is used by a skill to propose a transaction to the decision maker. The performative `TransactionMessage.Performative.PROPOSE_FOR_SETTLEMENT` is used by a skill to propose a transaction which the decision maker is supposed to settle on chain. The performative `TransactionMessage.Performative.PROPOSE_FOR_SIGNING` is used by the skill to propose a transaction which the decision maker is supposed to sign and which will be settled later.

The decision maker processes messages and can accept or reject them.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For examples how to use these concepts have a look at the `tac_` skills. These functionalities are experimental and subject to change.
</p>
</div>

### Wallet

The wallet contains the private-public key pairs used by the AEA.

### Identity

The identity contains the AEAs addresses as well as its name.


## Optional elements AEAs use

### Ledger APIs

Ledger APIs are special types of connections.
<!--  #In particular, they must implement a protocol compatible 
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

