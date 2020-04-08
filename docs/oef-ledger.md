
The Open Economic Framework and the Ledgers allow AEAs to create value through their interaction with other AEAs. The following diagram illustrates the relation of AEAs to the OEF and Ledgers.

<center>![The AEA, OEF, and Ledger systems](assets/oef-ledger.png)</center>

## Open Economic Framework (OEF)

The 'Open Economic Framework' (OEF) consists of protocols, languages and market mechanisms agents use to search and find each other, communicate with as well as trade with each other.

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>The OEF is under development. Expect frequent changes. What follows is a description of the current implementation.</p>
</div>

At present, the OEF services are fulfilled by an `OEF search and communication node`. This node consists of two parts. A `search node` part enables agents to register their services and search and discover other agents' services. A `communication node` part enables agents to communicate with each other.

For two agents to be able to find each other, at least one must register as a service and the other must query the `OEF search node` for this service. For an example of such an interaction see <a href="../skill-guide" target="_blank">this guide</a>.

Agents can receive messages from other agents if they are both connected to the same `OEF communication node`.

Currently, you need to run your own `OEF search and communication node` for local development and testing. To start an `OEF search and communication node` follow the <a href="../quickstart/#preliminaries">Preliminaries</a> sections from the AEA quick start. Then run:

``` bash
python scripts/oef/launch.py -c ./scripts/oef/launch_config.json
```

When it is live you will see the sentence 'A thing of beauty is a joy forever...'.

To view the `OEF search and communication node` logs for debugging, navigate to `data/oef-logs`.

To connect to an `OEF search and communication node` an AEA uses the `OEFConnection` connection package (`fetchai/oef:0.2.0`).

<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>In the current implementation agents act as clients to the `OEF search and communication node`. We are working on a fully decentralized peer-to-peer implementation which will remove the need for a central entity.</p>
</div>


## Ledgers

Ledgers enable the AEAs to complete a transaction, which can involve the transfer of funds to each other or the execution of smart contracts.

Whilst a ledger can, in principle, also be used to store structured data - for instance, training data in a machine learning model - in most use cases the resulting costs and privacy implications do not make this a relevant use of the ledger. Instead, usually only references to the structured data - often in the form of hashes - are stored on the ledger and the actual data is stored off-chain.
