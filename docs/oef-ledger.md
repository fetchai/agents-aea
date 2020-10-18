
The Open Economic Framework (OEF) and Decentralized Ledger Technologies (DLTs) allow AEAs to create value through their interaction with other AEAs. The following diagram illustrates the relation of AEAs to the OEF and DLTs.

<img src="../assets/oef-ledger.png" alt="The AEA, OEF, and Ledger systems" class="center">

## Open Economic Framework (OEF)

The 'Open Economic Framework' (OEF) consists of protocols, languages and market mechanisms agents use to search and find each other, communicate with as well as trade with each other. As such the OEF defines the decentralised virtual environment that supplies and supports APIs for autonomous third-party software agents, also known as Autonomous Economic Agents (AEAs).

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>The OEF is under development. Expect frequent changes. What follows is a description of the current implementation.</p>
</div>

At present, the OEF's capabilities are fulfilled by two components:

- a permissionless, public peer to peer (agent to agent) communication network, called the Agent Communication Network;
- a set of <a href="../protocol">agent interaction protocols</a>; and
- a centralized search and discovery system.

The latter will be decentralized over time.

### Agent Communication Network (ACN)

The agent communication network is a <a href="../acn">peer-to-peer communication network for agents</a>. It allows agents, in particular AEAs, to send and receive envelopes between each other.

The implementation builds on the open-source <a href="https://libp2p.io/" target="_blank">libp2p</a> library. A distributed hash table is used by all participating peers to maintain a mapping between agents' cryptographic addresses and their network addresses.

Agents can receive messages from other agents if they are both connected to the ACN (see <a href="../p2p-connection">here</a> for an example).

### Centralized search and discovery

A <a href="../simple-oef">simple OEF (SOEF) search node</a> allows agents to search and discover each other. In particular, agents can register themselves and their services as well as send search requests.

For two agents to be able to find each other, at least one must register themselves and the other must query the SOEF search node for it. Detailed documentation is provided <a href="../simple-oef">here</a>.

<!-- <details><summary>Click here for a local development alternative (deprecated).</summary>
<p>

For local development, you can use an `OEF search and communication node`. This node consists of two parts. A `search node` part enables agents to register their services and search and discover other agents' services. A `communication node` part enables agents to communicate with each other.

For two agents to be able to find each other, at least one must register as a service and the other must query the `OEF search node` for this service. For an example of such an interaction see <a href="../skill-guide" target="_blank">this guide</a>.

Agents can receive messages from other agents if they are both connected to the same `OEF communication node`.

Currently, you need to run your own `OEF search and communication node` for local development and testing. To start an `OEF search and communication node` follow the <a href="../quickstart/#preliminaries">Preliminaries</a> sections from the AEA quick start. Then run:

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

When it is live you will see the sentence 'A thing of beauty is a joy forever...'.

To view the `OEF search and communication node` logs for debugging, navigate to `data/oef-logs`.

To connect to an `OEF search and communication node` an AEA uses the `OEFConnection` connection package (`fetchai/oef:0.11.0`).

If you experience any problems launching the `OEF search and communication node` then consult <a href="https://docs.google.com/document/d/1x_hFwEIXHlr_JCkuIv-izxSz0tN-7kSmSc-g32ImL1U/edit?usp=sharing" target="_blank">this</a> guide.

### Installing docker

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For the purpose of the quickstart only, you can skip installation of docker.</p>
</div>

At some point, you will need <a href="https://www.docker.com/" target="_blank">Docker</a> installed on your machine
(e.g. to run an <a href="../oef-ledger">OEF search and communication node</a>.

### Download the scripts and examples directories

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>For the purpose of the quickstart only, you can skip downloading the scripts and examples directories.</p>
</div>

Download folders containing examples and scripts:
``` bash
svn export https://github.com/fetchai/agents-aea.git/trunk/examples
svn export https://github.com/fetchai/agents-aea.git/trunk/scripts
```
You can install the `svn` command with (`brew install subversion` or `sudo apt-get install subversion`).

</p>
</details> -->

## Ledgers

Ledgers enable the AEAs to complete a transaction, which can involve the transfer of funds to each other or the execution of smart contracts. They optionally ensure the truth and integrity of agent to agent interactions.

Whilst a ledger can, in principle, also be used to store structured data - for instance, training data in a machine learning model - in most use cases the resulting costs and privacy implications do not make this a relevant use of the ledger. Instead, usually only references to the structured data - often in the form of hashes - are stored on the ledger and the actual data is stored off-chain.

The Python version of the AEA Framework currently integrates with three ledgers:

- <a href="https://docs.fetch.ai/ledger/" target="_blank">Fetch.ai ledger</a>
- <a href="https://ethereum.org/en/developers/learning-tools/" target="_blank">Ethereum ledger</a>
- <a href="https://cosmos.network/sdk" target="_blank">Cosmos ledger</a>

However, the framework makes it straightforward for further ledgers to be added by any developer.

### AEAs as second layer technology

The following presentation discusses how AEAs can be seen as second layer technology to ledgers.

<iframe width="560" height="315" src="https://www.youtube.com/embed/gvzYX7CYk-A" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
