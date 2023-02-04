# Agent Ecosystem

AEAs are situated within a larger ecosystem comprised of various other systems and technology layers.

<img src="../assets/oef-ledger.jpg" alt="The AEA, OEF, and Ledger systems" class="center">

## Agent Communication Network (ACN)

ACN is a <a href="../acn">peer-to-peer communication network</a> for agents. It allows AEAs to send and receive envelopes between each other.

The implementation builds on the open-source <a href="https://libp2p.io/" target="_blank">libp2p</a> library. A distributed hash table is used by all participating peers to maintain a mapping between agents' cryptographic addresses and their network addresses.

Agents can receive messages from other agents if they are both connected to the ACN (see <a href="../p2p-connection">here</a> for an example).

## Search and Discovery

An <a href="../simple-oef">sOEF node</a> allows agents to discover each other. In particular, agents can register themselves and the services they offer, and can search for agents who offer specific services.

For two agents to be able to find each other, at least one must register itself on the sOEF and the other must query the sOEF node for it. Detailed documentation is provided <a href="../simple-oef">here</a>.

## Ledgers

Ledgers enable AEAs to store transactions, for example involving the transfer of funds to each other, or the execution of smart contracts. They optionally ensure the truth and integrity of agent to agent interactions.

Although a ledger can, in principle, be used to store structured data (e.g. training data in a machine learning model), in most cases the resulting costs and privacy implications do not make this sustainable. Instead, usually only references to structured data - often in the form of hashes - are stored on a ledger, and the actual data is stored off-chain.

The Python implementation of the AEA Framework currently integrates with three ledgers:

- <a href="https://docs.fetch.ai/ledger_v2/" target="_blank">Fetch.ai ledger</a>
- <a href="https://ethereum.org/en/developers/learning-tools/" target="_blank">Ethereum ledger</a>
- <a href="https://v1.cosmos.network/sdk" target="_blank">Cosmos ledger</a>

Furthermore, the framework makes it straightforward for any developer to create a ledger plugin, adding support for another ledger.

### AEAs as Second Layer Technology

The following presentation discusses how AEAs can be seen as second layer technology to ledgers.

<iframe width="560" height="315" src="https://www.youtube.com/embed/gvzYX7CYk-A" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
