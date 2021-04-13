
The Open Economic Framework (OEF) and Decentralized Ledger Technologies (DLTs) allow AEAs to create value through their interaction with other AEAs. The following diagram illustrates the relation of AEAs to the OEF and DLTs.

<img src="../assets/oef-ledger.jpg" alt="The AEA, OEF, and Ledger systems" class="center">

## Open Economic Framework (OEF)

The _Open Economic Framework_ (OEF) consists of protocols, languages and market mechanisms agents use to search and find each other, communicate with as well as trade with each other. As such the OEF defines the decentralised virtual environment that supplies and supports APIs for autonomous third-party software agents, also known as Autonomous Economic Agents (AEAs).

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>The OEF is under development. Expect frequent changes. What follows is a description of the current implementation.</p>
</div>

At present, the OEF's capabilities are fulfilled by three components:

- a permissionless, public peer to peer (agent to agent) communication network, called the <a href="../acn">Agent Communication Network</a>;
- a set of <a href="../interaction-protocol">agent interaction protocols</a>; and
- a centralized <a href="../simple-oef">search and discovery system</a>.

The latter will be decentralized over time.

### Agent Communication Network (ACN)

ACN is a <a href="../acn">peer-to-peer communication network for agents</a>. It allows AEAs to send and receive envelopes between each other.

The implementation builds on the open-source <a href="https://libp2p.io/" target="_blank">libp2p</a> library. A distributed hash table is used by all participating peers to maintain a mapping between agents' cryptographic addresses and their network addresses.

Agents can receive messages from other agents if they are both connected to the ACN (see <a href="../p2p-connection">here</a> for an example).

### Search and Discovery

A <a href="../simple-oef">simple OEF (sOEF) node</a> allows agents to discover each other. In particular, agents can register themselves and the services they offer, and can search for agents who offer specific services. 

For two agents to be able to find each other, at least one must register itself on the sOEF and the other must query the sOEF node for it. Detailed documentation is provided <a href="../simple-oef">here</a>.

## Ledgers

Ledgers enable AEAs to store transactions, for example involving the transfer of funds to each other, or the execution of smart contracts. They optionally ensure the truth and integrity of agent to agent interactions.

Whilst a ledger can, in principle, be used to store structured data (for instance, training data in a machine learning model) in most use cases the resulting costs and privacy implications do not make this an efficient use of the ledger. Instead, usually only references to structured data - often in the form of hashes - are stored on a ledger, and the actual data is stored off-chain.

The Python implementation of the AEA Framework currently integrates with three ledgers:

- <a href="https://docs.fetch.ai/ledger/" target="_blank">Fetch.ai ledger</a>
- <a href="https://ethereum.org/en/developers/learning-tools/" target="_blank">Ethereum ledger</a>
- <a href="https://v1.cosmos.network/sdk" target="_blank">Cosmos ledger</a>

However, the framework makes it straightforward for any developer to add support for other ledgers.

### AEAs as second layer technology

The following presentation discusses how AEAs can be seen as second layer technology to ledgers.

<iframe width="560" height="315" src="https://www.youtube.com/embed/gvzYX7CYk-A" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
